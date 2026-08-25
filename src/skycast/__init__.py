"""skycast — real weather, rendered as animated ASCII art.

    >>> import skycast
    >>> weather = skycast.fetch("Reykjavik")
    >>> print(skycast.render(weather, color=False))
"""

from __future__ import annotations

__version__ = "0.1.1"

from .api import SkycastError, fetch, geocode, locate_by_ip
from .layout import render, report
from .models import Day, Place, Units, Weather, art_key, compass, describe

__all__ = [
    "__version__",
    "Day",
    "Place",
    "SkycastError",
    "Units",
    "Weather",
    "art_key",
    "compass",
    "describe",
    "fetch",
    "geocode",
    "locate_by_ip",
    "render",
    "report",
]
