#!/usr/bin/env python3
"""
Heuristic OCR cleanup stage.

Reads OCR output with page markers, applies the new cleaning pipeline, and
writes the cleaned result back to disk.
"""

from pathlib import Path
import argparse

from pipeline.logging import configure_logging, get_logger
from pipeline.preprocess import clean_document
from pipeline.storage import read_document, write_document


log = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean OCR output heuristically.")
    parser.add_argument(
        "--in",
        dest="input",
        required=True,
        help="Input text file containing OCR output with page markers.",
    )
    parser.add_argument(
        "--out",
        dest="output",
        required=True,
        help="Output file for cleaned text.",
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
    cleaned = clean_document(document)

    output_path = Path(args.output).expanduser().resolve()
    write_document(cleaned, output_path, include_page_markers=False)
    log.info("Cleaned text written to %s", output_path)


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
