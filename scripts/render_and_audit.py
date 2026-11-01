#!/usr/bin/env python3
"""Structural slide audit and optional LibreOffice / Poppler render for review."""
import argparse
import json
import os
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
from zipfile import ZipFile


def audit_pptx(pptx_file):
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE_TYPE
    prs = Presentation(str(pptx_file))
    out = {"slide_count": len(prs.slides), "slides": [], "warnings": [],
           "media_count": 0, "zip_integrity": None, "embedded_picture_count": 0,
           "fonts_declared": {}, "speaker_notes_count": 0}
    fonts = Counter()
    with ZipFile(pptx_file) as z:
        out["zip_integrity"] = z.testzip() is None
        out["media_count"] = len([n for n in z.namelist() if n.startswith("ppt/media/") and not n.endswith("/")])
    for i, slide in enumerate(prs.slides, 1):
        s = {"slide": i, "picture_shapes": 0, "text_shapes": 0, "out_of_bounds": [],
             "has_notes": False}
        for j, shape in enumerate(slide.shapes, 1):
            if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                s["picture_shapes"] += 1
                out["embedded_picture_count"] += 1
                try:
                    _ = shape.image.blob
                except Exception as e:
                    out["warnings"].append(f"Slide {i} picture {j} failed to resolve: {e}")
            if shape.has_text_frame:
                s["text_shapes"] += 1
                for para in shape.text_frame.paragraphs:
                    for r in para.runs:
                        if r.font.name:
                            fonts[r.font.name] += 1
            if min(shape.left, shape.top) < -10000 or shape.left + shape.width > prs.slide_width + 10000 or shape.top + shape.height > prs.slide_height + 10000:
                s["out_of_bounds"].append({"shape": j, "type": str(shape.shape_type),
                                           "left": shape.left, "top": shape.top,
                                           "right": shape.left + shape.width,
                                           "bottom": shape.top + shape.height})
        try:
            s["has_notes"] = bool(slide.notes_slide.notes_text_frame.text.strip())
        except Exception:
            s["has_notes"] = False
        if s["has_notes"]:
            out["speaker_notes_count"] += 1
        if s["out_of_bounds"]:
            out["warnings"].append(f"Slide {i} contains {len(s['out_of_bounds'])} shape(s) out of bounds")
        out["slides"].append(s)
    out["fonts_declared"] = dict(fonts)
    if not out["zip_integrity"]:
        out["warnings"].append("PPTX ZIP integrity check failed")
    if out["speaker_notes_count"] < len(prs.slides):
        out["warnings"].append("Some slides have no notes; check speaking script")
    return out


def render_pptx(pptx_file, out_dir, dpi=90):
    result = {"pdf": None, "pages_png": [], "montage": None, "warnings": []}
    if not shutil.which("libreoffice"):
        result["warnings"].append("LibreOffice unavailable: no PDF or slide PNG previews created")
        return result
    pdfdir=out_dir / "pdf"
    pdfdir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="lo_profile_") as profile:
        cmd=["libreoffice", "-env:UserInstallation=file://"+profile,
             "--headless", "--convert-to", "pdf", "--outdir", str(pdfdir), str(pptx_file)]
        p=subprocess.run(cmd,text=True,capture_output=True,timeout=90)
    pdf=pdfdir/(pptx_file.stem+".pdf")
    if p.returncode or not pdf.is_file():
        result["warnings"].append(f"LibreOffice conversion failed: {p.stderr[-500:]}")
        return result
    result["pdf"]=str(pdf)
    if not shutil.which("pdftoppm"):
        result["warnings"].append("pdftoppm unavailable: no PNG previews")
        return result
    prefix=out_dir/"slides"/"slide"
    prefix.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(["pdftoppm", "-png", "-r", str(dpi), str(pdf), str(prefix)],
                       check=True,timeout=120,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    except Exception as e:
        result["warnings"].append(f"PNG rendering failed: {e}")
        return result
    pngs=sorted(prefix.parent.glob("*.png"))
    result["pages_png"]=[str(p) for p in pngs]
    if pngs:
        from PIL import Image, ImageOps, ImageDraw
        thumbs=[]
        for p in pngs:
            im=Image.open(p).convert("RGB")
            im.thumbnail((450,260))
            canvas=Image.new("RGB",(470,290),"#E6E6E6")
            canvas.paste(im,((470-im.width)//2,8))
            ImageDraw.Draw(canvas).text((14,268),p.stem,fill="#222222")
            thumbs.append(canvas)
        ncol=3
        nrow=(len(thumbs)+ncol-1)//ncol
        board=Image.new("RGB",(ncol*470,nrow*290),"white")
        for i,im in enumerate(thumbs):
            board.paste(im,((i%ncol)*470,(i//ncol)*290))
        montage=out_dir/"montage.png"
        board.save(montage)
        result["montage"]=str(montage)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pptx")
    parser.add_argument("--out",required=True)
    parser.add_argument("--no-render",action="store_true")
    parser.add_argument("--dpi",type=int,default=90)
    args=parser.parse_args()
    pp=Path(args.pptx).resolve()
    if not pp.is_file():
        parser.error(f"PPTX does not exist: {pp}")
    out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=True)
    report=audit_pptx(pp)
    if not args.no_render:
        report["render"]=render_pptx(pp,out,args.dpi)
        report["warnings"].extend(report["render"].get("warnings",[]))
    else:
        report["render"]={"skipped":True}
    fp=out/"audit.json";fp.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"audit":str(fp),"slides":report["slide_count"],
                      "embedded_picture_count":report["embedded_picture_count"],
                      "notes":report["speaker_notes_count"],
                      "warnings":report["warnings"]},indent=2))
    if not report["zip_integrity"] or any(s["out_of_bounds"] for s in report["slides"]):
        raise SystemExit(2)


if __name__=="__main__":
    main()
