# Evidence Slides

Evidence Slides is an agent skill for creating editable PowerPoint presentations from papers, reports, and other source materials. It combines source review, an evidence ledger, narrative planning, figure selection, slide generation, and visual checks. See [SKILL.md](SKILL.md) for the complete workflow.

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
