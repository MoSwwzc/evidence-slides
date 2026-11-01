#!/usr/bin/env python3
"""Validate cross-links and completeness of an evidence-slides deck plan."""
import argparse
import json
from pathlib import Path

VALID_LAYOUTS = {"title", "figure", "split", "comparison", "process", "table", "summary"}
VALID_STATUS = {"fact", "interpretation", "hypothesis", "teaching-example"}
VALID_ASSET_KINDS = {"source-figure", "source-table", "generated-concept", "user-asset", "original-illustration"}


def inspect_plan(file):
    plan = json.loads(Path(file).read_text(encoding="utf-8"))
    errors, warnings = [], []
    if not isinstance(plan.get("meta", {}).get("title"), str) or not plan["meta"]["title"].strip():
        errors.append("meta.title is required")
    for key in ("sources", "claims", "assets", "slides", "variants"):
        if not isinstance(plan.get(key), list):
            errors.append(f"{key} must be a list")
    if errors:
        return errors, warnings
    def uniq(items, kind):
        ids = [x.get("id") for x in items]
        if not all(isinstance(x, str) and x for x in ids):
            errors.append(f"All {kind} entries need nonempty string id")
        if len(ids) != len(set(ids)):
            errors.append(f"Duplicate ids in {kind}")
        return set(ids)
    sources = uniq(plan["sources"], "sources")
    claims = uniq(plan["claims"], "claims")
    assets = uniq(plan["assets"], "assets")
    slides = uniq(plan["slides"], "slides")
    variants = uniq(plan["variants"], "variants")
    if not slides:
        errors.append("At least one slide is required")
    if not variants:
        errors.append("At least one variant is required")
    for s in plan["sources"]:
        if not s.get("file") or not s.get("locator"):
            warnings.append(f"Source {s.get('id')} needs file and locator for traceability")
    for c in plan["claims"]:
        if c.get("status") not in VALID_STATUS:
            errors.append(f"Claim {c.get('id')}: status must be {sorted(VALID_STATUS)}")
        if c.get("status") == "fact" and not c.get("source_ids"):
            errors.append(f"Fact claim {c.get('id')} has no sources")
        for sid in c.get("source_ids", []):
            if sid not in sources:
                errors.append(f"Claim {c.get('id')} has unknown source {sid}")
    base = Path(file).resolve().parent
    for a in plan["assets"]:
        if a.get("kind") not in VALID_ASSET_KINDS:
            errors.append(f"Asset {a.get('id')}: bad kind")
        if not a.get("path"):
            errors.append(f"Asset {a.get('id')}: path required")
        elif not (base / a["path"]).is_file():
            errors.append(f"Asset {a.get('id')}: file not found: {a['path']}")
        for sid in a.get("source_ids", []):
            if sid not in sources:
                errors.append(f"Asset {a.get('id')}: unknown source {sid}")
        if a.get("kind") in {"source-figure", "source-table"} and not a.get("source_ids"):
            warnings.append(f"Source asset {a.get('id')} has no traceable source id")
    for s in plan["slides"]:
        for vk, ly in s.get("variant_layouts", {}).items():
            if vk not in variants or ly not in VALID_LAYOUTS:
                errors.append(f"Slide {s.get('id')}: unsupported variant layout {vk}={ly}")
        if not s.get("title"):
            errors.append(f"Slide {s.get('id')}: title required")
        if s.get("layout") not in VALID_LAYOUTS:
            errors.append(f"Slide {s.get('id')}: unsupported layout {s.get('layout')}")
        for c in s.get("claim_ids", []):
            if c not in claims:
                errors.append(f"Slide {s.get('id')}: unknown claim {c}")
        for a in s.get("image_ids", []):
            if a not in assets:
                errors.append(f"Slide {s.get('id')}: unknown image {a}")
        if s.get("layout") == "table":
            t = s.get("table")
            if not isinstance(t, dict) or not t.get("headers") or not t.get("rows"):
                errors.append(f"Slide {s.get('id')}: table needs headers and rows")
            elif any(len(row) != len(t["headers"]) for row in t["rows"]):
                errors.append(f"Slide {s.get('id')}: table row/header length mismatch")
        if s.get("layout") == "figure" and not s.get("image_ids"):
            errors.append(f"Slide {s.get('id')}: figure layout requires image")
        if not s.get("notes"):
            warnings.append(f"Slide {s.get('id')} has no speaking notes")
        if s.get("duration_sec", 45) < 10:
            warnings.append(f"Slide {s.get('id')} speaking duration unusually short")
        if len(s.get("body", "")) > 700:
            warnings.append(f"Slide {s.get('id')}: very long body; risk of overflows")
        if len(s.get("bullets", [])) > 8:
            warnings.append(f"Slide {s.get('id')}: too many bullets for one slide")
    for v in plan["variants"]:
        if v.get("style") not in {"editorial", "visual"}:
            errors.append(f"Variant {v.get('id')}: style must be editorial or visual")
        if not v.get("theme"):
            errors.append(f"Variant {v.get('id')}: theme required")
    return errors, warnings


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("plan")
    p.add_argument("--report")
    args = p.parse_args()
    errors, warnings = inspect_plan(args.plan)
    result = {"valid": not errors, "errors": errors, "warnings": warnings}
    report = json.dumps(result, ensure_ascii=False, indent=2)
    print(report)
    if args.report:
        path = Path(args.report)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report + "\n", encoding="utf-8")
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
