# Learning English from Subtitle

## Overview

Agent skill project that generates English exercises from movie subtitles and assesses completed exercises.

## Commands

- `/english-teacher generate <subtitle-file> --level <CEFR>` — Generate exercises from subtitle
- `/english-teacher assess <movie-folder> <scanned-pdf>` — Assess completed exercise

## Project Structure

- `scripts/` — Python scripts for parsing and rendering
- `templates/` — Jinja2 LaTeX templates
- `output/` — Generated exercise folders (gitignored)
- `tests/` — pytest test suite

## Development

```bash
# Install dependencies
uv pip install -r requirements.txt --system

# Run tests
python3 -m pytest tests/ -v

# Compile a .tex file to PDF
bash scripts/compile_pdf.sh <file.tex>
```

## Dependencies

- Python 3 with jinja2
- xelatex (TeX Live) for PDF generation
- docling-mcp for reading scanned PDFs (assess mode only)
