#!/usr/bin/env python3
"""
Convert cleaned or refined text into an EPUB while preserving page structure.
"""

from pathlib import Path
import argparse

from pipeline.config import PipelineConfig
from pipeline.epub import write_pagewise_epub
from pipeline.logging import configure_logging, get_logger
from pipeline.storage import read_document


log = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert text to EPUB format.")
    parser.add_argument("--in", dest="input", required=True, help="Input text file.")
    parser.add_argument("--out", dest="output", required=True, help="Output EPUB file.")
    parser.add_argument(
        "--source-pdf",
        dest="source_pdf",
        default=None,
        help="Original PDF path for metadata (optional).",
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

    input_path = Path(args.input).expanduser().resolve()
    document = read_document(input_path)

    source_pdf = (
        Path(args.source_pdf).expanduser().resolve()
        if args.source_pdf
        else input_path
    )

    cfg = PipelineConfig.load(
        input_pdf=source_pdf,
        allow_missing_input=not source_pdf.exists(),
    )

    cfg.final_epub = Path(args.output).expanduser().resolve()

    write_pagewise_epub(document, cfg)
    log.info("EPUB written to %s", cfg.final_epub)


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
