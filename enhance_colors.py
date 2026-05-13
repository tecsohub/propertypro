"""Enhance color visibility in PNG/WebP images by boosting saturation and contrast."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance


def enhance_color_visibility(image_path: Path, saturation_boost: float = 1.5, contrast_boost: float = 1.3) -> Image.Image:
    """
    Enhance color visibility by increasing saturation and contrast.
    Keeps white text and transparency intact.
    
    Args:
        image_path: Path to the PNG/WebP image.
        saturation_boost: Multiplier for color saturation (1.0 = no change, >1.0 = more vivid).
        contrast_boost: Multiplier for contrast (1.0 = no change, >1.0 = higher contrast).
    
    Returns:
        Enhanced PIL Image.
    """
    img = Image.open(image_path)
    
    # Ensure RGBA for transparency support
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    
    # Separate alpha channel
    alpha = img.split()[3]
    
    # Work with RGB only
    rgb_img = img.convert("RGB")
    
    # Boost saturation
    enhancer = ImageEnhance.Color(rgb_img)
    rgb_img = enhancer.enhance(saturation_boost)
    
    # Boost contrast
    enhancer = ImageEnhance.Contrast(rgb_img)
    rgb_img = enhancer.enhance(contrast_boost)
    
    # Restore alpha channel
    rgb_img.putalpha(alpha)
    
    return rgb_img


def process_images(pdf_base_name: str, saturation: float = 1.5, contrast: float = 1.3) -> list[Path]:
    """Process all page images for enhanced color visibility."""
    workspace = Path(".")
    page_num = 1
    created_files = []
    
    while True:
        png_path = workspace / f"{pdf_base_name}_page-{page_num}.png"
        webp_path = workspace / f"{pdf_base_name}_page-{page_num}.webp"
        
        if not png_path.exists():
            break
        
        # Process PNG
        png_enhanced = enhance_color_visibility(png_path, saturation, contrast)
        png_enhanced.save(png_path)
        created_files.append(png_path)
        print(f"Enhanced {png_path.name}")
        
        # Process WebP if it exists
        if webp_path.exists():
            webp_enhanced = enhance_color_visibility(webp_path, saturation, contrast)
            webp_enhanced.save(webp_path, format="WEBP", quality=100, method=6)
            created_files.append(webp_path)
            print(f"Enhanced {webp_path.name}")
        
        page_num += 1
    
    return created_files


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Enhance color visibility in PNG/WebP images by boosting saturation and contrast."
    )
    parser.add_argument("pdf_base_name", help="Base name of the PDF (without extension or page suffix).")
    parser.add_argument(
        "--saturation",
        type=float,
        default=1.5,
        help="Saturation boost multiplier (1.0=no change, >1.0=more vivid). Default: 1.5.",
    )
    parser.add_argument(
        "--contrast",
        type=float,
        default=1.3,
        help="Contrast boost multiplier (1.0=no change, >1.0=higher contrast). Default: 1.3.",
    )
    args = parser.parse_args()
    
    created_files = process_images(args.pdf_base_name, args.saturation, args.contrast)
    if created_files:
        print(f"\nEnhanced {len(created_files)} file(s) with boosted colors.")
    else:
        print(f"No images found for {args.pdf_base_name}")


if __name__ == "__main__":
    main()
