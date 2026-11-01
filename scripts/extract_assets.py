#!/usr/bin/env python3
"""Extract candidate images, text and figures from a PDF/PPTX/image or plain text.

Never treats an embedded image as the complete scientific figure automatically.
"""
import argparse
import csv
import hashlib
import json
import mimetypes
import re
import shutil
import subprocess
from pathlib import Path


def name_safe(value):
    return re.sub(r"[^0-9A-Za-z._-]+", "_", value)[:120]


def put_binary(raw, ext, dest, seen):
    digest = hashlib.sha256(raw).hexdigest()
    if digest in seen:
        return seen[digest], digest, True
    ext = ext.lower().lstrip(".")
    if ext not in {"png", "jpg", "jpeg", "svg", "tiff", "tif", "webp", "bmp", "gif", "jp2", "jpx"}:
        ext = "bin"
    name = f"asset_{len(seen)+1:03d}_{digest[:9]}.{ext}"
    p = dest / name
    p.write_bytes(raw)
    seen[digest] = str(p)
    return str(p), digest, False


def handle_pdf(input_file, output, manifest, render_pages, dpi):
    from pypdf import PdfReader
    reader = PdfReader(str(input_file))
    for index, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ""
        text_path = output / "text" / f"page_{index:03d}.txt"
        text_path.write_text(text, encoding="utf-8")
        manifest["text"].append({"page": index, "path": str(text_path), "characters": len(text)})
        try:
            images = page.images
        except Exception as exc:
            manifest["warnings"].append(f"PDF page {index}: image enumeration: {exc}")
            continue
        for image_i, image in enumerate(images, 1):
            try:
                ext = (image.name or "image.png").rsplit(".", 1)[-1]
                path, digest, dup = put_binary(image.data, ext, output / "media", manifest["_seen"])
                manifest["assets"].append({"path": path, "kind": "embedded-image-candidate", "page": index,
                                           "name": image.name, "sha256": digest, "duplicate": dup,
                                           "notice": "May be one layer of a composite PDF figure; inspect full page and caption."})
            except Exception as exc:
                manifest["warnings"].append(f"PDF page {index}: image {image_i}: {exc}")
    if render_pages:
        if not shutil.which("pdftoppm"):
            manifest["warnings"].append("pdftoppm unavailable: PDF pages were not rendered")
        else:
            prefix = output / "pages" / "page"
            cmd = ["pdftoppm", "-png", "-r", str(dpi), str(input_file), str(prefix)]
            try:
                subprocess.run(cmd, timeout=150, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                for p in sorted((output / "pages").glob("*.png")):
                    manifest["page_renders"].append(str(p))
            except (subprocess.SubprocessError, OSError) as exc:
                manifest["warnings"].append(f"Page render failed: {exc}")


def handle_pptx(input_file, output, manifest):
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE_TYPE
    prs = Presentation(str(input_file))
    for i, slide in enumerate(prs.slides, 1):
        blocks = []
        for j, shape in enumerate(slide.shapes, 1):
            if shape.has_text_frame and shape.text:
                blocks.append(shape.text)
            if shape.has_table:
                table = shape.table
                csv_path = output / "tables" / f"slide_{i:03d}_table_{j:03d}.csv"
                with csv_path.open("w", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    for row in table.rows:
                        writer.writerow([cell.text for cell in row.cells])
                manifest["tables"].append({"slide": i, "path": str(csv_path), "shape": j})
            if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                ext = shape.image.ext
                path, digest, dup = put_binary(shape.image.blob, ext, output / "media", manifest["_seen"])
                manifest["assets"].append({"path": path, "kind": "ppt-picture-candidate", "slide": i,
                                            "shape": j, "left": shape.left, "top": shape.top,
                                            "width": shape.width, "height": shape.height,
                                            "sha256": digest, "duplicate": dup,
                                            "notice": "Determine whether photo, scientific figure, logo or decoration."})
        txt_path = output / "text" / f"slide_{i:03d}.txt"
        txt_path.write_text("\n".join(blocks), encoding="utf-8")
        manifest["text"].append({"slide": i, "path": str(txt_path)})
        try:
            notes = slide.notes_slide.notes_text_frame.text
            note_path = output / "notes" / f"slide_{i:03d}.txt"
            note_path.write_text(notes, encoding="utf-8")
            manifest["notes"].append({"slide": i, "path": str(note_path)})
        except Exception:
            pass


def handle_docx(input_file, output, manifest):
    try:
        from docx import Document
    except ImportError:
        manifest["warnings"].append("Install python-docx for DOCX reading")
        return
    document = Document(str(input_file))
    lines = [p.text for p in document.paragraphs]
    (output / "text" / "document.txt").write_text("\n".join(lines), encoding="utf-8")
    manifest["text"].append({"path": str(output / "text" / "document.txt")})
    for ti, table in enumerate(document.tables, 1):
        path = output / "tables" / f"table_{ti:03d}.csv"
        with path.open("w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows([[cell.text for cell in row.cells] for row in table.rows])
        manifest["tables"].append({"path": str(path), "table": ti})
    for i, rel in enumerate(document.part.rels.values(), 1):
        if "image" not in rel.reltype:
            continue
        part = rel.target_part
        ext = Path(part.partname).suffix or ".bin"
        path, digest, dup = put_binary(part.blob, ext, output / "media", manifest["_seen"])
        manifest["assets"].append({"path": path, "kind": "docx-image-candidate", "shape": i,
                                   "sha256": digest, "duplicate": dup})


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("file", help="Input PDF, PPTX, DOCX, image, MD or TXT")
    p.add_argument("--out", required=True, help="Output directory for candidate assets")
    p.add_argument("--render-pages", action="store_true", help="Render PDF pages (for composite/vector figures)")
    p.add_argument("--dpi", type=int, default=140)
    args = p.parse_args()
    src = Path(args.file).resolve()
    if not src.is_file():
        p.error(f"No such file: {src}")
    out = Path(args.out).resolve()
    for d in [out, out / "text", out / "media", out / "tables", out / "notes", out / "pages"]:
        d.mkdir(parents=True, exist_ok=True)
    manifest = {"input_file": str(src), "source_type": src.suffix.lower(), "assets": [],
                "text": [], "tables": [], "notes": [], "page_renders": [], "warnings": [], "_seen": {}}
    ext = src.suffix.lower()
    if ext == ".pdf":
        handle_pdf(src, out, manifest, args.render_pages, args.dpi)
    elif ext == ".pptx":
        handle_pptx(src, out, manifest)
    elif ext == ".docx":
        handle_docx(src, out, manifest)
    elif ext in {".png", ".jpg", ".jpeg", ".webp", ".svg"}:
        dest = out / "media" / src.name
        shutil.copyfile(src, dest)
        manifest["assets"].append({"path": str(dest), "kind": "user-image"})
    elif ext in {".txt", ".md", ".csv"}:
        dest = out / "text" / src.name
        shutil.copyfile(src, dest)
        manifest["text"].append({"path": str(dest)})
    else:
        p.error(f"Unsupported file type: {ext}")
    manifest.pop("_seen")
    mpath = out / "manifest.json"
    mpath.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"manifest": str(mpath), "assets": len(manifest["assets"]),
                      "text_entries": len(manifest["text"]), "warnings": len(manifest["warnings"])}, indent=2))


if __name__ == "__main__":
    main()
