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


def find_header_rule_y(poster: Image.Image) -> int:
    """Find the dark horizontal rule that closes the generated blank header."""
    rgb = poster.convert("RGB")
    width, height = rgb.size
    search_start = round(height * 0.035)
    search_end = min(round(height * 0.18), height)

    best_y = round(height * 0.09)
    best_dark = 0
    muted_candidate: int | None = None
    for y in range(search_start, search_end):
        dark = 0
        muted = 0
        for x in range(width):
            r, g, b = rgb.getpixel((x, y))
            if r < 90 and g < 90 and b < 90:
                dark += 1
            if (r + g + b) / 3 < 230:
                muted += 1
        if dark > best_dark:
            best_y = y
            best_dark = dark
        if muted_candidate is None and muted > width * 0.35:
            muted_candidate = y

    if muted_candidate is not None and muted_candidate < best_y:
        return muted_candidate
    if best_dark < width * 0.35:
        return round(height * 0.095)
    return best_y


def fit_logo(logo: Image.Image, *, max_width: int, max_height: int) -> Image.Image:
    scale = min(max_width / logo.width, max_height / logo.height)
    target = (max(1, round(logo.width * scale)), max(1, round(logo.height * scale)))
    return logo.resize(target, Image.Resampling.LANCZOS)


def overlay_header(poster_path: Path, output_path: Path) -> None:
    poster = Image.open(poster_path).convert("RGBA")
    width, height = poster.size

    header_rule_y = find_header_rule_y(poster)
    margin_x = round(width * 0.035)
    header_top = max(10, round(header_rule_y * 0.18))
    available_h = max(36, header_rule_y - header_top - round(height * 0.012))
    max_logo_h = round(available_h * 0.72)

    popup_raw = render_svg(POPUP_LOGO, height=420)
    hull_raw = render_svg(HULL_LOGO, height=420)
    popup = fit_logo(popup_raw, max_width=round(width * 0.31), max_height=max_logo_h)
    hull = fit_logo(hull_raw, max_width=round(width * 0.25), max_height=max_logo_h)

    popup_y = header_top + max(0, (available_h - popup.height) // 2)
    hull_y = header_top + max(0, (available_h - hull.height) // 2)
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
