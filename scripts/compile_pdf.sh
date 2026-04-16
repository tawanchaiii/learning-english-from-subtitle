#!/usr/bin/env bash
# compile_pdf.sh — Compile .tex files to PDF using xelatex
# Usage: bash scripts/compile_pdf.sh <file.tex> [output-dir]
#
# Runs xelatex twice (for cross-references like page numbers),
# then cleans up auxiliary files.

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: bash scripts/compile_pdf.sh <file.tex> [output-dir]"
    exit 1
fi

TEX_FILE="$1"
OUTPUT_DIR="${2:-$(dirname "$TEX_FILE")}"

if [ ! -f "$TEX_FILE" ]; then
    echo "Error: File not found: $TEX_FILE"
    exit 1
fi

if ! command -v xelatex &> /dev/null; then
    echo "Error: xelatex not found. Install TeX Live:"
    echo "  macOS:  brew install --cask mactex"
    echo "  Ubuntu: sudo apt-get install texlive-xetex texlive-fonts-recommended"
    exit 1
fi

BASENAME=$(basename "$TEX_FILE" .tex)

echo "Compiling $TEX_FILE to $OUTPUT_DIR/$BASENAME.pdf"

# Run xelatex twice for cross-references (page numbers, TOC)
xelatex -interaction=nonstopmode -output-directory="$OUTPUT_DIR" "$TEX_FILE" > /dev/null 2>&1
xelatex -interaction=nonstopmode -output-directory="$OUTPUT_DIR" "$TEX_FILE" > /dev/null 2>&1

# Clean up auxiliary files
for ext in aux log out toc fls fdb_latexmk synctex.gz; do
    rm -f "$OUTPUT_DIR/$BASENAME.$ext"
done

if [ -f "$OUTPUT_DIR/$BASENAME.pdf" ]; then
    echo "Success: $OUTPUT_DIR/$BASENAME.pdf"
else
    echo "Error: PDF was not generated"
    exit 1
fi
