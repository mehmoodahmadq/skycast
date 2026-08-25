r"""ASCII weather art.

Every condition is a list of frames; cycling the frames animates the scene.
A frame is a list of lines, all frames of a condition share the same size.

Colour comes from a :class:`Palette`: a base colour per line (weather art is
naturally stratified -- rays on top, body in the middle, precipitation at the
bottom) plus optional per-character overrides applied within every line.

Adding your own art is deliberately easy: append an entry to ``ART`` and a
matching entry to ``PALETTES``. ``tests/test_art.py`` checks the shapes line up.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .models import (
    CLEAR,
    CLEAR_NIGHT,
    CLOUDY,
    DRIZZLE,
    FOG,
    HEAVY_RAIN,
    PARTLY,
    PARTLY_NIGHT,
    RAIN,
    SLEET,
    SNOW,
    THUNDER,
)

Frame = List[str]

# Every frame is padded to this many lines/columns so the layout never jitters.
HEIGHT = 5
WIDTH = 15


@dataclass(frozen=True)
class Palette:
    """Colour plan for one condition's art."""

    lines: List[str]
    overrides: Dict[str, str] = field(default_factory=dict)

    def line_color(self, index: int) -> str:
        if index < len(self.lines):
            return self.lines[index]
        return "default"


def _frames(*blocks: str) -> List[Frame]:
    """Turn raw art blocks into normalised frames.

    Only the single newline that opens a triple-quoted block is dropped, so a
    deliberate blank first line still floats the art down the panel.
    """
    out: List[Frame] = []
    for block in blocks:
        if block.startswith("\n"):
            block = block[1:]
        lines = block.rstrip("\n").split("\n")
        lines = lines[:HEIGHT] + [""] * max(0, HEIGHT - len(lines))
        out.append([line.ljust(WIDTH)[:WIDTH] for line in lines])
    return out


ART: Dict[str, List[Frame]] = {
    CLEAR: _frames(
        r"""
     \   /
      .-.
   --(   )--
      `-'
     /   \
""",
        r"""
    \     /
      .-.
  ---(   )---
      `-'
    /     \
""",
    ),
    CLEAR_NIGHT: _frames(
        r"""
    *      .
       ,-.
      (   )
       `-'  *
    .
""",
        r"""
    .      *
       ,-.
      (   )
       `-'  .
    *
""",
    ),
    PARTLY: _frames(
        r"""
     \  /
     ,''.-.
     \_(   ).
      (___(__)
""",
        r"""
    \   /
     ,''.-.
     \_(   ).
      (___(__)
""",
    ),
    PARTLY_NIGHT: _frames(
        r"""
     *   .
      ,-.
     (   ).
      (___(__)
""",
        r"""
     .   *
      ,-.
     (   ).
      (___(__)
""",
    ),
    CLOUDY: _frames(
        r"""

       .--.
    .-(    ).
   (___.__)__)
""",
        r"""

        .--.
     .-(    ).
    (___.__)__)
""",
    ),
    FOG: _frames(
        r"""
  _ - _ - _ -
   _ - _ - _
  _ - _ - _ -
   _ - _ - _
  _ - _ - _ -
""",
        r"""
   _ - _ - _
  _ - _ - _ -
   _ - _ - _
  _ - _ - _ -
   _ - _ - _
""",
    ),
    DRIZZLE: _frames(
        r"""
      .-.
     (   ).
    (___(__)
     '  '  '
       '  '
""",
        r"""
      .-.
     (   ).
    (___(__)
       '  '
     '  '  '
""",
    ),
    RAIN: _frames(
        r"""
      .-.
     (   ).
    (___(__)
    ' ' ' ' '
     ' ' ' '
""",
        r"""
      .-.
     (   ).
    (___(__)
     ' ' ' '
    ' ' ' ' '
""",
    ),
    HEAVY_RAIN: _frames(
        r"""
      .-.
     (   ).
    (___(__)
    /////////
   /////////
""",
        r"""
      .-.
     (   ).
    (___(__)
   /////////
    /////////
""",
    ),
    SNOW: _frames(
        r"""
      .-.
     (   ).
    (___(__)
     *  *  *
       *  *
""",
        r"""
      .-.
     (   ).
    (___(__)
       *  *
     *  *  *
""",
    ),
    SLEET: _frames(
        r"""
      .-.
     (   ).
    (___(__)
     * ' * '
      ' * '
""",
        r"""
      .-.
     (   ).
    (___(__)
      ' * '
     * ' * '
""",
    ),
    THUNDER: _frames(
        r"""
      .-.
     (   ).
    (___(__)
      /_/
       /
""",
        r"""
      .-.
     (   ).
    (___(__)
    /_/ /_/
     /   /
""",
    ),
}

_CLOUD = ["gray"] * HEIGHT

PALETTES: Dict[str, Palette] = {
    CLEAR: Palette(["bright_yellow"] * HEIGHT),
    CLEAR_NIGHT: Palette(
        ["bright_yellow"] * HEIGHT,
        {"*": "bright_white", ".": "gray"},
    ),
    PARTLY: Palette(
        ["bright_yellow", "gray", "gray", "gray", "gray"],
        {"'": "bright_yellow", ",": "bright_yellow"},
    ),
    PARTLY_NIGHT: Palette(
        ["bright_yellow", "bright_yellow", "gray", "gray", "gray"],
        {"*": "bright_white", ".": "gray"},
    ),
    CLOUDY: Palette(_CLOUD),
    FOG: Palette(["gray"] * HEIGHT, {"-": "dim"}),
    DRIZZLE: Palette(_CLOUD, {"'": "blue"}),
    RAIN: Palette(_CLOUD, {"'": "bright_blue"}),
    HEAVY_RAIN: Palette(_CLOUD, {"/": "bright_blue"}),
    SNOW: Palette(_CLOUD, {"*": "bright_white"}),
    SLEET: Palette(_CLOUD, {"*": "bright_white", "'": "bright_blue"}),
    THUNDER: Palette(
        ["gray", "gray", "gray", "bright_yellow", "bright_yellow"],
    ),
}

_FALLBACK = CLOUDY


def frames(key: str) -> List[Frame]:
    """Frames for an art key, falling back to plain cloud for unknown keys."""
    return ART.get(key, ART[_FALLBACK])


def palette(key: str) -> Palette:
    """Palette for an art key."""
    return PALETTES.get(key, PALETTES[_FALLBACK])


def frame(key: str, index: int = 0) -> Frame:
    """One frame, cycling by ``index``."""
    options = frames(key)
    return options[index % len(options)]


def paint(key: str, index: int, painter) -> Frame:
    """Render one frame with colour applied via ``painter``."""
    plan = palette(key)
    out: Frame = []
    for row, line in enumerate(frame(key, index)):
        base = plan.line_color(row)
        out.append(_paint_line(line, base, plan.overrides, painter))
    return out


def _paint_line(
    line: str,
    base: str,
    overrides: Dict[str, str],
    painter,
) -> str:
    """Colour a line, splitting it into runs that share a colour."""
    if not overrides:
        return painter(line, base)

    parts: List[str] = []
    run = ""
    run_color: Optional[str] = None
    for char in line:
        color = overrides.get(char, base)
        if color != run_color:
            if run:
                parts.append(painter(run, run_color))
            run, run_color = "", color
        run += char
    if run:
        parts.append(painter(run, run_color))
    return "".join(parts)
