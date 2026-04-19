#!/usr/bin/env bash
# compile_pdf.sh — Compile .typ or .tex files to PDF
# Usage: bash scripts/compile_pdf.sh <file.typ|file.tex> [output-dir]
#
# For .typ files: uses typst compile
# For .tex files: uses xelatex (runs twice for cross-references)

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: bash scripts/compile_pdf.sh <file.typ|file.tex> [output-dir]"
    exit 1
fi

INPUT_FILE="$1"
OUTPUT_DIR="${2:-$(dirname "$INPUT_FILE")}"
BASENAME=$(basename "$INPUT_FILE")
EXTENSION="${BASENAME##*.}"
BASENAME_NOEXT="${BASENAME%.*}"

if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: File not found: $INPUT_FILE"
    exit 1
fi

if [ "$EXTENSION" = "typ" ]; then
    # Typst compilation
    if ! command -v typst &> /dev/null; then
        echo "Error: typst not found. Install it:"
        echo "  macOS:  brew install typst"
        echo "  Other:  https://github.com/typst/typst/releases"
        exit 1
    fi

    OUTPUT_PDF="$OUTPUT_DIR/$BASENAME_NOEXT.pdf"
    echo "Compiling $INPUT_FILE to $OUTPUT_PDF"

    typst compile "$INPUT_FILE" "$OUTPUT_PDF"

    if [ -f "$OUTPUT_PDF" ]; then
        echo "Success: $OUTPUT_PDF"
    else
        echo "Error: PDF was not generated"
        exit 1
    fi

elif [ "$EXTENSION" = "tex" ]; then
    # XeLaTeX compilation (legacy)
    if ! command -v xelatex &> /dev/null; then
        echo "Error: xelatex not found. Install TeX Live:"
        echo "  macOS:  brew install --cask mactex"
        echo "  Ubuntu: sudo apt-get install texlive-xetex texlive-fonts-recommended"
        exit 1
    fi

    echo "Compiling $INPUT_FILE to $OUTPUT_DIR/$BASENAME_NOEXT.pdf"

    # Run xelatex twice for cross-references
    xelatex -interaction=nonstopmode -output-directory="$OUTPUT_DIR" "$INPUT_FILE" > /dev/null 2>&1
    xelatex -interaction=nonstopmode -output-directory="$OUTPUT_DIR" "$INPUT_FILE" > /dev/null 2>&1

    # Clean up auxiliary files
    for ext in aux log out toc fls fdb_latexmk synctex.gz; do
        rm -f "$OUTPUT_DIR/$BASENAME_NOEXT.$ext"
    done

    if [ -f "$OUTPUT_DIR/$BASENAME_NOEXT.pdf" ]; then
        echo "Success: $OUTPUT_DIR/$BASENAME_NOEXT.pdf"
    else
        echo "Error: PDF was not generated"
        exit 1
    fi

else
    echo "Error: Unsupported file extension: .$EXTENSION (expected .typ or .tex)"
    exit 1
fi