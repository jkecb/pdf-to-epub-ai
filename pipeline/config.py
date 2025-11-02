from __future__ import annotations

"""
Configuration handling for the PDF-to-EPUB pipeline.

The config ensures environment variables, CLI overrides, and defaults are
resolved in a single place so that individual stages remain stateless.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Tuple
import os

from dotenv import load_dotenv


def _coerce_path(value: Optional[str], default: Path) -> Path:
    """Convert the provided path string to a resolved Path with fallback."""
    if not value:
        return default
    return Path(value).expanduser().resolve()


@dataclass
class PipelineConfig:
    """Strongly typed configuration for the pipeline."""

    input_pdf: Path
    temp_dir: Path
    output_dir: Path
    ocr_output: Path
    clean_text: Path
    refined_text: Path
    final_txt: Path
    final_epub: Path
    ai_model: str = "gpt-4.1"
    max_pages: Optional[int] = None
    max_tokens_per_chunk: int = 2500
    max_cost_limit: float = 10.0
    confirm_cost: bool = False
    tesseract_lang: str = "eng"
    force_ocr: bool = False
    ocr_engine: str = "text"
    page_range: Optional[Tuple[int, int]] = None
    openai_api_key: Optional[str] = field(default=None, repr=False)

    @staticmethod
    def load(
        input_pdf: Path,
        output_dir: Optional[str] = None,
        temp_dir: Optional[str] = None,
        *,
        force_ocr: bool = False,
        tesseract_lang: Optional[str] = None,
        ocr_engine: Optional[str] = None,
        ai_model: Optional[str] = None,
        max_pages: Optional[int] = None,
        page_range: Optional[Tuple[int, int]] = None,
        max_tokens_per_chunk: Optional[int] = None,
        max_cost_limit: Optional[float] = None,
        confirm_cost: bool = False,
        allow_missing_input: bool = False,
    ) -> "PipelineConfig":
        """
        Construct a PipelineConfig, loading environment defaults first and
        allowing CLI overrides to take precedence.
        """
        load_dotenv()

        openai_key = os.getenv("OPENAI_API_KEY")
        default_output_dir = _coerce_path(os.getenv("OUTPUT_DIR"), Path.cwd() / "output")
        default_temp_dir = _coerce_path(os.getenv("TEMP_DIR"), Path.cwd() / "temp")

        resolved_output = _coerce_path(output_dir, default_output_dir)
        resolved_temp = _coerce_path(temp_dir, default_temp_dir)
        resolved_input = input_pdf.expanduser().resolve()

        if not resolved_input.exists() and not allow_missing_input:
            raise FileNotFoundError(f"Input PDF not found: {resolved_input}")

        ocr_filename = resolved_temp / f"{resolved_input.stem}_ocr.txt"
        clean_filename = resolved_temp / f"{resolved_input.stem}_clean.txt"
        refined_filename = resolved_temp / f"{resolved_input.stem}_refined.txt"
        final_txt_path = resolved_output / f"{resolved_input.stem}_final.txt"
        final_epub_path = resolved_output / f"{resolved_input.stem}.epub"

        resolved_engine = (ocr_engine or os.getenv("OCR_ENGINE", "text")).lower()
        if resolved_engine not in {"text", "surya"}:
            raise ValueError(f"Unsupported OCR engine: {resolved_engine}")

        validated_range = _validate_page_range(page_range)

        cfg = PipelineConfig(
            input_pdf=resolved_input,
            temp_dir=resolved_temp,
            output_dir=resolved_output,
            ocr_output=ocr_filename,
            clean_text=clean_filename,
            refined_text=refined_filename,
            final_txt=final_txt_path,
            final_epub=final_epub_path,
            tesseract_lang=tesseract_lang
            or os.getenv("TESSERACT_LANG", "eng"),
            force_ocr=force_ocr,
            ocr_engine=resolved_engine,
            page_range=validated_range,
            ai_model=ai_model or os.getenv("AI_MODEL", "gpt-4.1"),
            max_pages=max_pages,
            max_tokens_per_chunk=int(
                max_tokens_per_chunk or os.getenv("MAX_TOKENS_PER_CHUNK", 2500)
            ),
            max_cost_limit=float(max_cost_limit or os.getenv("MAX_COST_LIMIT", 10.0)),
            confirm_cost=confirm_cost,
            openai_api_key=openai_key,
        )

        cfg.temp_dir.mkdir(parents=True, exist_ok=True)
        cfg.output_dir.mkdir(parents=True, exist_ok=True)

        return cfg


def _validate_page_range(
    page_range: Optional[Tuple[int, int]]
) -> Optional[Tuple[int, int]]:
    """Validate the provided 1-based inclusive page range."""
    if page_range is None:
        return None
    start, end = page_range
    if start < 1 or end < 1:
        raise ValueError("Page range values must be >= 1.")
    if end < start:
        raise ValueError("Page range end must be >= start.")
    return (start, end)


__all__ = ["PipelineConfig"]
