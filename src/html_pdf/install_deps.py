"""Dependency installer for html-pdf skill."""

import platform
import subprocess
import sys
from typing import List

from .check_deps import has_command


def pip_install(*packages: str) -> None:
    """Install or upgrade Python packages with pip."""
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "--upgrade", *packages],
        stdout=sys.stdout,
        stderr=sys.stderr,
    )


def install_playwright_browsers() -> None:
    """Install Chromium browser binaries for Playwright."""
    subprocess.check_call(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        stdout=sys.stdout,
        stderr=sys.stderr,
    )


def manual_install_hint(package: str) -> str:
    """Return platform-specific manual install instructions."""
    system = platform.system()
    if system == "Windows":
        return (
            f"Could not auto-install {package}. Please install manually:\n"
            f"  - With winget: winget install {package}\n"
            f"  - With Chocolatey: choco install {package} -y\n"
            f"  - Or download from the official {package} website."
        )
    elif system == "Darwin":
        return f"Could not auto-install {package}. Run: brew install {package}"
    else:
        return (
            f"Could not auto-install {package}. Run one of:\n"
            f"  sudo apt-get install -y {package}\n"
            f"  sudo dnf install -y {package}\n"
            f"  sudo pacman -S {package}"
        )


def install_system_command(cmd: str) -> None:
    """Try to install a system command-line tool; raise on failure."""
    system = platform.system()
    if system == "Windows":
        if has_command("winget"):
            subprocess.check_call(["winget", "install", cmd])
            return
        if has_command("choco"):
            subprocess.check_call(["choco", "install", cmd, "-y"])
            return
    elif system == "Darwin":
        if has_command("brew"):
            subprocess.check_call(["brew", "install", cmd])
            return
    else:
        if has_command("apt-get"):
            subprocess.check_call(["sudo", "apt-get", "update"])
            subprocess.check_call(["sudo", "apt-get", "install", "-y", cmd])
            return
        if has_command("dnf"):
            subprocess.check_call(["sudo", "dnf", "install", "-y", cmd])
            return
        if has_command("pacman"):
            subprocess.check_call(["sudo", "pacman", "-S", "--noconfirm", cmd])
            return

    raise RuntimeError(manual_install_hint(cmd))


def ensure_dependencies(packages: List[str] = None) -> None:
    """Install missing Python packages and Chromium browser."""
    from .check_deps import check_all

    if packages is None:
        packages = ["playwright", "img2pdf", "requests", "beautifulsoup4"]

    status = check_all()

    missing_python_packages = [pkg for pkg in packages if not status.get(pkg, False)]
    if missing_python_packages:
        print(f"Installing Python packages: {', '.join(missing_python_packages)}")
        pip_install(*missing_python_packages)

    if not status["chromium"]:
        print("Installing Playwright Chromium browser...")
        install_playwright_browsers()

    for cmd in ("curl", "git"):
        if not status[cmd]:
            print(f"Attempting to install system command: {cmd}")
            try:
                install_system_command(cmd)
            except Exception as exc:
                print(f"WARNING: {exc}")
