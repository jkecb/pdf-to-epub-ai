from __future__ import annotations

"""
OCR and text extraction utilities.
"""

from pathlib import Path
from typing import List, Optional
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
    from pdf2image import convert_from_path  # type: ignore

    PDF2IMAGE_AVAILABLE = True
except ImportError:  # pragma: no cover
    PDF2IMAGE_AVAILABLE = False
    convert_from_path = None  # type: ignore
    log.warning("pdf2image not available; OCR image conversion fallback disabled.")

try:
    from PIL import Image  # type: ignore
    import pytesseract  # type: ignore

    TESSERACT_AVAILABLE = True
except ImportError:  # pragma: no cover
    Image = None  # type: ignore
    pytesseract = None  # type: ignore
    TESSERACT_AVAILABLE = False
    log.warning("pytesseract not available; OCR fallback disabled.")


def extract_pdf(cfg: PipelineConfig) -> DocumentText:
    """
    Extract text from PDF, performing OCR when direct extraction is insufficient.

    Returns:
        DocumentText: page-oriented text content.
    """
    log.info("Extracting text from %s", cfg.input_pdf)

    if not cfg.force_ocr and PYMUPDF_AVAILABLE:
        doc = fitz.open(cfg.input_pdf)  # type: ignore[arg-type]
        page_count = len(doc)
        pages = []
        limit = cfg.max_pages or page_count
        for idx in range(min(page_count, limit)):
            page = doc.load_page(idx)
            text = page.get_text()
            pages.append(
                PageText(
                    index=idx + 1,
                    raw=_format_page(idx + 1, text),
                )
            )
        doc.close()

        combined = "\n".join(page.raw for page in pages)
        if len(combined.strip()) > 200:
            log.info("Direct text extraction successful (%d pages).", len(pages))
            return DocumentText(source=cfg.input_pdf, pages=pages)

        log.info("Direct extraction yielded minimal content; falling back to OCR.")

    if not TESSERACT_AVAILABLE:
        raise RuntimeError(
            "Tesseract OCR not available. Install pytesseract and pillow packages."
        )

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        images = _convert_to_images(cfg.input_pdf, temp_path, cfg.max_pages)
        if not images:
            raise RuntimeError("Failed to generate images from PDF for OCR.")

        pages: List[PageText] = []
        for idx, image_path in enumerate(images, start=1):
            text = _ocr_image(image_path, cfg.tesseract_lang)
            pages.append(PageText(index=idx, raw=_format_page(idx, text)))

    log.info("OCR extraction completed (%d pages).", len(pages))
    return DocumentText(source=cfg.input_pdf, pages=pages)


def _format_page(index: int, text: str) -> str:
    """Annotate text with a consistent page marker for downstream processing."""
    text = text.replace("\f", "").strip()
    header = f"--- Page {index} ---"
    if text:
        return f"{header}\n{text}"
    return header


def _convert_to_images(pdf_path: Path, target_dir: Path, max_pages: Optional[int]) -> List[Path]:
    """Convert PDF pages to image files for OCR."""
    if PDF2IMAGE_AVAILABLE:
        try:
            kwargs = {"dpi": 300}
            if max_pages is not None:
                kwargs["first_page"] = 1
                kwargs["last_page"] = max_pages
            images = convert_from_path(str(pdf_path), **kwargs)  # type: ignore[arg-type]
            outputs = []
            for idx, image in enumerate(images, start=1):
                image_path = target_dir / f"page_{idx:04d}.png"
                image.save(image_path, "PNG")
                outputs.append(image_path)
            return outputs
        except Exception as exc:  # pragma: no cover
            log.warning("pdf2image conversion failed: %s", exc)

    if not PYMUPDF_AVAILABLE:
        return []

    outputs: List[Path] = []
    doc = fitz.open(pdf_path)  # type: ignore[arg-type]
    total = len(doc)
    limit = max_pages or total
    for idx in range(min(total, limit)):
        page = doc.load_page(idx)
        matrix = fitz.Matrix(2.5, 2.5)  # type: ignore[attr-defined]
        pix = page.get_pixmap(matrix=matrix)
        image_path = target_dir / f"page_{idx + 1:04d}.png"
        pix.save(image_path)
        outputs.append(image_path)
    doc.close()
    return outputs


def _ocr_image(image_path: Path, language: str) -> str:
    """Perform OCR on a single image file."""
    if not TESSERACT_AVAILABLE:
        return ""
    image = Image.open(image_path)  # type: ignore[union-attr]
    config = r"--oem 3 --psm 6 -c preserve_interword_spaces=1"
    text = pytesseract.image_to_string(image, lang=language, config=config)  # type: ignore[union-attr]
    return text


__all__ = ["extract_pdf"]
