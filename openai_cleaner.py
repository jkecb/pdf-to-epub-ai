#!/usr/bin/env python3
"""
AI-based text refinement using OpenAI API.

The logic is now delegated to pipeline.refine.AIRefiner for consistency
across CLI and orchestrated runs.
"""

from pathlib import Path
import argparse

from pipeline.config import PipelineConfig
from pipeline.logging import configure_logging, get_logger
from pipeline.refine import AIRefiner
from pipeline.storage import read_document, write_document


log = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Refine cleaned OCR text using an OpenAI model."
    )
    parser.add_argument("--in", dest="input", required=True, help="Input text file.")
    parser.add_argument("--out", dest="output", required=True, help="Output text file.")
    parser.add_argument(
        "--source-pdf",
        dest="source_pdf",
        default=None,
        help="Original PDF path (improves metadata, optional).",
    )
    parser.add_argument(
        "--model",
        dest="model",
        default=None,
        help="OpenAI model to use (defaults to env AI_MODEL or gpt-4.1).",
    )
    parser.add_argument(
        "--max-cost",
        dest="max_cost",
        type=float,
        default=None,
        help="Maximum allowed cost in USD.",
    )
    parser.add_argument(
        "--confirm-cost",
        dest="confirm_cost",
        action="store_true",
        help="Proceed even if estimated cost exceeds --max-cost.",
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

    source_pdf = Path(args.source_pdf).expanduser().resolve() if args.source_pdf else Path(args.input).resolve()

    cfg = PipelineConfig.load(
        input_pdf=source_pdf,
        ai_model=args.model,
        max_cost_limit=args.max_cost,
        confirm_cost=args.confirm_cost,
        allow_missing_input=not source_pdf.exists(),
    )

    input_path = Path(args.input).expanduser().resolve()
    document = read_document(input_path)

    refiner = AIRefiner(cfg)
    refined = refiner.refine_document(document)

    output_path = Path(args.output).expanduser().resolve()
    write_document(refined, output_path, include_page_markers=False)
    log.info("Refined text written to %s", output_path)


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
