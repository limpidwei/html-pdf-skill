"""CLI entry point for html-pdf skill."""

import argparse
import sys
import time
from pathlib import Path

from .check_deps import check_all, check_python, print_status
from .fetcher import is_url, prepare_input
from .install_deps import ensure_dependencies
from .pdf_builder import build_pdf
from .renderer import render_pages


def default_output_dir(input_value: str) -> Path:
    """Default output: input file's directory for local files, ~/html-pdf-output/<ts>/ for URLs."""
    if is_url(input_value):
        stamp = time.strftime("%Y%m%d-%H%M%S")
        return Path.home() / "html-pdf-output" / stamp
    return Path(input_value).expanduser().resolve().parent


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert HTML files or URLs to PDF using Playwright screenshots."
    )
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Local HTML file path or http(s) URL",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        default=None,
        help="Directory for output PDFs and intermediate files "
        "(default: input file's directory, or ~/html-pdf-output/<timestamp>/ for URLs)",
    )
    parser.add_argument(
        "--hd",
        action="store_true",
        help="Also generate a 2x high-resolution PDF",
    )
    parser.add_argument(
        "--skip-deps",
        action="store_true",
        help="Skip dependency checks and installation",
    )
    parser.add_argument(
        "--wait",
        type=int,
        default=3000,
        help="Milliseconds to wait after networkidle before screenshots (default: 3000)",
    )

    args = parser.parse_args(argv)

    try:
        check_python()
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        return 1

    if not args.skip_deps:
        print("Checking dependencies...")
        status = check_all()
        print_status(status)

        if not all(status.values()):
            print("Installing missing dependencies...")
            ensure_dependencies()
            print("Dependencies ready.")

    out_dir = (
        Path(args.output_dir).expanduser().resolve()
        if args.output_dir
        else default_output_dir(args.input)
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        print(f"Preparing input: {args.input}")
        html_path = prepare_input(args.input, out_dir / "work")
        print(f"Localized HTML: {html_path}")

        print("Rendering pages...")
        std_pngs, hd_pngs = render_pages(
            html_path,
            out_dir / "screenshots",
            hd=args.hd,
            wait_time=args.wait,
        )

        std_pdf = out_dir / "output.pdf"
        build_pdf(std_pngs, std_pdf)

        if args.hd:
            hd_pdf = out_dir / "output-hd.pdf"
            build_pdf(hd_pngs, hd_pdf)

        # Validate outputs
        if not std_pdf.exists() or std_pdf.stat().st_size == 0:
            raise RuntimeError("Standard PDF was not created successfully")

        print("\nDone.")
        print(f"  Standard PDF: {std_pdf}")
        if args.hd:
            print(f"  HD PDF:       {hd_pdf}")

        return 0

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
