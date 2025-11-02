#!/bin/bash
# This script runs the new Python orchestrator for the PDF to EPUB pipeline.

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: $0 <input.pdf> [--skip-ai] [additional args]"
    exit 1
fi

INPUT_PDF="$1"
shift || true

python -m pipeline "$INPUT_PDF" "$@"
