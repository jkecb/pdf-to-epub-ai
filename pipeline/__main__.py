from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .main import (
    run_clean_command,
    run_epub_command,
    run_ocr_command,
    run_pipeline,
    run_refine_command,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m pipeline",
        description="PDF to EPUB AI toolkit",
    )
    subparsers = parser.add_subparsers(
        title="commands", dest="command", required=True
    )

    # run (full pipeline)
    run_parser = subparsers.add_parser("run", help="Run the full PDF→EPUB pipeline.")
    run_parser.add_argument("pdf", type=Path, help="Path to the input PDF.")
    run_parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory for final outputs (defaults to OUTPUT_DIR or ./output).",
    )
    run_parser.add_argument(
        "--temp-dir",
        type=str,
        default=None,
        help="Directory for intermediate artefacts (defaults to TEMP_DIR or ./temp).",
    )
    run_parser.add_argument(
        "--force-ocr",
        action="store_true",
        help="Force OCR even if the PDF contains extractable text.",
    )
    run_parser.add_argument(
        "--tesseract-lang",
        type=str,
        default=None,
        help="OCR language code (defaults to TESSERACT_LANG or 'eng').",
    )
    run_parser.add_argument(
        "--skip-ai",
        action="store_true",
        help="Skip the OpenAI refinement stage.",
    )
    run_parser.add_argument(
        "--ai-model",
        type=str,
        default=None,
        help="OpenAI model to use (defaults to AI_MODEL or gpt-4.1).",
    )
    run_parser.add_argument(
        "--max-cost",
        type=float,
        default=None,
        help="Maximum allowed cost in USD before requiring confirmation.",
    )
    run_parser.add_argument(
        "--confirm-cost",
        action="store_true",
        help="Proceed even if estimated cost exceeds --max-cost.",
    )
    run_parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Process only the first N pages (useful for testing).",
    )
    run_parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR).",
    )
    run_parser.set_defaults(handler=run_pipeline)

    # ocr command
    ocr_parser = subparsers.add_parser("ocr", help="Extract text (direct or OCR).")
    ocr_parser.add_argument("pdf", type=Path, help="Path to the input PDF.")
    ocr_parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output text file (defaults to temp/<stem>_ocr.txt).",
    )
    ocr_parser.add_argument(
        "--force-ocr",
        action="store_true",
        help="Force OCR even if direct extraction succeeds.",
    )
    ocr_parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Process only the first N pages.",
    )
    ocr_parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR).",
    )
    ocr_parser.set_defaults(handler=run_ocr_command)

    # clean command
    clean_parser = subparsers.add_parser(
        "clean", help="Apply heuristic cleanup to OCR text."
    )
    clean_parser.add_argument("--input", required=True, type=Path, help="Input text file.")
    clean_parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output text file (defaults to *_clean.txt).",
    )
    clean_parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR).",
    )
    clean_parser.set_defaults(handler=run_clean_command)

    # refine command
    refine_parser = subparsers.add_parser(
        "refine", help="Send cleaned text through the OpenAI refinement stage."
    )
    refine_parser.add_argument("--input", required=True, type=Path, help="Input text file.")
    refine_parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output text file (defaults to *_refined.txt).",
    )
    refine_parser.add_argument(
        "--pdf",
        type=Path,
        default=None,
        help="Original PDF path (improves metadata; optional).",
    )
    refine_parser.add_argument(
        "--ai-model",
        type=str,
        default=None,
        help="OpenAI model to use (defaults to AI_MODEL or gpt-4.1).",
    )
    refine_parser.add_argument(
        "--max-cost",
        type=float,
        default=None,
        help="Maximum allowed cost in USD before requiring confirmation.",
    )
    refine_parser.add_argument(
        "--confirm-cost",
        action="store_true",
        help="Proceed even if estimated cost exceeds --max-cost.",
    )
    refine_parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR).",
    )
    refine_parser.set_defaults(handler=run_refine_command)

    # epub command
    epub_parser = subparsers.add_parser(
        "epub", help="Convert cleaned/refined text into an EPUB."
    )
    epub_parser.add_argument("--input", required=True, type=Path, help="Input text file.")
    epub_parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output EPUB path (defaults to input stem with .epub).",
    )
    epub_parser.add_argument(
        "--pdf",
        type=Path,
        default=None,
        help="Original PDF path for metadata (optional).",
    )
    epub_parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR).",
    )
    epub_parser.set_defaults(handler=run_epub_command)

    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.handler(args)


if __name__ == "__main__":
    main()
