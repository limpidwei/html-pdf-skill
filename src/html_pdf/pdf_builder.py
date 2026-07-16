"""PDF builder for html-pdf skill."""

from pathlib import Path
from typing import List

import img2pdf


def build_pdf(images: List[Path], output_path: Path) -> None:
    """Combine a list of image files into a single PDF."""
    if not images:
        raise ValueError("No images provided for PDF generation")

    output_path = output_path.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "wb") as f:
        f.write(img2pdf.convert([str(img) for img in images]))

    print(f"PDF created: {output_path}")
