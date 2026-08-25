"""Tiny ANSI colour helper. No dependencies, honours NO_COLOR."""

from __future__ import annotations

import os
import sys

RESET = "\033[0m"

CODES = {
    "default": "",
    "gray": "\033[90m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
    "bright_red": "\033[91m",
    "bright_yellow": "\033[93m",
    "bright_blue": "\033[94m",
    "bright_magenta": "\033[95m",
    "bright_cyan": "\033[96m",
    "bright_white": "\033[97m",
    "bold": "\033[1m",
    "dim": "\033[2m",
}


def supported(stream=None) -> bool:
    """True when the stream can reasonably display ANSI colour."""
    stream = stream or sys.stdout
    if os.environ.get("NO_COLOR") is not None:
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    return bool(getattr(stream, "isatty", lambda: False)())


class Painter:
    """Applies colour codes, or passes text straight through when disabled."""

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled

    def __call__(self, text: str, color: str | None) -> str:
        if not self.enabled or not color:
            return text
        code = CODES.get(color, "")
        if not code:
            return text
        return f"{code}{text}{RESET}"
