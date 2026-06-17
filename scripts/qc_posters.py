#!/usr/bin/env python3
"""Lightweight quality-control report for generated poster assets."""

from __future__ import annotations

from pathlib import Path

from PIL import Image


REPO = Path(__file__).resolve().parents[1]
POSTER_DIRS = [REPO / "images", REPO / "images" / "headered"]
EXPECTED_MIN_WIDTH = 1000
EXPECTED_MIN_HEIGHT = 1450


def poster_files(directory: Path) -> list[Path]:
    return [
        path
        for path in sorted(directory.glob("*.png"))
        if not path.name.startswith("contact-sheet")
    ]


def header_dark_rule_y(image: Image.Image) -> int | None:
    rgb = image.convert("RGB")
    width, height = rgb.size
    best_y = None
    best_dark = 0
    muted_candidate = None
    for y in range(round(height * 0.035), min(round(height * 0.18), height)):
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
    if muted_candidate is not None and (best_y is None or muted_candidate < best_y):
        return muted_candidate
    if best_dark > width * 0.35:
        return best_y
    return muted_candidate


def check_file(path: Path, *, headered: bool) -> list[str]:
    issues: list[str] = []
    image = Image.open(path)
    width, height = image.size

    if width < EXPECTED_MIN_WIDTH or height < EXPECTED_MIN_HEIGHT:
        issues.append(f"small dimensions: {width}x{height}")

    ratio = height / width
    if not 1.35 <= ratio <= 1.55:
        issues.append(f"unexpected A4-ish ratio: {width}x{height}")

    rule_y = header_dark_rule_y(image)
    if rule_y is None:
        issues.append("header rule not detected")
    elif not 0.04 <= rule_y / height <= 0.12:
        issues.append(f"header rule unusual position: {rule_y}px")

    if headered:
        # Ensure the top header has some non-background content on both sides.
        rgb = image.convert("RGB")
        sample_y = max(5, round((rule_y or height * 0.09) * 0.5))
        left_dark = 0
        right_dark = 0
        band_h = max(12, round(height * 0.045))
        for y in range(max(0, sample_y - band_h // 2), min(height, sample_y + band_h // 2)):
            for x in range(round(width * 0.02), round(width * 0.30)):
                r, g, b = rgb.getpixel((x, y))
                if r < 160 or g < 160 or b < 160:
                    left_dark += 1
            for x in range(round(width * 0.70), round(width * 0.98)):
                r, g, b = rgb.getpixel((x, y))
                if r < 160 or g < 160 or b < 160:
                    right_dark += 1
        if left_dark < 50:
            issues.append("left logo may be missing or too small")
        if right_dark < 50:
            issues.append("right logo may be missing or too small")

    return issues


def main() -> None:
    for directory in POSTER_DIRS:
        headered = directory.name == "headered"
        print(f"\n{directory.relative_to(REPO)}")
        for path in poster_files(directory):
            issues = check_file(path, headered=headered)
            status = "OK" if not issues else "; ".join(issues)
            print(f"- {path.name}: {status}")


if __name__ == "__main__":
    main()
