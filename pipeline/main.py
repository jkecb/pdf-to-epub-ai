from __future__ import annotations

"""
Shared command implementations for the pipeline CLI.
"""

from pathlib import Path

from .config import PipelineConfig
from .epub import write_pagewise_epub, write_plain_text
from .logging import configure_logging, get_logger
from .ocr import extract_pdf
from .preprocess import clean_document
from .refine import AIRefiner
from .storage import read_document, write_document

log = get_logger(__name__)


def run_pipeline(args) -> None:
    """Run the full PDF → EPUB pipeline."""
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


def run_ocr_command(args) -> None:
    """Extract text (direct or OCR) and write a page-marked text file."""
    configure_logging(_parse_log_level(args.log_level))
    cfg = PipelineConfig.load(
        input_pdf=args.pdf,
        force_ocr=args.force_ocr,
        max_pages=args.max_pages,
        allow_missing_input=False,
    )

    doc = extract_pdf(cfg)
    output_path = Path(args.output) if args.output else cfg.ocr_output
    write_document(doc, output_path, include_page_markers=True)
    log.info("OCR text written to %s", output_path)


def run_clean_command(args) -> None:
    """Apply heuristic cleanup to a page-marked text file."""
    configure_logging(_parse_log_level(args.log_level))
    input_path = Path(args.input)
    doc = read_document(input_path)
    cleaned = clean_document(doc)

    output_path = Path(args.output) if args.output else _derive_output_path(input_path, "_clean")
    write_document(cleaned, output_path, include_page_markers=False)
    log.info("Clean text written to %s", output_path)


def run_refine_command(args) -> None:
    """Send cleaned text through the OpenAI refinement stage."""
    configure_logging(_parse_log_level(args.log_level))
    input_path = Path(args.input)
    doc = read_document(input_path)

    pdf_source = Path(args.pdf) if args.pdf else input_path.with_suffix(".pdf")
    cfg = PipelineConfig.load(
        input_pdf=pdf_source,
        ai_model=args.ai_model,
        max_cost_limit=args.max_cost,
        confirm_cost=args.confirm_cost,
        allow_missing_input=not pdf_source.exists(),
    )

    output_path = Path(args.output) if args.output else _derive_output_path(input_path, "_refined")
    cfg.refined_text = output_path
    cfg.final_txt = output_path

    refiner = AIRefiner(cfg)
    refined_doc = refiner.refine_document(doc)
    write_document(refined_doc, output_path, include_page_markers=False)
    log.info("Refined text written to %s", output_path)


def run_epub_command(args) -> None:
    """Convert a cleaned/refined text file into an EPUB with page splits."""
    configure_logging(_parse_log_level(args.log_level))
    input_path = Path(args.input)
    doc = read_document(input_path)

    pdf_source = Path(args.pdf) if args.pdf else input_path.with_suffix(".pdf")
    cfg = PipelineConfig.load(
        input_pdf=pdf_source,
        allow_missing_input=not pdf_source.exists(),
    )

    output_path = Path(args.output) if args.output else input_path.with_suffix(".epub")
    cfg.final_epub = output_path

    write_pagewise_epub(doc, cfg)
    log.info("EPUB written to %s", output_path)


def _derive_output_path(source: Path, suffix: str) -> Path:
    """Append suffix before the file extension."""
    if source.suffix:
        return source.with_name(f"{source.stem}{suffix}{source.suffix}")
    return source.with_name(f"{source.name}{suffix}")


def _parse_log_level(level: str) -> int:
    mapping = {
        "CRITICAL": 50,
        "ERROR": 40,
        "WARNING": 30,
        "INFO": 20,
        "DEBUG": 10,
    }
    return mapping.get(level.upper(), 20)


__all__ = [
    "run_pipeline",
    "run_ocr_command",
    "run_clean_command",
    "run_refine_command",
    "run_epub_command",
]
