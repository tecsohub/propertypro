from __future__ import annotations

import argparse
from pathlib import Path

import fitz
from PIL import Image


def render_pdf_to_images(pdf_path: Path, dpi: int, output_dir: Path | None = None) -> list[Path]:
    """Render each PDF page to PNG and WebP without changing the page content."""
    if not pdf_path.exists():
        raise FileNotFoundError(f"File not found: {pdf_path}")

    if dpi <= 0:
        raise ValueError("DPI must be a positive integer.")

    target_dir = output_dir or pdf_path.parent
    target_dir.mkdir(parents=True, exist_ok=True)

    written_files: list[Path] = []
    scale = dpi / 72.0

    with fitz.open(pdf_path) as document:
        for page_index in range(document.page_count):
            page = document.load_page(page_index)
            pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
            image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)

            base_name = f"{pdf_path.stem}_page-{page_index + 1}"
            png_path = target_dir / f"{base_name}.png"
            webp_path = target_dir / f"{base_name}.webp"

            image.save(png_path, format="PNG")
            image.save(webp_path, format="WEBP", quality=100, method=6)

            written_files.extend([png_path, webp_path])

    return written_files


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a PDF into PNG and WebP images page by page without altering the content."
    )
    parser.add_argument("pdf_file", help="Path to the input PDF file.")
    parser.add_argument(
        "--dpi",
        type=int,
        default=1200,
        help="Render resolution in DPI. Default: 1200.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Optional directory for the generated images. Default: same folder as the PDF.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pdf_path = Path(args.pdf_file)
    output_dir = Path(args.output_dir) if args.output_dir else None

    written_files = render_pdf_to_images(pdf_path, args.dpi, output_dir=output_dir)
    for file_path in written_files:
        print(f"Created {file_path}")


if __name__ == "__main__":
    main()