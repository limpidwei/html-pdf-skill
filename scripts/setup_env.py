#!/usr/bin/env python3
"""One-shot environment setup for html-pdf skill."""

import subprocess
import sys
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parent.parent
    src_dir = project_root / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

    try:
        from html_pdf.check_deps import check_python
        check_python()
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        return 1

    try:
        from html_pdf.check_deps import check_all, print_status
        from html_pdf.install_deps import ensure_dependencies

        print("Checking current environment...")
        status = check_all()
        print_status(status)

        if not all(status.values()):
            print("\nInstalling missing dependencies...")
            ensure_dependencies()
            print("\nRechecking environment...")
            print_status(check_all())
        else:
            print("\nAll dependencies are already satisfied.")

        # Install the local package in editable mode so CLI is on PATH
        project_root = Path(__file__).resolve().parent.parent
        print(f"\nInstalling html_pdf package from {project_root} ...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--upgrade", "-e", str(project_root)],
            stdout=sys.stdout,
            stderr=sys.stderr,
        )

        print("\nhtml-pdf environment is ready.")
        print("Usage: python -m html_pdf --input <file-or-url> --output-dir <dir> [--hd]")
        return 0

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
