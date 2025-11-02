from __future__ import annotations

"""
EPUB generation from cleaned document text.
"""

import html
from pathlib import Path

from ebooklib import epub

from .config import PipelineConfig
from .logging import get_logger
from .pages import DocumentText
from .storage import strip_page_marker

log = get_logger(__name__)


def write_pagewise_epub(doc: DocumentText, cfg: PipelineConfig) -> None:
    """Write an EPUB preserving original page boundaries."""
    book = epub.EpubBook()

    title = doc.source.stem.replace("_", " ")
    book.set_identifier(title.lower())
    book.set_title(title)
    book.add_author("Unknown Author")

    spine = ["nav"]
    toc_entries = []

    for page in doc.pages:
        content = page.cleaned or page.raw
        title = f"Page {page.index}"
        file_name = f"page_{page.index:04d}.xhtml"
        chapter_html = _page_to_html(title, content)
        chapter = epub.EpubHtml(title=title, file_name=file_name, content=chapter_html)
        book.add_item(chapter)
        toc_entries.append(chapter)
        spine.append(chapter)

    book.toc = tuple(toc_entries)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    book.add_item(
        epub.EpubItem(
            uid="style_nav",
            file_name="style/nav.css",
            media_type="text/css",
            content=_default_css(),
        )
    )

    book.spine = spine

    epub.write_epub(str(cfg.final_epub), book)
    log.info("EPUB written to %s", cfg.final_epub)


def _page_to_html(title: str, content: str) -> str:
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
    html_paragraphs = [
        f"<p>{html.escape(paragraph).replace('\\n', '<br/>')}</p>"
        for paragraph in paragraphs
    ]
    body = "\n".join(html_paragraphs)
    return f"<h2>{html.escape(title)}</h2>\n{body}"


def _default_css() -> str:
    return """
    body { font-family: Georgia, 'Times New Roman', serif; line-height: 1.4; }
    h2 { text-align: center; margin-top: 1.5em; margin-bottom: 1em; }
    p { text-indent: 1.2em; margin: 0 0 1em 0; }
    """


def write_plain_text(doc: DocumentText, cfg: PipelineConfig) -> None:
    """Save cleaned text with page markers for inspection."""
    with open(cfg.final_txt, "w", encoding="utf-8") as handle:
        for page in doc.pages:
            handle.write(f"--- Page {page.index} ---\n")
            content = page.cleaned if page.cleaned else strip_page_marker(page.raw)
            handle.write(content.strip())
            handle.write("\n\n")
    log.info("Clean text written to %s", cfg.final_txt)


__all__ = ["write_pagewise_epub", "write_plain_text"]
