# Learning English from Subtitle

A Claude Code agent skill that turns movie subtitles into printable English exercises and grades the completed work from a scanned PDF.

## What it does

The `english-teacher` skill has three modes:

- **Generate** — takes a subtitle file (`.srt` / `.vtt`), auto-detects its CEFR level, and produces a CS188-style exercise booklet (vocabulary, comprehension, subjective writing) plus a vocabulary list PDF and a machine-readable guideline JSON used later for grading.
- **Listening** — takes a subtitle file and CEFR level, generates TOEFL-style listening exercises with audio tracks synthesized by Qwen3-TTS running locally on Apple Silicon via MLX-Audio.
- **Assess** — takes a scanned PDF of the completed exercise and the matching guideline JSON, scores the multiple choice, evaluates the handwritten writing against a rubric, estimates the learner's CEFR level, and writes an assessment report PDF + markdown with a personalized study plan and movie recommendations.

## Requirements

- Python 3 with `jinja2` and `pytest`
- `typst` for PDF generation (primary; `brew install typst`)
- `xelatex` (TeX Live) for PDF generation (legacy fallback; `brew install --cask mactex`)
- `mlx_audio` for TTS generation (listening mode): `pip install mlx_audio`
- Qwen3-TTS model (listening mode): download from [MLX Community](https://huggingface.co/collections/mlx-community/qwen3-tts) to `models/`
- [`docling-mcp`](https://github.com/docling-project/docling-mcp) for reading scanned PDFs (assess mode only)

## Setup

```bash
# Install Python deps
uv pip install -r requirements.txt --system

# Install typst (primary PDF engine)
brew install typst

# (Legacy) Install xelatex fallback
# brew install --cask mactex

# For listening exercises: install mlx_audio
pip install mlx_audio

# Download Qwen3-TTS model (listening mode)
# Choose one:
#   CustomVoice (pre-defined speakers): https://huggingface.co/mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-8bit
#   VoiceDesign (text-described voices): https://huggingface.co/mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-8bit
#   Base (voice cloning): https://huggingface.co/mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit
# Download ALL files including speech_tokenizer/ to models/

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

### Generate a listening exercise

```
/english-teacher listening path/to/Movie.srt --level B1
```

Optional flags:
- `--model-path` — Path to Qwen3-TTS model (default: `models/Qwen3-TTS-12Hz-1.7B-CustomVoice-8bit`)
- `--tts-mode` — Voice mode: `custom` (default), `design`, or `base`

Generates TOEFL-style listening exercises with *audio tracks* synthesized by Qwen3-TTS running locally on Apple Silicon via MLX-Audio.

Outputs in `output/<movie-name>/`:

- `<movie>-listening.pdf` — printable listening exercise (short conversations + longer talks)
- `<movie>-listening-guideline.json` — answer key + rubric
- `audio/` — MP3 audio tracks for each passage

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
  render.py            JSON + Jinja2 template -> .typ or .tex
  render_latex.py      (legacy) JSON + Jinja2 template -> .tex
  generate_tts.py      Text -> audio via Qwen3-TTS / MLX-Audio
  compile_pdf.sh      typst/xelatex wrapper
templates/       Jinja2 templates (Typst .typ.j2 primary; LaTeX .tex.j2 legacy)
  common.typ.j2, exercise.typ.j2, vocabulary.typ.j2, assessment.typ.j2, listening.typ.j2
  common.tex.j2, exercise.tex.j2, vocabulary.tex.j2, assessment.tex.j2, listening.tex.j2
tests/           pytest suite
output/          Generated exercise folders (gitignored)
.agents/skills/english-teacher/SKILL.md   Skill definition (agent-compatible layout)
```

## Development

```bash
# Run tests
python3 -m pytest tests/ -v

# Compile a .typ file to PDF
bash scripts/compile_pdf.sh path/to/file.typ

# Compile a .tex file to PDF (legacy)
bash scripts/compile_pdf.sh path/to/file.tex
```

## Exercise format

Each generated booklet contains three parts (CS188 UC Berkeley exam style, black and white, New Computer Modern font):

- **Part A — Vocabulary** (~15 multiple-choice, 5 options each): meaning-in-context and fill-in-the-blank.
- **Part B — Comprehension** (~10 multiple-choice): listening comprehension and grammar usage.
- **Part C — Writing** (~8 subjective): scene summaries, intent/emotion analysis, alternative dialogue, vocabulary-in-use. Each prints with a handwriting box.

The accompanying vocabulary PDF groups words by CEFR level and includes part of speech, meaning, a real quote from the movie, and a real-life example sentence.

## Listening exercise format

TOEFL-style listening exercises with audio tracks:

- **Part A — Short Conversations** (~3 passages, 1 question each): brief dialogues with main idea, detail, or inference questions.
- **Part B — Longer Talks** (~3 passages, 2–3 questions each): extended dialogues/monologues with main idea, detail, inference, purpose, and attitude questions.

Audio tracks are generated locally using Qwen3-TTS via MLX-Audio on Apple Silicon.