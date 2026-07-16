"""Environment dependency checks for html-pdf skill."""

import shutil
import sys
from typing import Dict

MIN_PYTHON = (3, 10)


def check_python() -> None:
    """Ensure Python version meets minimum requirement."""
    if sys.version_info < MIN_PYTHON:
        raise RuntimeError(
            f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ is required; "
            f"found {sys.version_info.major}.{sys.version_info.minor}"
        )


def has_command(cmd: str) -> bool:
    """Check if a command-line tool is available."""
    return shutil.which(cmd) is not None


def has_python_package(name: str) -> bool:
    """Check if a Python package can be imported."""
    try:
        __import__(name)
        return True
    except ImportError:
        return False


def has_chromium_browser() -> bool:
    """Check if Playwright Chromium browser is installed by trying to launch it."""
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch()
            browser.close()
            return True
    except Exception:
        return False


def check_all() -> Dict[str, bool]:
    """Return a dict of all dependency statuses."""
    return {
        "python": sys.version_info >= MIN_PYTHON,
        "playwright": has_python_package("playwright"),
        "chromium": has_chromium_browser(),
        "img2pdf": has_python_package("img2pdf"),
        "requests": has_python_package("requests"),
        "bs4": has_python_package("bs4"),
        "curl": has_command("curl"),
        "git": has_command("git"),
    }


def print_status(status: Dict[str, bool]) -> None:
    """Pretty-print dependency status."""
    for name, ok in status.items():
        symbol = "[OK]" if ok else "[MISSING]"
        print(f"  {symbol} {name}")
