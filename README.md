# Evidence Slides

Evidence Slides is an agent skill for creating editable PowerPoint presentations from papers, reports, and other source materials. It combines source review, an evidence ledger, narrative planning, figure selection, slide generation, and visual checks. See [SKILL.md](SKILL.md) for the complete workflow.

## What it does

The skill supports paper reading presentations, literature comparisons, teaching, research proposals, and project reviews. It can work with papers, supplementary files, reports, existing presentations, figures, and optional design references. It separates scientific evidence from design references so that an example slide does not become a source of claims about a different project.

For a new presentation, the workflow develops a slide-by-slide narrative, selects figures and tables from the source materials, and prepares editable slide titles and annotations, speaker notes, and source references. When useful and supported by the host, it can also use generated conceptual illustrations. It does not generate experimental plots or treat generated illustrations as evidence.

The default workflow aims to produce two complete design variants with the same scientific content. A small revision to an existing presentation follows a narrower path and preserves the existing content and layout except for the requested changes. Users can also request an outline before a presentation is built.

## Workflow

The agent first checks the available tools and reads the source materials, including figures, captions, tables, and supplementary content. It records the source and conditions for each substantive claim, along with missing or uncertain evidence.

It then develops the central message and a slide-by-slide outline before choosing layouts. It selects relevant figures and tables, prepares slide text and speaker notes, and records the content and assets in a presentation plan. The supplied scripts can extract candidate assets and validate the plan; the agent must still check whether the evidence and selected figures are appropriate.

The presentation is built from the plan using an available presentation editor. The supplied baseline uses PptxGenJS. After generation, the agent renders and inspects the slides, checks their content and source references, and revises issues before delivery. The actual checks and outputs depend on the tools available in the host environment.

## Use

Clone this repository into a directory named `evidence-slides` in the skills directory of a compatible agent, then restart or reload the agent if needed. For Codex, the user skills directory is `~/.codex/skills/`.

```bash
git clone https://github.com/MoSwwzc/evidence-slides.git ~/.codex/skills/evidence-slides
```

Ask the agent to use Evidence Slides with your source files. The agent must read the source, prepare the presentation plan, and verify the generated slides; the scripts do not independently read and interpret a paper or call an LLM.

## Runtime

The portable baseline requires Python 3.10 or later and Node.js 20 or later. From the skill directory, install the dependencies with:

```bash
python -m pip install -r requirements.txt
npm install
```

LibreOffice and Poppler are needed for the described PDF export and raster preview workflow. See [runtime.md](references/runtime.md) for commands and limitations, and [sample_plan.json](examples/sample_plan.json) for the plan format.

Source figures and data may be subject to third-party rights. Review provenance and permissions before sharing a presentation.
