#!/usr/bin/env python3
"""
Extract text from PDF files, performing OCR when required.

This thin wrapper reuses the core pipeline modules so that CLI usage stays
compatible with the previous script while benefiting from the new architecture.
"""

from pathlib import Path
import argparse

from pipeline.config import PipelineConfig
from pipeline.logging import configure_logging, get_logger
from pipeline.ocr import extract_pdf
from pipeline.storage import write_document


log = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract text from a PDF, using OCR if necessary."
    )
    parser.add_argument("--in", dest="input", required=True, help="Input PDF path.")
    parser.add_argument(
        "--out",
        dest="output",
        help="Output text file (defaults to temp/<name>_ocr.txt).",
    )
    parser.add_argument(
        "--force-ocr",
        action="store_true",
        help="Force OCR even if selectable text is detected.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Process only the first N pages (for testing).",
    )
    parser.add_argument(
        "--language",
        dest="language",
        default=None,
        help="Tesseract language code (defaults to env TESSERACT_LANG or 'eng').",
    )
    parser.add_argument(
        "--log-level",
        dest="log_level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    configure_logging(_parse_log_level(args.log_level))

    cfg = PipelineConfig.load(
        input_pdf=Path(args.input),
        force_ocr=args.force_ocr,
        tesseract_lang=args.language,
        max_pages=args.max_pages,
    )

    doc = extract_pdf(cfg)
    target = Path(args.output).expanduser().resolve() if args.output else cfg.ocr_output
    write_document(doc, target, include_page_markers=True)
    log.info("Wrote OCR text to %s", target)


def _parse_log_level(level: str) -> int:
    return {
        "CRITICAL": 50,
        "ERROR": 40,
        "WARNING": 30,
        "INFO": 20,
        "DEBUG": 10,
    }.get(level.upper(), 20)


if __name__ == "__main__":
    main()
