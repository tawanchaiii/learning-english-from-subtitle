# Learning English from Subtitle

A Claude Code agent skill that turns movie subtitles into printable English exercises and grades the completed work from a scanned PDF.

## What it does

The `english-teacher` skill has two modes:

- **Generate** — takes a subtitle file (`.srt` / `.vtt`), auto-detects its CEFR level, and produces a CS188-style exercise booklet (vocabulary, comprehension, subjective writing) plus a vocabulary list PDF and a machine-readable guideline JSON used later for grading.
- **Assess** — takes a scanned PDF of the completed exercise and the matching guideline JSON, scores the multiple choice, evaluates the handwritten writing against a rubric, estimates the learner's CEFR level, and writes an assessment report PDF + markdown with a personalized study plan and movie recommendations.

## Requirements

- Python 3 with `jinja2` and `pytest`
- `xelatex` (TeX Live) for PDF generation
- [`docling-mcp`](https://github.com/docling-project/docling-mcp) for reading scanned PDFs (assess mode only)

## Setup

```bash
# Install Python deps
uv pip install -r requirements.txt --system

# Verify LaTeX toolchain
xelatex --version | head -1

# (Assess mode only) Add docling-mcp to your MCP config
#   "docling-mcp": {
#     "command": "uvx",
#     "args": ["--from", "docling-mcp", "docling-mcp-server", "--transport", "stdio"]
#   }
```

## Usage

The skill is invoked inside Claude Code as a slash command.

### Generate an exercise

```
/english-teacher generate path/to/Movie.srt --level B1
```

CEFR levels: `A1`, `A2`, `B1`, `B2`, `C1`, `C2`.

Outputs in `output/<movie-name>/`:

- `<movie>-exercise.pdf` — printable exercise (~33 questions)
- `<movie>-vocabulary.pdf` — tagged vocabulary list
- `<movie>-guideline.json` — answer key + rubric (keep this for assessment)

Workflow: print the exercise, watch the movie, fill it out by hand, then scan it.

### Assess a completed exercise

```
/english-teacher assess output/<movie-name> path/to/scanned.pdf
```

Outputs in the same folder:

- `<movie>-assessment.pdf` — graded report with feedback, CEFR estimate, study plan
- `<movie>-assessment.md` — markdown version of the same report

## Project structure

```
scripts/         Parsing and rendering pipeline
  parse_subtitle.py   .srt/.vtt -> scenes.json
  render_latex.py     JSON + Jinja2 template -> .tex
  compile_pdf.sh      xelatex wrapper
templates/       Jinja2 LaTeX templates (CS188 exam style)
  common.tex.j2, exercise.tex.j2, vocabulary.tex.j2, assessment.tex.j2
tests/           pytest suite
output/          Generated exercise folders (gitignored)
.agents/skills/english-teacher/SKILL.md   Skill definition (agent-compatible layout)
```

## Development

```bash
# Run tests
python3 -m pytest tests/ -v

# Compile a .tex file manually
bash scripts/compile_pdf.sh path/to/file.tex
```

## Exercise format

Each generated booklet contains three parts (CS188 UC Berkeley exam style, black and white, Computer Modern):

- **Part A — Vocabulary** (~15 multiple-choice, 5 options each): meaning-in-context and fill-in-the-blank.
- **Part B — Comprehension** (~10 multiple-choice): listening comprehension and grammar usage.
- **Part C — Writing** (~8 subjective): scene summaries, intent/emotion analysis, alternative dialogue, vocabulary-in-use. Each prints with a handwriting box.

The accompanying vocabulary PDF groups words by CEFR level and includes part of speech, meaning, a real quote from the movie, and a real-life example sentence.
