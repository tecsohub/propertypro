#!/usr/bin/env python
"""Convert a PDF to per-page PNG and WebP images using PyMuPDF and Pillow.

Usage:
  python convert_pdf_to_images.py input.pdf [--dpi 300] [--outprefix out]
"""
import argparse
import os
import sys

try:
    import fitz
except Exception:
    print("PyMuPDF (fitz) is required: pip install pymupdf", file=sys.stderr)
    raise

try:
    from PIL import Image
except Exception:
    print("Pillow is required: pip install pillow", file=sys.stderr)
    raise


def main():
    p = argparse.ArgumentParser()
    p.add_argument("pdf", help="Input PDF file")
    p.add_argument("--dpi", type=int, default=3000, help="Rasterization DPI (default 300)")
    p.add_argument("--outprefix", default=None, help="Output filename prefix (default: input basename)")
    args = p.parse_args()

    pdf_path = args.pdf
    if not os.path.exists(pdf_path):
        print(f"Input PDF not found: {pdf_path}", file=sys.stderr)
        sys.exit(2)

    base = args.outprefix or os.path.splitext(os.path.basename(pdf_path))[0]

    doc = fitz.open(pdf_path)
    zoom = args.dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    out_files = []

    for i, page in enumerate(doc, start=1):
        pix = page.get_pixmap(matrix=mat, alpha=False)
        png_path = f"{base}_page-{i}.png"
        webp_path = f"{base}_page-{i}.webp"
        pix.save(png_path)

        # Convert PNG -> WebP via Pillow to control quality
        # Disable Pillow decompression bomb check for very large images (trusted local file)
        try:
            Image.MAX_IMAGE_PIXELS = None
        except Exception:
            pass
        img = Image.open(png_path)
        # WebP has a maximum dimension limit (16383). Downscale if necessary for WebP only.
        max_dim = 16383
        w, h = img.size
        if max(w, h) > max_dim:
            scale = max_dim / max(w, h)
            new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
            img_resized = img.resize(new_size, Image.LANCZOS)
            img_resized.save(webp_path, "WEBP", quality=90)
        else:
            img.save(webp_path, "WEBP", quality=90)

        out_files.append((png_path, webp_path))
        print(f"Wrote: {png_path}")
        print(f"Wrote: {webp_path}")

    print(f"Done. Generated {len(out_files)} page(s).")


if __name__ == "__main__":
    main()
