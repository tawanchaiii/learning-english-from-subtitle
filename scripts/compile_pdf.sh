#!/usr/bin/env bash
# compile_pdf.sh — Compile a Typst .typ file to PDF
# Usage: bash scripts/compile_pdf.sh <file.typ> [output-dir]

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: bash scripts/compile_pdf.sh <file.typ> [output-dir]"
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

if [ "$EXTENSION" != "typ" ]; then
    echo "Error: Unsupported file extension: .$EXTENSION (expected .typ)"
    exit 1
fi

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
