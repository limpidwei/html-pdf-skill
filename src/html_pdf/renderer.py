"""Playwright-based HTML renderer and screenshot capture for html-pdf skill."""

from pathlib import Path
from typing import List

from playwright.sync_api import sync_playwright


# Common slide/page selectors in order of preference
SLIDE_SELECTORS = [
    ".reveal .slides > section",
    ".reveal .slides > section > section",
    ".slides > section",
    ".slide",
    "[class*='slide']",
    "[class*='page']",
]


def detect_slides(page) -> List:
    """Detect slide elements; fall back to full page body."""
    for selector in SLIDE_SELECTORS:
        elements = page.query_selector_all(selector)
        if len(elements) > 1:
            return elements
    # If no multi-slide structure, treat whole page as one slide
    return [page.locator("body")]


def render_at_scale(
    html_path: Path,
    out_dir: Path,
    scale: int,
    wait_time: int = 3000,
) -> List[Path]:
    """Render an HTML file and capture screenshots at the given device scale."""
    out_dir = out_dir.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    screenshots: List[Path] = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        # Viewport large enough to accommodate 1280x720 deck even at scale 1
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=scale,
        )
        page = context.new_page()
        page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
        page.wait_for_timeout(wait_time)

        # Remove deck transform scaling and hide UI overlays
        page.evaluate(
            """
            () => {
                const deck = document.getElementById('deck');
                if (deck) deck.style.transform = 'none';
                const nav = document.getElementById('nav');
                if (nav) nav.style.display = 'none';
                const hint = document.querySelector('.hint');
                if (hint) hint.style.display = 'none';
                document.body.style.overflow = 'visible';
            }
            """
        )
        page.wait_for_timeout(500)

        slides = detect_slides(page)
        total = len(slides)

        for i, slide in enumerate(slides):
            screenshot_path = out_dir / f"page_{i + 1:03d}_{scale}x.png"

            # If we detected real slide elements, show only one at a time
            if total > 1:
                page.evaluate(
                    f"""
                    () => {{
                        const slides = document.querySelectorAll('.slide, .reveal .slides > section, .slides > section, [class*="slide"], [class*="page"]');
                        slides.forEach((s, idx) => {{
                            s.style.display = idx === {i} ? (s.classList.contains('slide') ? 'flex' : 'block') : 'none';
                            if (idx === {i}) s.classList.add('on');
                        }});
                    }}
                    """
                )
                page.wait_for_timeout(300)

            # Screenshot the deck if it exists, otherwise the slide/body
            deck = page.locator("#deck")
            try:
                if deck.count() > 0 and deck.is_visible():
                    deck.screenshot(path=str(screenshot_path))
                else:
                    slide.screenshot(path=str(screenshot_path))
            except Exception as exc:
                print(f"WARNING: screenshot failed for page {i + 1}: {exc}")
                # Fallback to full page
                page.screenshot(path=str(screenshot_path))

            screenshots.append(screenshot_path)
            print(f"  Captured page {i + 1}/{total} at {scale}x ({screenshot_path.name})")

        browser.close()

    return screenshots


def render_pages(
    html_path: Path,
    out_dir: Path,
    hd: bool = False,
) -> tuple[List[Path], List[Path]]:
    """Render standard (1x) and optionally HD (2x) screenshots."""
    standard = render_at_scale(html_path, out_dir / "standard", scale=1)
    high_def = render_at_scale(html_path, out_dir / "hd", scale=2) if hd else []
    return standard, high_def
