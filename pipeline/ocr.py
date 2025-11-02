from __future__ import annotations

"""
OCR and text extraction utilities supporting direct text extraction and Surya.
"""

from typing import List, Optional, Sequence, Tuple
import tempfile

from .config import PipelineConfig
from .logging import get_logger
from .pages import DocumentText, PageText

log = get_logger(__name__)

try:
    import fitz  # type: ignore

    PYMUPDF_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    PYMUPDF_AVAILABLE = False
    fitz = None  # type: ignore
    log.warning("PyMuPDF not available; direct text extraction disabled.")

try:
    import surya  # noqa: F401

    SURYA_AVAILABLE = True
except ImportError:  # pragma: no cover
    SURYA_AVAILABLE = False
    log.debug("Surya OCR not available; surya engine disabled.")


_SURYA_PREDICTORS = None  # type: ignore[assignment]


def extract_pdf(cfg: PipelineConfig) -> DocumentText:
    """
    Extract text from PDF according to the configured OCR engine.

    Returns:
        DocumentText: page-oriented text content.
    """
    log.info("Extracting text from %s using %s engine.", cfg.input_pdf, cfg.ocr_engine)

    engine = cfg.ocr_engine
    if engine == "text":
        return _extract_via_text(cfg)
    if engine == "surya":
        return _extract_via_surya(cfg)

    raise ValueError(f"Unsupported OCR engine: {engine}")


def _extract_via_text(cfg: PipelineConfig) -> DocumentText:
    _ensure_pymupdf()
    doc = fitz.open(cfg.input_pdf)  # type: ignore[arg-type]
    try:
        indices = _select_page_indices(len(doc), cfg)
        pages: List[PageText] = []
        for page_idx in indices:
            page = doc.load_page(page_idx)
            text = page.get_text()
            pages.append(PageText(index=page_idx + 1, raw=_format_page(page_idx + 1, text)))
    finally:
        doc.close()

    log.info("Direct text extraction completed (%d pages).", len(pages))
    return DocumentText(source=cfg.input_pdf, pages=pages)


def _extract_via_surya(cfg: PipelineConfig) -> DocumentText:
    if not SURYA_AVAILABLE:
        raise RuntimeError("Surya OCR not available. Install surya-ocr to enable this engine.")

    _ensure_pymupdf()
    doc = fitz.open(cfg.input_pdf)  # type: ignore[arg-type]
    total_pages = len(doc)
    doc.close()

    indices = _select_page_indices(total_pages, cfg)
    page_range_arg = _compress_indices(indices)

    from surya.scripts.config import CLILoader  # type: ignore
    from surya.common.surya.schema import TaskNames  # type: ignore

    with tempfile.TemporaryDirectory() as temp_dir:
        loader_kwargs = {
            "output_dir": temp_dir,
            "page_range": page_range_arg,
            "debug": False,
            "images": False,
        }
        loader = CLILoader(str(cfg.input_pdf), loader_kwargs, highres=True)
        selected_indices = loader.page_range or list(range(len(loader.images)))
        if not loader.images:
            raise RuntimeError("Surya loader failed to render any pages from the PDF.")

        foundation, detector, recognizer = _get_surya_predictors()
        task_names = [TaskNames.ocr_with_boxes] * len(loader.images)
        predictions_by_image = recognizer(
            loader.images,
            task_names=task_names,
            det_predictor=detector,
            highres_images=loader.highres_images,
            math_mode=True,
        )

    pages: List[PageText] = []
    for pred, page_idx in zip(predictions_by_image, selected_indices):
        page_number = page_idx + 1
        pred_dict = pred.model_dump()
        text_lines = pred_dict.get("text_lines", [])
        text = "\n".join(
            line.get("text")
            for line in text_lines
            if isinstance(line, dict) and line.get("text")
        ).strip()
        pages.append(PageText(index=page_number, raw=_format_page(page_number, text)))

    log.info("Surya OCR extraction completed (%d pages).", len(pages))
    return DocumentText(source=cfg.input_pdf, pages=pages)


def _format_page(index: int, text: str) -> str:
    """Annotate text with a consistent page marker for downstream processing."""
    text = (text or "").replace("\f", "").strip()
    header = f"--- Page {index} ---"
    if text:
        return f"{header}\n{text}"
    return header


def _select_page_indices(total_pages: int, cfg: PipelineConfig) -> List[int]:
    """Resolve zero-based page indices based on config constraints."""
    if total_pages <= 0:
        raise ValueError("The source PDF contains no pages.")

    if cfg.page_range:
        start_one, end_one = cfg.page_range
        if start_one > total_pages:
            raise ValueError(
                f"Page range start {start_one} exceeds document length ({total_pages})."
            )
        end_one = min(end_one, total_pages)
        indices = list(range(start_one - 1, end_one))
    else:
        indices = list(range(total_pages))

    if cfg.max_pages is not None:
        indices = indices[: cfg.max_pages]

    if not indices:
        raise ValueError("No pages selected for extraction. Adjust --page-range or --max-pages.")

    return indices


def _compress_indices(indices: Sequence[int]) -> str:
    """Compress a sorted sequence of zero-based indices into CLI-friendly ranges."""
    if not indices:
        return ""
    ranges: List[Tuple[int, int]] = []
    start = prev = indices[0]
    for value in indices[1:]:
        if value == prev + 1:
            prev = value
            continue
        ranges.append((start, prev))
        start = prev = value
    ranges.append((start, prev))

    parts = []
    for start, end in ranges:
        if start == end:
            parts.append(str(start))
        else:
            parts.append(f"{start}-{end}")
    return ",".join(parts)


def _get_surya_predictors():
    """Initialise and cache Surya predictor components."""
    global _SURYA_PREDICTORS  # type: ignore[global-variable-not-assigned]
    if _SURYA_PREDICTORS is None:
        from surya.logging import configure_logging as configure_surya_logging  # type: ignore
        from surya.foundation import FoundationPredictor  # type: ignore
        from surya.detection import DetectionPredictor  # type: ignore
        from surya.recognition import RecognitionPredictor  # type: ignore

        configure_surya_logging()
        foundation = FoundationPredictor()
        detector = DetectionPredictor()
        recognizer = RecognitionPredictor(foundation)
        _SURYA_PREDICTORS = (foundation, detector, recognizer)
    return _SURYA_PREDICTORS


def _ensure_pymupdf() -> None:
    if not PYMUPDF_AVAILABLE:
        raise RuntimeError("PyMuPDF not available. Install pymupdf to extract text or render pages.")


__all__ = ["extract_pdf"]
