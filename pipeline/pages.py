from __future__ import annotations

"""
Utilities for representing PDFs as page-oriented text collections.
"""

from dataclasses import dataclass
from typing import List
from pathlib import Path


@dataclass
class PageText:
    """In-memory representation of a single page's textual content."""

    index: int  # 1-based page index
    raw: str
    cleaned: str | None = None

    def header_candidate(self) -> str:
        """Return the probable header line to aid detection."""
        lines = [line.strip() for line in self.raw.splitlines() if line.strip()]
        return lines[0] if lines else ""

    def footer_candidate(self) -> str:
        """Return the probable footer line to aid detection."""
        lines = [line.strip() for line in self.raw.splitlines() if line.strip()]
        return lines[-1] if lines else ""


@dataclass
class DocumentText:
    """Wrapper for the entire document's page collection."""

    source: Path
    pages: List[PageText]

    def combined_raw(self) -> str:
        """Join raw page content with markers."""
        return "\n".join(page.raw for page in self.pages)

    def combined_clean(self, marker: str = "\n\n") -> str:
        """Join cleaned page content with separation markers."""
        payload = []
        for page in self.pages:
            content = page.cleaned if page.cleaned is not None else page.raw
            payload.append(content.strip())
        return marker.join(payload).strip()


__all__ = ["PageText", "DocumentText"]
