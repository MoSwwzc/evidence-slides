# Evidence Slides

![Cartoon illustration of the Evidence Slides workflow, from reading papers to checking finished slides](assets/workflow-illustration.png)

Evidence Slides is an agent skill for creating editable PowerPoint presentations from papers, reports, and other source materials. It combines source review, an evidence ledger, narrative planning, figure selection, slide generation, and visual checks. See [SKILL.md](SKILL.md) for the complete workflow.

## What it does

The skill supports paper reading presentations, literature comparisons, teaching, research proposals, and project reviews. It can work with papers, supplementary files, reports, existing presentations, figures, and optional design references. It separates scientific evidence from design references so that an example slide does not become a source of claims about a different project.

For a new presentation, the workflow develops a slide-by-slide narrative, selects figures and tables from the source materials, and prepares editable slide titles and annotations, speaker notes, and source references. When useful and supported by the host, it can also use generated conceptual illustrations. It does not generate experimental plots or treat generated illustrations as evidence.

The default workflow aims to produce two complete design variants with the same scientific content. A small revision to an existing presentation follows a narrower path and preserves the existing content and layout except for the requested changes. Users can also request an outline before a presentation is built.

## How the workflow works

### 📥 1. Give the agent your materials

Provide the paper or report and, when available, supplementary files, an existing presentation, or a design reference. Tell the agent who the audience is, how long the talk should be, and which language to use. The agent identifies which files provide scientific content and which serve only as writing or design references. If details are omitted, it uses the defaults described in [SKILL.md](SKILL.md).

### 🔎 2. Read the source and collect evidence

The agent reads the full text, figures, captions, tables, and relevant supplementary material. It records each important claim with its source location, such as a page, figure, or table, together with relevant experimental conditions and limitations. It distinguishes reported results from interpretation, hypotheses, and teaching examples.

The extraction script can collect candidate images and other assets. The agent checks those candidates against the original source, since extraction may miss vector graphics, labels, axes, or legends.

```bash
python scripts/extract_assets.py paper.pdf --out work/assets/paper
```

### 🧭 3. Plan the story

Before designing slides, the agent decides what the audience needs to understand and develops a slide-by-slide sequence. For each substantive slide, it considers the question or claim, the evidence or explanation, the conclusion, and how the slide connects to the next one. The sequence changes with the source: an experimental paper, a review, a teaching session, and a proposal do not all need the same structure.

### 🖼️ 4. Choose figures and prepare slide content

The agent selects relevant figures and tables from the provided sources, checks their context, and keeps necessary labels and legends. It prepares slide titles, explanations, speaker notes, and source references. If a table is rebuilt, its values and headers are checked against the source. Generated illustrations may be used for concepts when the host supports them, but they are not used as experimental evidence.

### 📝 5. Write and validate the presentation plan

The agent records sources, claims, assets, slide content, notes, and design variants in `deck_plan.json`. The [sample plan](examples/sample_plan.json) shows the format. The following command checks the plan structure and references; it does not establish whether scientific claims are true.

```bash
python scripts/validate_plan.py work/deck_plan.json
```

### 🛠️ 6. Build the presentation

The agent uses the plan to build editable slides. The supplied baseline renderer uses PptxGenJS; other supported editors may also be used. By default, the workflow aims to create two complete variants with different design choices while keeping the same claims and evidence. The baseline may need manual improvements for dense figures or an adapter for a supplied template.

```bash
node scripts/build_deck.cjs work/deck_plan.json --variant A --output work/A.pptx
node scripts/build_deck.cjs work/deck_plan.json --variant B --output work/B.pptx
```

### ✅ 7. Check, revise, and deliver

The agent renders the presentation when the required tools are available, inspects the slides, and checks figures, source references, notes, and layout. It corrects problems such as clipped content or missing images and repeats relevant checks. The audit script helps with structural checks and rendering; a successful script run does not replace visual or scientific review.

```bash
python scripts/render_and_audit.py work/A.pptx --out work/A_qa
```

The intended delivery includes the editable PPTX files and, when supported, PDFs, previews, notes, and a report of the checks performed. The agent should state any missing outputs or unavailable checks. See [quality.md](references/quality.md) for the full quality criteria.

For a small revision, the agent keeps the existing presentation and makes the requested changes without running the full redesign workflow. For an outline-first request, it delivers the outline and figure plan before building the slides.

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
