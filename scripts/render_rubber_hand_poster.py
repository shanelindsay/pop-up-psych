#!/usr/bin/env python3
"""Render a deterministic Rubber Hand Illusion poster.

This replaces the unstable image-generation step for the activity where the
canonical divider geometry matters.
"""

from __future__ import annotations

import math
import argparse
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


REPO = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO / "images" / "rubber-hand-illusion.png"

W, H = 1024, 1536
IVORY = (250, 247, 239)
INK = (31, 24, 36)
TEAL = (0, 111, 115)
TEAL_DARK = (0, 92, 96)
PERSIMMON = (241, 88, 36)
AUBERGINE = (74, 46, 101)
MINT = (219, 244, 224)
TABLE = (39, 42, 41)
CLOTH = (104, 58, 87)
SKIN = (232, 183, 145)
SKIN_DARK = (180, 116, 84)
SCREEN = (225, 224, 216)
SCREEN_EDGE = (127, 125, 116)

FONT = "/usr/share/fonts/TTF/DejaVuSansCondensed.ttf"
BOLD = "/usr/share/fonts/TTF/DejaVuSansCondensed-Bold.ttf"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(BOLD if bold else FONT, size)


def text_size(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0], box[3] - box[1]


def wrap(text: str, chars: int) -> str:
    return "\n".join(textwrap.wrap(text, width=chars, break_long_words=False))


def rounded(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], fill, outline=None, width: int = 2, radius: int = 10) -> None:
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def draw_centered(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], text: str, fnt, fill=INK) -> None:
    x1, y1, x2, y2 = xy
    tw, th = text_size(draw, text, fnt)
    draw.text((x1 + (x2 - x1 - tw) / 2, y1 + (y2 - y1 - th) / 2), text, font=fnt, fill=fill)


def panel(draw: ImageDraw.ImageDraw, xy, title: str, colour, title_size: int = 37) -> None:
    x1, y1, x2, y2 = xy
    rounded(draw, xy, fill=(255, 253, 248), outline=colour, width=2, radius=12)
    draw.rounded_rectangle((x1, y1, x2, y1 + 70), radius=12, fill=colour)
    draw.rectangle((x1, y1 + 35, x2, y1 + 70), fill=colour)
    draw_centered(draw, (x1, y1, x2, y1 + 70), title, font(title_size, True), fill=(255, 255, 255))


def draw_label(draw: ImageDraw.ImageDraw, anchor: tuple[int, int], text: str, target: tuple[int, int], side: str = "right") -> None:
    fnt = font(19, True)
    wrapped = wrap(text, 16)
    lines = wrapped.splitlines()
    tw = max(text_size(draw, line, fnt)[0] for line in lines)
    th = sum(text_size(draw, line, fnt)[1] + 4 for line in lines) + 12
    x, y = anchor
    box = (x, y, x + tw + 24, y + th)
    rounded(draw, box, fill=(255, 253, 248), outline=TEAL, width=2, radius=7)
    cy = y + 8
    for line in lines:
        draw.text((x + 12, cy), line, font=fnt, fill=INK)
        cy += text_size(draw, line, fnt)[1] + 7
    start = (box[0] if side == "left" else box[2], y + th // 2)
    draw.line((start, target), fill=TEAL, width=3)
    draw.ellipse((target[0] - 5, target[1] - 5, target[0] + 5, target[1] + 5), fill=TEAL)


def draw_hand(draw: ImageDraw.ImageDraw, cx: int, y: int, *, hidden: bool = False) -> None:
    alpha_fill = SKIN if not hidden else (232, 183, 145, 130)
    outline = SKIN_DARK if not hidden else (180, 116, 84, 160)
    # Forearm and palm, vertical top-down orientation.
    draw.rounded_rectangle((cx - 27, y - 82, cx + 27, y + 12), radius=18, fill=alpha_fill, outline=outline, width=2)
    draw.ellipse((cx - 42, y - 2, cx + 42, y + 74), fill=alpha_fill, outline=outline, width=2)
    fingers = [-30, -15, 0, 15, 30]
    lengths = [65, 78, 84, 76, 58]
    widths = [13, 13, 14, 13, 12]
    for dx, length, fw in zip(fingers, lengths, widths):
        draw.rounded_rectangle(
            (cx + dx - fw // 2, y + 38, cx + dx + fw // 2, y + 38 + length),
            radius=fw // 2,
            fill=alpha_fill,
            outline=outline,
            width=2,
        )
    # Thumb.
    draw.line((cx - 36, y + 28, cx - 65, y + 73), fill=outline, width=16)
    draw.line((cx - 37, y + 29, cx - 65, y + 73), fill=alpha_fill, width=12)
    if hidden:
        for off in range(-48, 56, 14):
            draw.line((cx + off, y - 86, cx + off + 35, y + 138), fill=(255, 255, 255, 50), width=2)


def draw_brush(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], colour=PERSIMMON) -> None:
    sx, sy = start
    ex, ey = end
    draw.line((sx, sy, ex, ey), fill=(112, 73, 44), width=9)
    draw.line((sx, sy, ex, ey), fill=(211, 151, 81), width=5)
    angle = math.atan2(ey - sy, ex - sx)
    tip_len = 20
    tx = ex + math.cos(angle) * tip_len
    ty = ey + math.sin(angle) * tip_len
    draw.line((ex, ey, tx, ty), fill=colour, width=13)
    draw.line((ex, ey, tx, ty), fill=(255, 222, 168), width=5)


def draw_experiment_hand(draw: ImageDraw.ImageDraw, cx: int, cy: int) -> None:
    draw.ellipse((cx - 22, cy - 18, cx + 22, cy + 22), fill=SKIN, outline=SKIN_DARK, width=2)
    draw.rounded_rectangle((cx - 14, cy + 14, cx + 14, cy + 86), radius=12, fill=SKIN, outline=SKIN_DARK, width=2)


def draw_diagram(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = xy
    rounded(draw, xy, fill=(250, 250, 246), outline=TEAL, width=2, radius=12)
    table = (x1 + 24, y1 + 30, x2 - 24, y2 - 28)
    rounded(draw, table, fill=TABLE, outline=(12, 15, 15), width=2, radius=18)

    tx1, ty1, tx2, ty2 = table
    midx = (tx1 + tx2) // 2
    cloth_y = ty1 + 60
    draw.ellipse((midx - 65, ty1 + 8, midx + 65, ty1 + 112), fill=(236, 204, 171), outline=SKIN_DARK, width=2)
    draw.polygon(
        [(midx - 170, cloth_y + 10), (midx + 170, cloth_y + 10), (midx + 125, cloth_y + 180), (midx - 125, cloth_y + 180)],
        fill=CLOTH,
        outline=(72, 34, 59),
    )

    divider_x = midx + 8
    divider_top = cloth_y + 42
    divider_bottom = ty2 - 82
    draw.rounded_rectangle((divider_x - 13, divider_top, divider_x + 13, divider_bottom), radius=5, fill=SCREEN_EDGE)
    draw.rectangle((divider_x - 6, divider_top + 7, divider_x + 6, divider_bottom - 7), fill=SCREEN)
    draw.line((divider_x - 13, divider_top, divider_x + 13, divider_top), fill=(255, 255, 255), width=2)

    hidden_x = divider_x - 102
    rubber_x = divider_x + 112
    hand_y = cloth_y + 178
    draw_hand(draw, hidden_x, hand_y, hidden=True)
    draw_hand(draw, rubber_x, hand_y, hidden=False)
    draw.text((rubber_x - 54, hand_y + 134), "rubber hand", font=font(16, True), fill=(235, 232, 218))
    draw.text((hidden_x - 48, hand_y + 134), "real hand", font=font(16, True), fill=(235, 232, 218))

    # Experimenter hands and synchronous brushing from the near side.
    draw_experiment_hand(draw, hidden_x - 68, ty2 - 52)
    draw_experiment_hand(draw, rubber_x + 72, ty2 - 52)
    draw_brush(draw, (hidden_x - 50, ty2 - 82), (hidden_x - 9, hand_y + 52), colour=TEAL)
    draw_brush(draw, (rubber_x + 52, ty2 - 82), (rubber_x + 10, hand_y + 52), colour=TEAL)
    draw.arc((hidden_x - 16, hand_y + 34, hidden_x + 28, hand_y + 78), 210, 330, fill=PERSIMMON, width=4)
    draw.arc((rubber_x - 28, hand_y + 34, rubber_x + 16, hand_y + 78), 210, 330, fill=PERSIMMON, width=4)

    draw_label(draw, (x1 + 42, y1 + 48), "hidden real hand", (hidden_x, hand_y + 46), side="right")
    draw_label(draw, (x2 - 190, y1 + 48), "visible rubber hand", (rubber_x, hand_y + 46), side="left")
    draw_label(draw, (x1 + 40, y2 - 118), "divider screen", (divider_x, divider_top + 80), side="right")
    draw_label(draw, (x2 - 190, y2 - 118), "synchronous brushing", (rubber_x + 8, hand_y + 54), side="left")


def draw_diagram_facing_participant(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = xy
    rounded(draw, xy, fill=(250, 250, 246), outline=TEAL, width=2, radius=12)
    table = (x1 + 24, y1 + 70, x2 - 24, y2 - 28)
    rounded(draw, table, fill=TABLE, outline=(12, 15, 15), width=2, radius=18)

    tx1, ty1, tx2, ty2 = table
    midx = (tx1 + tx2) // 2

    # Participant facing the viewer across the table.
    head = (midx - 46, y1 + 20, midx + 46, y1 + 105)
    draw.ellipse(head, fill=(236, 204, 171), outline=SKIN_DARK, width=2)
    draw.arc((head[0] + 18, head[1] + 36, head[2] - 18, head[3] - 20), 15, 165, fill=INK, width=2)
    cloth = [
        (midx - 210, ty1 + 28),
        (midx + 210, ty1 + 28),
        (midx + 168, ty1 + 210),
        (midx - 168, ty1 + 210),
    ]
    draw.polygon(cloth, fill=CLOTH, outline=(72, 34, 59))
    draw.line((midx - 190, ty1 + 32, midx + 190, ty1 + 32), fill=(133, 78, 111), width=5)

    # Lengthwise divider: from participant toward experimenter, between hands.
    divider_x = midx + 10
    top_y = ty1 + 70
    bottom_y = ty2 - 110
    board = [
        (divider_x - 18, top_y),
        (divider_x + 18, top_y + 10),
        (divider_x + 18, bottom_y),
        (divider_x - 18, bottom_y - 10),
    ]
    draw.polygon(board, fill=SCREEN_EDGE, outline=(75, 75, 70))
    draw.polygon(
        [(divider_x - 10, top_y + 8), (divider_x + 10, top_y + 14), (divider_x + 10, bottom_y - 8), (divider_x - 10, bottom_y - 14)],
        fill=SCREEN,
    )
    draw.rounded_rectangle((divider_x - 42, bottom_y - 8, divider_x + 42, bottom_y + 18), radius=5, fill=(161, 130, 82), outline=(92, 65, 36), width=2)

    # Hands sit beside the divider, with wrists disappearing under cloth.
    hidden_x = divider_x - 118
    rubber_x = divider_x + 116
    hand_y = ty1 + 240
    draw_hand(draw, hidden_x, hand_y, hidden=True)
    draw.rectangle((hidden_x - 58, ty1 + 74, hidden_x + 58, ty1 + 156), fill=CLOTH)
    draw.text((hidden_x - 50, hand_y + 134), "real hand", font=font(16, True), fill=(235, 232, 218))

    draw_hand(draw, rubber_x, hand_y, hidden=False)
    draw.rectangle((rubber_x - 58, ty1 + 74, rubber_x + 58, ty1 + 156), fill=CLOTH)
    draw.text((rubber_x - 56, hand_y + 134), "rubber hand", font=font(16, True), fill=(235, 232, 218))

    # Experimenter hands enter from foreground and brush both hands at matched points.
    draw_experiment_hand(draw, hidden_x - 62, ty2 - 58)
    draw_experiment_hand(draw, rubber_x + 66, ty2 - 58)
    draw_brush(draw, (hidden_x - 44, ty2 - 90), (hidden_x - 4, hand_y + 55), colour=TEAL)
    draw_brush(draw, (rubber_x + 46, ty2 - 90), (rubber_x + 4, hand_y + 55), colour=TEAL)
    draw.arc((hidden_x - 16, hand_y + 34, hidden_x + 28, hand_y + 78), 210, 330, fill=PERSIMMON, width=4)
    draw.arc((rubber_x - 28, hand_y + 34, rubber_x + 16, hand_y + 78), 210, 330, fill=PERSIMMON, width=4)

    draw_label(draw, (x1 + 40, y1 + 48), "hidden real hand", (hidden_x, hand_y + 46), side="right")
    draw_label(draw, (x2 - 190, y1 + 48), "visible rubber hand", (rubber_x, hand_y + 46), side="left")
    draw_label(draw, (x1 + 40, y2 - 118), "lengthwise divider", (divider_x, top_y + 90), side="right")
    draw_label(draw, (x2 - 190, y2 - 118), "synchronous brushing", (rubber_x + 8, hand_y + 54), side="left")


def draw_steps(draw: ImageDraw.ImageDraw, xy) -> None:
    panel(draw, xy, "RUN THE EXPERIMENT", TEAL_DARK, title_size=31)
    x1, y1, x2, _ = xy
    steps = [
        "Seat participant at the table.",
        "Hide their real hand behind a lengthwise screen.",
        "Place the rubber hand in view, aligned with the arm.",
        "Brush both hands together for 60 seconds.",
        "Ask where they feel the touch.",
    ]
    y = y1 + 95
    for idx, line in enumerate(steps, 1):
        rounded(draw, (x1 + 24, y - 5, x1 + 70, y + 41), fill=TEAL_DARK, radius=8)
        draw_centered(draw, (x1 + 24, y - 5, x1 + 70, y + 41), str(idx), font(30, True), fill=(255, 255, 255))
        draw.text((x1 + 92, y - 4), wrap(line, 30), font=font(22), fill=INK)
        if idx < len(steps):
            draw.line((x1 + 24, y + 62, x2 - 24, y + 62), fill=TEAL, width=2)
        y += 88


def draw_observation(draw: ImageDraw.ImageDraw, xy) -> None:
    panel(draw, xy, "WHAT TO WATCH FOR", PERSIMMON, title_size=29)
    x1, y1, x2, _ = xy
    lines = [
        "The participant may feel touch on the rubber hand.",
        "Some people feel that the rubber hand belongs to them.",
        "A sudden threat to the rubber hand may make them flinch.",
    ]
    y = y1 + 98
    for line in lines:
        draw.text((x1 + 40, y), wrap(line, 31), font=font(20), fill=INK)
        y += 92
        draw.line((x1 + 28, y - 18, x2 - 28, y - 18), fill=PERSIMMON, width=2)


def draw_debrief(draw: ImageDraw.ImageDraw, xy) -> None:
    panel(draw, xy, "DEBRIEF", AUBERGINE, title_size=36)
    x1, y1, x2, _ = xy
    lines = [
        "Vision and touch are synchronised.",
        "The brain uses this multisensory evidence to judge body ownership.",
        "When the seen hand and felt touch match, the rubber hand can be experienced as part of the body.",
        "The illusion shows that the sense of my body is actively constructed.",
    ]
    y = y1 + 94
    body = font(18)
    for line in lines:
        draw.ellipse((x1 + 32, y + 8, x1 + 43, y + 19), fill=AUBERGINE)
        wrapped = wrap(line, 52)
        draw.text((x1 + 60, y), wrapped, font=body, fill=INK)
        _, h = text_size(draw, wrapped, body)
        y += h + 38
        if y < xy[3] - 30:
            draw.line((x1 + 24, y - 20, x2 - 24, y - 20), fill=(124, 93, 147), width=1)


def render(out: Path, *, variant: str) -> None:
    img = Image.new("RGB", (W, H), IVORY)
    draw = ImageDraw.Draw(img, "RGBA")

    # Blank header band for the fixed logo overlay workflow.
    draw.line((20, 96, W - 20, 96), fill=INK, width=2)

    draw.text((36, 145), "RUBBER HAND ILLUSION", font=font(74, True), fill=(25, 8, 38))
    draw.text((40, 292), "Can a fake hand feel like yours?", font=font(39, True), fill=TEAL_DARK)
    draw.line((40, 356, 176, 356), fill=PERSIMMON, width=5)

    draw_steps(draw, (22, 396, 430, 956))
    if variant == "facing":
        draw_diagram_facing_participant(draw, (450, 368, 1002, 960))
    else:
        draw_diagram(draw, (450, 368, 1002, 960))
    draw_observation(draw, (22, 984, 440, 1380))
    draw_debrief(draw, (462, 984, 1002, 1380))

    # Quiet footer motif, kept below content.
    draw.ellipse((-78, 1412, 210, 1698), fill=(0, 111, 115, 210))
    draw.ellipse((258, 1456, 592, 1780), fill=(241, 88, 36, 220))
    draw.ellipse((558, 1500, 910, 1818), fill=(74, 46, 101, 215))
    draw.ellipse((800, 1414, 1138, 1714), fill=(196, 219, 203, 180))
    for x in range(230, 390, 26):
        for y in range(1415, 1480, 24):
            draw.ellipse((x, y, x + 7, y + 7), fill=TEAL_DARK)

    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, quality=95)
    print(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", choices=["topdown", "facing", "both"], default="topdown")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    if args.variant == "both":
        render(REPO / "images" / "rubber-hand-illusion-topdown.png", variant="topdown")
        render(REPO / "images" / "rubber-hand-illusion-facing.png", variant="facing")
    else:
        render(args.out, variant=args.variant)


if __name__ == "__main__":
    main()
