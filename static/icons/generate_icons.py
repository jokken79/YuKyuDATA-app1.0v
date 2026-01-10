#!/usr/bin/env python3
"""
PWA Icon Generator
Generates PNG icons from SVG source for YuKyuDATA PWA

Usage: python generate_icons.py

Requirements:
    pip install cairosvg pillow

If cairosvg is not available, you can use online tools like:
- https://cloudconvert.com/svg-to-png
- https://svgtopng.com/
"""

import os
from pathlib import Path

# Icon sizes needed for PWA
ICON_SIZES = [72, 96, 128, 144, 152, 192, 384, 512]
MASKABLE_SIZES = [192, 512]

def generate_placeholder_svg(size: int, maskable: bool = False) -> str:
    """Generate a simple placeholder SVG icon."""
    padding = size * 0.1 if maskable else 0
    inner_size = size - (padding * 2)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">
  <defs>
    <linearGradient id="bg-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#0f172a"/>
      <stop offset="100%" style="stop-color:#020617"/>
    </linearGradient>
    <linearGradient id="accent-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#38bdf8"/>
      <stop offset="100%" style="stop-color:#0ea5e9"/>
    </linearGradient>
  </defs>

  <!-- Background -->
  <rect width="{size}" height="{size}" rx="{size * 0.15}" fill="url(#bg-grad)"/>

  <!-- Calendar icon simplified -->
  <g transform="translate({size * 0.2}, {size * 0.22})">
    <!-- Calendar body -->
    <rect x="0" y="{inner_size * 0.12}"
          width="{inner_size * 0.6}" height="{inner_size * 0.5}"
          rx="{inner_size * 0.05}"
          fill="rgba(30,41,59,0.9)"
          stroke="rgba(255,255,255,0.1)"
          stroke-width="{max(1, size * 0.005)}"/>

    <!-- Calendar top bar -->
    <rect x="0" y="{inner_size * 0.12}"
          width="{inner_size * 0.6}" height="{inner_size * 0.12}"
          rx="{inner_size * 0.05}"
          fill="url(#accent-grad)"/>

    <!-- Calendar hooks -->
    <rect x="{inner_size * 0.12}" y="{inner_size * 0.05}"
          width="{inner_size * 0.04}" height="{inner_size * 0.12}"
          rx="{inner_size * 0.02}" fill="#94a3b8"/>
    <rect x="{inner_size * 0.44}" y="{inner_size * 0.05}"
          width="{inner_size * 0.04}" height="{inner_size * 0.12}"
          rx="{inner_size * 0.02}" fill="#94a3b8"/>

    <!-- Check mark -->
    <path d="M{inner_size * 0.12} {inner_size * 0.38}
             L{inner_size * 0.22} {inner_size * 0.48}
             L{inner_size * 0.42} {inner_size * 0.28}"
          stroke="#34d399"
          stroke-width="{max(2, size * 0.025)}"
          stroke-linecap="round"
          stroke-linejoin="round"
          fill="none"/>

    <!-- YK text -->
    <text x="{inner_size * 0.3}" y="{inner_size * 0.2}"
          text-anchor="middle"
          font-family="Arial, sans-serif"
          font-size="{inner_size * 0.08}"
          font-weight="bold"
          fill="white">YK</text>
  </g>
</svg>'''


def generate_icons():
    """Generate all PWA icons as SVG (can be converted to PNG)."""
    script_dir = Path(__file__).parent

    print("Generating PWA icons...")

    # Generate regular icons
    for size in ICON_SIZES:
        svg_content = generate_placeholder_svg(size, maskable=False)
        output_path = script_dir / f"icon-{size}.svg"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        print(f"  Created: icon-{size}.svg")

    # Generate maskable icons (with safe zone padding)
    for size in MASKABLE_SIZES:
        svg_content = generate_placeholder_svg(size, maskable=True)
        output_path = script_dir / f"icon-maskable-{size}.svg"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        print(f"  Created: icon-maskable-{size}.svg")

    print("\nSVG icons generated successfully!")
    print("\nTo convert to PNG, you can use:")
    print("  - cairosvg: pip install cairosvg")
    print("  - Online: https://cloudconvert.com/svg-to-png")
    print("  - Inkscape: inkscape icon-192.svg --export-png=icon-192.png")

    # Try to convert to PNG using cairosvg if available
    try:
        import cairosvg
        print("\nConverting SVGs to PNGs with cairosvg...")

        for size in ICON_SIZES:
            svg_path = script_dir / f"icon-{size}.svg"
            png_path = script_dir / f"icon-{size}.png"
            cairosvg.svg2png(url=str(svg_path), write_to=str(png_path),
                           output_width=size, output_height=size)
            print(f"  Converted: icon-{size}.png")

        for size in MASKABLE_SIZES:
            svg_path = script_dir / f"icon-maskable-{size}.svg"
            png_path = script_dir / f"icon-maskable-{size}.png"
            cairosvg.svg2png(url=str(svg_path), write_to=str(png_path),
                           output_width=size, output_height=size)
            print(f"  Converted: icon-maskable-{size}.png")

        print("\nPNG icons generated successfully!")

    except ImportError:
        print("\ncairosvg not available. Install with: pip install cairosvg")
        print("SVG files can still be used directly or converted manually.")


if __name__ == "__main__":
    generate_icons()
