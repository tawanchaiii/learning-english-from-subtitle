# Learning English from Subtitle

## Overview

Agent skill project that generates English exercises from movie subtitles and assesses completed exercises.

## Commands

- `/english-teacher generate <subtitle-file> --level <CEFR>` — Generate exercises from subtitle
- `/english-teacher listening <subtitle-file> --level <CEFR>` — Generate TOEFL-style listening exercises with TTS audio
- `/english-teacher assess <movie-folder> <scanned-pdf>` — Assess completed exercise

## Project Structure

- `scripts/` — Python scripts for parsing, rendering, and TTS generation
- `templates/` — Jinja2 Typst templates (`.typ.j2`)
- `output/` — Generated exercise folders (gitignored)
- `tests/` — pytest test suite

## Development

```bash
# Install dependencies
uv pip install -r requirements.txt --system

# Run tests
python3 -m pytest tests/ -v

# Compile a .typ file to PDF
bash scripts/compile_pdf.sh <file.typ>
```

## Dependencies

- Python 3 with jinja2
- typst for PDF generation (`brew install typst`)
- mlx_audio + Qwen3-TTS model for TTS generation (listening mode only)
- docling-mcp for reading scanned PDFs (assess mode only)