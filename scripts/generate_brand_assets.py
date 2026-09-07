"""Generate the brand assets for the Folder integration.

Home Assistant brand icons are square PNGs with a transparent background,
256x256 with a 512x512 "@2x" companion. Run this to regenerate them:

    python3 scripts/generate_brand_assets.py
"""

from __future__ import annotations

import pathlib

from PIL import Image, ImageDraw

# Drawn at 4x and downscaled, which is what gives the edges their antialiasing.
CANVAS = 1024
SCALE_TO = (512, 256)

BACK = (30, 136, 185, 255)  # darker blue: the back of the folder and its tab
FRONT = (65, 189, 245, 255)  # Home Assistant blue: the front panel

OUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "custom_components/folder/brand"


def draw_folder() -> Image.Image:
    """Draw a folder glyph on a transparent square canvas."""
    image = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Tab, then the back panel it joins onto.
    draw.rounded_rectangle((52, 138, 430, 290), radius=38, fill=BACK)
    draw.rounded_rectangle((52, 224, 972, 900), radius=58, fill=BACK)
    # Front panel, leaving a band of the back visible along the top.
    draw.rounded_rectangle((52, 366, 972, 900), radius=58, fill=FRONT)

    return image


def main() -> None:
    """Write icon.png and icon@2x.png."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    folder = draw_folder()

    for size in SCALE_TO:
        name = "icon.png" if size == 256 else f"icon@{size // 256}x.png"
        folder.resize((size, size), Image.LANCZOS).save(OUT_DIR / name, "PNG")
        print(f"wrote {OUT_DIR / name} ({size}x{size})")


if __name__ == "__main__":
    main()
