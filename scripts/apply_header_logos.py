#!/usr/bin/env python3
"""Overlay fixed header logos onto generated poster PNGs."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

from PIL import Image


REPO = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = REPO / "images"
DEFAULT_OUTPUT = REPO / "images" / "headered"
POPUP_LOGO = REPO / "assets" / "logos" / "pop-up-psychology.svg"
HULL_LOGO = REPO / "assets" / "logos" / "university-of-hull.svg"


def render_svg(svg_path: Path, *, height: int) -> Image.Image:
    with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
        subprocess.run(
            ["rsvg-convert", "-h", str(height), "-o", tmp.name, str(svg_path)],
            check=True,
        )
        return Image.open(tmp.name).convert("RGBA")


def logo_height_for_poster(poster_height: int, fraction: float) -> int:
    return max(36, round(poster_height * fraction))


def overlay_header(poster_path: Path, output_path: Path) -> None:
    poster = Image.open(poster_path).convert("RGBA")
    width, height = poster.size

    margin_x = round(width * 0.035)
    header_top = round(height * 0.028)
    popup_h = logo_height_for_poster(height, 0.052)
    hull_h = logo_height_for_poster(height, 0.044)

    popup = render_svg(POPUP_LOGO, height=popup_h)
    hull = render_svg(HULL_LOGO, height=hull_h)

    popup_y = header_top
    hull_y = header_top + max(0, (popup.height - hull.height) // 2)
    hull_x = width - margin_x - hull.width

    poster.alpha_composite(popup, (margin_x, popup_y))
    poster.alpha_composite(hull, (hull_x, hull_y))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    poster.convert("RGB").save(output_path, quality=95)


def iter_posters(input_dir: Path) -> list[Path]:
    return [
        path
        for path in sorted(input_dir.glob("*.png"))
        if path.name != "contact-sheet.png" and path.parent.name != "headered"
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    for source in iter_posters(args.input_dir):
        target = args.output_dir / source.name
        overlay_header(source, target)
        print(target)


if __name__ == "__main__":
    main()
