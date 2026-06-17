#!/usr/bin/env python3
"""Build contact sheets for the canonical poster set."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


REPO = Path(__file__).resolve().parents[1]
IMAGES = REPO / "images"
HEADERED = IMAGES / "headered"

CANONICAL_POSTERS = [
    "buzz-wire-task.png",
    "corsi-block-tapping-task.png",
    "hollow-face-illusion.png",
    "hybrid-image-illusion.png",
    "mcgurk-effect.png",
    "reaction-catch-challenge.png",
    "rubber-hand-illusion.png",
    "semantic-priming.png",
    "spiral-after-effect.png",
    "stroop-effect.png",
    "tower-of-hanoi.png",
    "train-track-illusion.png",
    "upside-down-goggles.png",
]


def font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = "/usr/share/fonts/TTF/DejaVuSansCondensed-Bold.ttf" if bold else "/usr/share/fonts/TTF/DejaVuSansCondensed.ttf"
    return ImageFont.truetype(path, size)


def title_for(filename: str) -> str:
    return filename.removesuffix(".png").replace("-", " ").title()


def build_sheet(source_dir: Path, output: Path) -> None:
    thumb_w = 210
    thumb_h = 315
    label_h = 34
    gap = 22
    margin = 28
    cols = 4
    rows = (len(CANONICAL_POSTERS) + cols - 1) // cols

    sheet_w = margin * 2 + cols * thumb_w + (cols - 1) * gap
    sheet_h = margin * 2 + rows * (thumb_h + label_h) + (rows - 1) * gap
    sheet = Image.new("RGB", (sheet_w, sheet_h), (250, 247, 239))
    draw = ImageDraw.Draw(sheet)
    label_font = font(15, bold=True)

    for index, filename in enumerate(CANONICAL_POSTERS):
        path = source_dir / filename
        if not path.exists():
            raise FileNotFoundError(path)

        row, col = divmod(index, cols)
        x = margin + col * (thumb_w + gap)
        y = margin + row * (thumb_h + label_h + gap)

        poster = Image.open(path).convert("RGB")
        poster.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        px = x + (thumb_w - poster.width) // 2
        py = y
        sheet.paste(poster, (px, py))
        draw.rectangle((px, py, px + poster.width - 1, py + poster.height - 1), outline=(45, 45, 45), width=1)

        label = title_for(filename)
        box = draw.textbbox((0, 0), label, font=label_font)
        tx = x + (thumb_w - (box[2] - box[0])) // 2
        draw.text((tx, y + thumb_h + 9), label, font=label_font, fill=(31, 24, 36))

    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, quality=95)
    print(output)


def main() -> None:
    build_sheet(IMAGES, IMAGES / "contact-sheet.png")
    build_sheet(HEADERED, HEADERED / "contact-sheet-headered.png")


if __name__ == "__main__":
    main()
