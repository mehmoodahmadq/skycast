#!/usr/bin/env python3
"""Render the animated report to a GIF for the README.

    pip install Pillow
    python examples/make_demo_gif.py Manila --out assets/demo.gif

Pillow is needed only for this script -- skycast itself stays dependency-free.
The GIF is generated from the real renderer, so regenerating it after an art
change is one command rather than another screen recording.
"""

from __future__ import annotations

import argparse
import os
import re
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
)

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import skycast  # noqa: E402
from skycast.colors import Painter  # noqa: E402

FONT_CANDIDATES = (
    "/System/Library/Fonts/Menlo.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/Library/Fonts/Courier New.ttf",
)

# A GitHub-dark-ish palette, so the GIF sits comfortably in a README.
BG = (13, 17, 23)
CHROME = (22, 27, 34)
DEFAULT_FG = (201, 209, 217)

SGR = {
    0: DEFAULT_FG,
    1: (240, 246, 252),  # bold -> brightest
    2: (110, 118, 129),  # dim
    31: (255, 123, 114),
    32: (86, 211, 100),
    33: (210, 153, 34),
    34: (56, 139, 253),
    35: (188, 140, 255),
    36: (57, 197, 207),
    37: (201, 209, 217),
    90: (110, 118, 129),
    91: (255, 123, 114),
    93: (227, 179, 65),
    94: (121, 192, 255),
    95: (210, 168, 255),
    96: (86, 214, 224),
    97: (240, 246, 252),
}

ANSI = re.compile(r"\033\[([0-9;?]*)([a-zA-Z])")


def load_font(size: int):
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    raise SystemExit("no monospace font found; edit FONT_CANDIDATES")


def runs(line: str):
    """Split an ANSI-coloured line into (text, rgb) runs."""
    out = []
    color = DEFAULT_FG
    index = 0
    for match in ANSI.finditer(line):
        if match.start() > index:
            out.append((line[index : match.start()], color))
        if match.group(2) == "m":
            for part in (match.group(1) or "0").split(";"):
                if part.isdigit():
                    color = SGR.get(int(part), color)
        index = match.end()
    if index < len(line):
        out.append((line[index:], color))
    return out


def render(frames, font, char_w: float, line_h: int, pad: int, chrome: int):
    width = max(
        len(ANSI.sub("", line)) for frame in frames for line in frame
    )
    size = (
        int(width * char_w) + pad * 2,
        len(frames[0]) * line_h + pad * 2 + chrome,
    )

    images = []
    for frame in frames:
        image = Image.new("RGB", size, BG)
        draw = ImageDraw.Draw(image)
        if chrome:
            draw.rectangle([0, 0, size[0], chrome], fill=CHROME)
            for i, dot in enumerate(((255, 95, 86), (255, 189, 46), (39, 201, 63))):
                cx = pad + 6 + i * 16
                cy = chrome // 2
                draw.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=dot)

        for row, line in enumerate(frame):
            y = chrome + pad + row * line_h
            x = float(pad)
            for text, color in runs(line):
                if text.strip():
                    draw.text((x, y), text, font=font, fill=color)
                x += len(text) * char_w
        images.append(image)
    return images


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("location", nargs="*", default=["Manila"])
    parser.add_argument("--out", default="assets/demo.gif")
    parser.add_argument("--font-size", type=int, default=28)
    parser.add_argument("--cycles", type=int, default=3)
    parser.add_argument("--ms", type=int, default=550, help="ms per frame")
    parser.add_argument("--units", default="metric")
    args = parser.parse_args()

    location = " ".join(args.location) or "Manila"
    weather = skycast.fetch(location, system=args.units)
    print(f"{weather.place.label}: {weather.summary} (art={weather.art_key})")

    painter = Painter(enabled=True)
    frames = [
        skycast.report(weather, painter, frame=index)
        for index in range(2 * args.cycles)
    ]

    font = load_font(args.font_size)
    char_w = font.getlength("M")
    line_h = int(args.font_size * 1.45)
    images = render(frames, font, char_w, line_h, pad=18, chrome=34)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    first, *rest = [
        image.convert("P", palette=Image.ADAPTIVE, colors=64) for image in images
    ]
    first.save(
        args.out,
        save_all=True,
        append_images=rest,
        duration=args.ms,
        loop=0,
        optimize=True,
    )
    print(f"wrote {args.out}  ({os.path.getsize(args.out) / 1024:.0f} KB, "
          f"{len(images)} frames, {images[0].size[0]}x{images[0].size[1]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
