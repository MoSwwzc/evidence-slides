# Minimal plan JSON specification

`deck_plan.json` is the structured handoff from evidence/narrative planning to PowerPoint rendering. See `examples/sample_plan.json`.

## Required top-level fields
- `meta`: `title` (string), `subtitle` (optional), `language` (optional), `minutes` (optional), `aspect` (`16:9` by default).
- `sources`: list of `{id,file,locator,type?}`; paths may be source names if the original is not locally available during rendering, but every displayed scientific claim must be grounded in an actual source.
- `claims`: list of `{id,text,status,source_ids,scope?}`. Status: `fact`, `interpretation`, `hypothesis`, `teaching-example`. A fact cannot have empty `source_ids`.
- `assets`: list of `{id,path,kind,source_ids?,description?}`. Path resolves relative to the JSON file. `kind` is `source-figure`, `source-table`, `generated-concept`, `user-asset`, or `original-illustration`.
- `slides`: ordered list of `{id,title,layout,body?,bullets?,image_ids?,claim_ids?,table?,notes?,duration_sec?,sources?}`. Supported baseline layouts: `title`, `figure`, `split`, `comparison`, `process`, `table`, `summary`. `table` is `{headers:[...],rows:[[...],...]}`. Optional `variant_layouts:{"A":"figure","B":"split"}` overrides layout while retaining all shared content and claims. Other fields can be carried for richer host-specific rendering.
- `variants`: list of `{id,theme,style}`. Built-in `theme` names: `academic-light`, `conference-dark`. `style`: `editorial` or `visual`.

## Semantics
Source ids and asset ids must resolve. When images have source provenance, `source_ids` should resolve to `sources`. Evidence-backed results should use `claims` linking to source ids. Exact numeric values on the slide must occur in the source or recorded note; validator cannot establish source truth automatically.

`slides[].sources` may include human-readable source descriptions in the notes; the builder merges them with referenced claims to fill `[Sources]`. A missing source for a claim marked `fact` is a fatal validator error.

## ImageGen
For generated concept images, record the generated file path and mark `kind=generated-concept`. The builder does not call ImageGen. Do not record merely proposed images as present assets.
