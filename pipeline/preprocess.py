from __future__ import annotations

"""
Text preprocessing pipeline that normalises OCR output while maintaining
page-oriented structure.
"""

import re
from collections import Counter
from typing import Iterable

from .logging import get_logger
from .pages import DocumentText, PageText

log = get_logger(__name__)


def clean_document(doc: DocumentText) -> DocumentText:
    """
    Clean OCR text while preserving page boundaries.

    Returns a new DocumentText with the `cleaned` attribute populated.
    """
    log.info("Cleaning OCR text (%d pages).", len(doc.pages))

    header_lines = Counter(
        _normalise_line(page.header_candidate()) for page in doc.pages if page.raw
    )
    footer_lines = Counter(
        _normalise_line(page.footer_candidate()) for page in doc.pages if page.raw
    )

    headers_to_remove = {
        line for line, count in header_lines.items() if count >= max(3, len(doc.pages) // 4)
    }
    footers_to_remove = {
        line for line, count in footer_lines.items() if count >= max(3, len(doc.pages) // 4)
    }

    cleaned_pages = []
    for page in doc.pages:
        cleaned_text = _clean_page(
            page,
            headers_to_remove=headers_to_remove,
            footers_to_remove=footers_to_remove,
        )
        cleaned_pages.append(
            PageText(index=page.index, raw=page.raw, cleaned=cleaned_text)
        )

    return DocumentText(source=doc.source, pages=cleaned_pages)


def _clean_page(
    page: PageText,
    *,
    headers_to_remove: set[str],
    footers_to_remove: set[str],
) -> str:
    lines = page.raw.splitlines()

    filtered: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            filtered.append("")
            continue
        if stripped.startswith("--- Page"):
            continue

        normalised = _normalise_line(stripped)

        if normalised in headers_to_remove or normalised in footers_to_remove:
            continue

        if _is_page_counter(stripped):
            continue

        filtered.append(stripped)

    normalised_lines = _prepare_lines(filtered)
    merged = _merge_lines(normalised_lines)
    merged = _fix_common_ocr_glitches(merged)
    merged = _shrink_whitespace(merged)
    return merged.strip()


def _prepare_lines(lines: list[str]) -> list[str]:
    """Remove soft hyphen and newline artifacts before merging lines."""
    blob = "\n".join(lines)
    blob = re.sub(r"(\w)[\u00ad-]\s*\n\s*(\w)", r"\1\2", blob)
    blob = re.sub(r"(\w)\u00ad(\w)", r"\1\2", blob)
    return blob.split("\n")


def _normalise_line(line: str) -> str:
    """Normalise a line for comparison when detecting headers/footers."""
    return re.sub(r"\s+", " ", line).strip().lower()


def _is_page_counter(line: str) -> bool:
    """Return True if the line looks like a page number."""
    if re.fullmatch(r"\d{1,4}", line):
        return True
    if re.fullmatch(r"[ivxlcdm]+", line.lower()):
        return True
    return False


def _merge_lines(lines: Iterable[str]) -> str:
    """
    Merge fragmented lines into paragraphs while respecting intentional breaks.
    """
    paragraphs: list[str] = []
    buffer: list[str] = []

    def flush_buffer() -> None:
        if buffer:
            paragraphs.append(" ".join(buffer).strip())
            buffer.clear()

    for raw_line in lines:
        line = raw_line.rstrip()
        if not line:
            flush_buffer()
            continue

        if _looks_like_list_item(line):
            flush_buffer()
            paragraphs.append(line)
            continue

        if buffer and _should_break(buffer[-1], line):
            flush_buffer()

        if buffer:
            if _should_join(buffer[-1], line):
                buffer[-1] = _join_fragments(buffer[-1], line)
            else:
                buffer.append(line)
        else:
            buffer.append(line)

    flush_buffer()
    return "\n\n".join(paragraphs)


def _looks_like_list_item(line: str) -> bool:
    return bool(re.match(r"^([-*•]|(\d+|[a-zA-Z])\.)\s+", line))


def _should_break(prev_line: str, current_line: str) -> bool:
    """Determine whether the current line should start a new paragraph."""
    if prev_line.endswith((":", "?", "!")):
        return True
    if re.match(r"^[A-Z][A-Z\s]{3,}$", current_line):
        return True
    if _looks_like_section_heading(current_line):
        return True
    return False


def _should_join(prev_line: str, current_line: str) -> bool:
    """
    Decide if the new line should be appended to the previous fragment with a
    space rather than creating a new sentence fragment.
    """
    if prev_line.endswith("-"):
        return True
    if prev_line.endswith((",", "—", "–")):
        return True
    if not re.search(r"[.!?](['\"])?$", prev_line):
        if not _looks_like_section_heading(current_line) and not current_line.startswith(("\"", "“")):
            return True
    return False


def _join_fragments(prev_line: str, current_line: str) -> str:
    if prev_line.endswith("-"):
        return prev_line[:-1] + current_line.lstrip()
    return prev_line + " " + current_line.lstrip()


def _looks_like_section_heading(line: str) -> bool:
    return bool(
        re.match(
            r"^(chapter|part|section|book|foreword|preface|appendix|introduction|conclusion)\b",
            line.lower(),
        )
    )


def _fix_common_ocr_glitches(text: str) -> str:
    """Apply conservative OCR corrections."""
    replacements = {
        "ﬁ": "fi",
        "ﬂ": "fl",
        "—": "—",  # kept for completeness
        "–": "–",
        "\u00ad": "",  # soft hyphen
        "\u2011": "-",  # non-breaking hyphen
        "\u00a0": " ",  # non-breaking space
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    text = re.sub(r"(\w)-\s+(\w)", r"\1\2", text)
    text = re.sub(r"(?<=\w)-\n(?=\w)", "", text)
    text = re.sub(r"\s+([,.;:])", r"\1", text)
    text = re.sub(r"([,;])([^\s])", r"\1 \2", text)
    text = re.sub(r"([.!?])([A-Z])", r"\1 \2", text)
    return text


def _shrink_whitespace(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


__all__ = ["clean_document"]
