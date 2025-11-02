from __future__ import annotations

"""
Command-line orchestrator for the pipeline.
"""

import argparse
from pathlib import Path

from .config import PipelineConfig
from .epub import write_pagewise_epub, write_plain_text
from .logging import configure_logging, get_logger
from .ocr import extract_pdf
from .preprocess import clean_document
from .refine import AIRefiner
from .storage import write_document

log = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PDF to EPUB AI pipeline.")
    parser.add_argument("pdf", type=Path, help="Path to the input PDF.")
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory for final outputs (defaults to OUTPUT_DIR or ./output).",
    )
    parser.add_argument(
        "--temp-dir",
        type=str,
        default=None,
        help="Directory for intermediate artefacts (defaults to TEMP_DIR or ./temp).",
    )
    parser.add_argument(
        "--force-ocr",
        action="store_true",
        help="Force OCR even if the PDF contains extractable text.",
    )
    parser.add_argument(
        "--tesseract-lang",
        type=str,
        default=None,
        help="Tesseract language code (defaults to TESSERACT_LANG or 'eng').",
    )
    parser.add_argument(
        "--skip-ai",
        action="store_true",
        help="Skip AI refinement stage.",
    )
    parser.add_argument(
        "--ai-model",
        type=str,
        default=None,
        help="OpenAI model to use (defaults to AI_MODEL or gpt-4.1).",
    )
    parser.add_argument(
        "--max-cost",
        type=float,
        default=None,
        help="Maximum allowed cost in USD before requiring confirmation.",
    )
    parser.add_argument(
        "--confirm-cost",
        action="store_true",
        help="Proceed even if estimated cost exceeds --max-cost.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Process only the first N pages (useful for testing).",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR).",
    )
    return parser.parse_args()


def run_pipeline(args: argparse.Namespace) -> None:
    configure_logging(_parse_log_level(args.log_level))
    cfg = PipelineConfig.load(
        input_pdf=args.pdf,
        output_dir=args.output_dir,
        temp_dir=args.temp_dir,
        force_ocr=args.force_ocr,
        tesseract_lang=args.tesseract_lang,
        ai_model=args.ai_model,
        max_pages=args.max_pages,
        max_cost_limit=args.max_cost,
        confirm_cost=args.confirm_cost,
    )

    log.info("Starting pipeline for %s", cfg.input_pdf.name)

    doc = extract_pdf(cfg)
    write_document(doc, cfg.ocr_output, include_page_markers=True)

    cleaned = clean_document(doc)
    write_document(cleaned, cfg.clean_text, include_page_markers=False)

    final_doc = cleaned
    if not args.skip_ai:
        refiner = AIRefiner(cfg)
        final_doc = refiner.refine_document(cleaned)
        write_document(final_doc, cfg.refined_text, include_page_markers=False)
    else:
        log.info("Skipping AI refinement stage.")

    write_plain_text(final_doc, cfg)
    write_pagewise_epub(final_doc, cfg)
    log.info("Pipeline complete.")


def _parse_log_level(level: str) -> int:
    mapping = {
        "CRITICAL": 50,
        "ERROR": 40,
        "WARNING": 30,
        "INFO": 20,
        "DEBUG": 10,
    }
    return mapping.get(level.upper(), 20)


def main() -> None:
    args = parse_args()
    run_pipeline(args)


if __name__ == "__main__":
    main()
