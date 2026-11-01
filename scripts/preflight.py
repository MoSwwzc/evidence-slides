#!/usr/bin/env python3
"""Inspect portable prerequisites without invoking remote services."""
import argparse
import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path


def version_of(program):
    executable = shutil.which(program)
    if not executable:
        return {"available": False, "path": None}
    try:
        p = subprocess.run([program, "--version"], text=True, capture_output=True, timeout=6)
        first = (p.stdout or p.stderr).splitlines()
        return {"available": True, "path": executable, "version": first[0] if first else "unknown"}
    except Exception:
        return {"available": True, "path": executable, "version": "unknown"}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", help="Optional JSON report path")
    args = p.parse_args()
    modules = ["pypdf", "pptx", "PIL"]
    report = {
        "python_modules": {m: importlib.util.find_spec(m) is not None for m in modules},
        "executables": {p: version_of(p) for p in ["node", "npm", "libreoffice", "pdftoppm", "fc-match"]},
        "font_examples": {},
        "host_imagegen": "not-detectable-from-this-script",
        "notes": ["Image generation and any hosted connectors are capabilities of the calling agent, not this CLI.",
                  "If a renderer is missing, PPTX generation can still work but PDF and PNG previews may not."],
    }
    if shutil.which("fc-match"):
        for font in ("Arial", "Noto Sans CJK SC", "Microsoft YaHei"):
            try:
                v = subprocess.check_output(["fc-match", "-f", "%{family}", font], text=True, timeout=5)
                report["font_examples"][font] = v.strip()
            except Exception:
                report["font_examples"][font] = "unavailable"
    try:
        p = subprocess.run(["node", "-e", "require('pptxgenjs');require('image-size')"],
                           text=True, capture_output=True, timeout=8, cwd=str(Path(__file__).resolve().parent.parent))
        report["node_dependencies"] = p.returncode == 0
    except Exception:
        report["node_dependencies"] = False
    report["ready_for_pptx"] = all(report["python_modules"].values()) and report["node_dependencies"]
    report["ready_for_pdf_preview"] = report["executables"]["libreoffice"]["available"]
    report["ready_for_png_preview"] = report["ready_for_pdf_preview"] and report["executables"]["pdftoppm"]["available"]
    content = json.dumps(report, indent=2, ensure_ascii=False)
    print(content)
    if args.out:
        dest = Path(args.out)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
