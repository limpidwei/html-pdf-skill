"""html-pdf: Convert HTML files or URLs to PDF with Playwright."""

__version__ = "1.0.0"

from .check_deps import check_all, check_python
from .fetcher import prepare_input
from .install_deps import ensure_dependencies
from .pdf_builder import build_pdf
from .renderer import render_pages

__all__ = [
    "check_all",
    "check_python",
    "ensure_dependencies",
    "prepare_input",
    "render_pages",
    "build_pdf",
]
