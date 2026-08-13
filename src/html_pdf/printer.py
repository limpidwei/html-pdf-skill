"""Chromium print-to-PDF backend for html-pdf skill.

Produces a real text-based (vector) PDF with selectable text, unlike the
screenshot/img2pdf raster pipeline. Best for articles and text documents;
slide decks should keep using the raster renderer (print mode can truncate
fixed-layout slides).
"""

from pathlib import Path

from playwright.sync_api import sync_playwright

DEFAULT_MARGINS = {"top": "15mm", "bottom": "15mm", "left": "12mm", "right": "12mm"}


def print_pdf(
    html_path: Path,
    out_path: Path,
    wait_time: int = 3000,
    page_format: str = "A4",
    landscape: bool = False,
) -> Path:
    """Render an HTML file to a text-based PDF via Chromium's print engine."""
    out_path = out_path.expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        # networkidle can hang on pages with websockets/long-polling; fall back to load
        try:
            page.goto(html_path.resolve().as_uri(), wait_until="networkidle", timeout=30000)
        except Exception:
            print("WARNING: networkidle timed out, falling back to load event")
            page.goto(html_path.resolve().as_uri(), wait_until="load", timeout=60000)
        page.wait_for_timeout(wait_time)

        # Use screen media so the PDF matches what the browser shows
        # (Chromium print-to-PDF otherwise applies print stylesheets).
        page.emulate_media(media="screen")
        page.pdf(
            path=str(out_path),
            format=page_format,
            landscape=landscape,
            print_background=True,
            margin=DEFAULT_MARGINS,
        )
        browser.close()

    print(f"PDF created (print mode, selectable text): {out_path}")
    return out_path
