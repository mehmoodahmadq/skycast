#!/usr/bin/env python3
"""Print every art condition and its animation frames, offline.

    python examples/gallery.py

Handy when you are adding art: you see all frames side by side without
waiting for the right weather to happen somewhere in the world.
"""

import os
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
)

from skycast import art  # noqa: E402
from skycast.colors import Painter, supported  # noqa: E402
from skycast.models import WMO_CODES  # noqa: E402


def codes_for(key):
    """Which WMO codes render with this art."""
    return sorted(
        code for code, (_, day, night) in WMO_CODES.items() if key in (day, night)
    )


def main():
    painter = Painter(enabled=supported(sys.stdout))
    gutter = "    "

    for key in sorted(art.ART):
        frames = [art.paint(key, index, painter) for index in range(len(art.ART[key]))]
        codes = codes_for(key)
        header = "%s  %s" % (
            painter(key, "bold"),
            painter("WMO %s" % ", ".join(str(code) for code in codes), "gray"),
        )
        print("\n" + header)
        for row in range(art.HEIGHT):
            print(("  " + gutter.join(frame[row] for frame in frames)).rstrip())

    print(
        "\n%s conditions, %s frames total."
        % (len(art.ART), sum(len(frames) for frames in art.ART.values()))
    )


if __name__ == "__main__":
    main()
