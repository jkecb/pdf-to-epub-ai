from __future__ import annotations

"""
I/O helpers for reading and writing intermediate artefacts.
"""

from pathlib import Path
import re

from .logging import get_logger
from .pages import DocumentText, PageText

log = get_logger(__name__)

PAGE_MARKER_PATTERN = re.compile(r"^--- Page (\d+) ---$")


def write_document(
    doc: DocumentText,
    path: Path,
    *,
    include_page_markers: bool = False,
) -> None:
    """Persist document pages to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        for page in doc.pages:
            if include_page_markers:
                handle.write(f"--- Page {page.index} ---\n")
            content = page.cleaned if page.cleaned is not None else strip_page_marker(page.raw)
            handle.write(content.rstrip())
            handle.write("\n\n")
    log.debug("Wrote %s", path)


def read_document(path: Path) -> DocumentText:
    """Load a text file with page markers into a DocumentText."""
    pages: list[PageText] = []
    current_lines: list[str] = []
    current_index = 1

    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            match = PAGE_MARKER_PATTERN.match(line.strip())
            if match:
                if current_lines:
                    pages.append(
                        PageText(index=current_index, raw="\n".join(current_lines).strip())
                    )
                    current_lines = []
                current_index = int(match.group(1))
                continue
            current_lines.append(line.rstrip("\n"))

    if current_lines:
        pages.append(
            PageText(index=current_index, raw="\n".join(current_lines).strip())
        )

    return DocumentText(source=path, pages=pages)


def strip_page_marker(text: str) -> str:
    lines = text.splitlines()
    if lines and lines[0].startswith("--- Page"):
        return "\n".join(lines[1:])
    return text


__all__ = ["write_document", "read_document", "strip_page_marker"]
