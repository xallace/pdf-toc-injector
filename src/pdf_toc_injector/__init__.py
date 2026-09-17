"""
pdf-toc-injector: Heuristic TOC Discovery & Bookmark Injection Engine.
"""

from .core import (
    inject_toc,
    find_toc_pages,
    parse_toc_entries,
    detect_page_offset,
    build_pdf_toc,
)

__version__ = "0.1.0"
__all__ = [
    "inject_toc",
    "find_toc_pages",
    "parse_toc_entries",
    "detect_page_offset",
    "build_pdf_toc",
]
