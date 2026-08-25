"""Command line interface for skycast."""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import sys
import time
from collections.abc import Sequence

from . import __version__, api, colors, layout
from .api import SkycastError
from .models import Weather

ENV_LOCATION = "SKYCAST_DEFAULT_LOCATION"

HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"
CLEAR_LINE = "\033[K"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skycast",
        description="Real weather, rendered as animated ASCII art.",
        epilog=f"Set {ENV_LOCATION} to skip typing your usual location.",
    )
    parser.add_argument(
        "location",
        nargs="*",
        help='place name or "lat,lon" (e.g. Kyoto / 35.01,135.76)',
    )
    parser.add_argument(
        "--here",
        action="store_true",
        help="locate via your IP address (sends your IP to ipapi.co)",
    )
    parser.add_argument(
        "-u",
        "--units",
        choices=("metric", "imperial"),
        default="metric",
        help="unit system (default: metric)",
    )
    parser.add_argument(
        "-d",
        "--days",
        type=int,
        default=3,
        help="days of forecast, 1-7 (default: 3)",
    )
    parser.add_argument(
        "-a",
        "--animate",
        action="store_true",
        help="animate the art in place until Ctrl-C",
    )
    parser.add_argument(
        "--fps",
        type=float,
        default=2.0,
        help="animation frames per second (default: 2)",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=None,
        help="stop animating after this many seconds",
    )
    parser.add_argument(
        "--no-forecast",
        action="store_true",
        help="show current conditions only",
    )
    parser.add_argument("--json", action="store_true", help="print raw JSON instead")
    color = parser.add_mutually_exclusive_group()
    color.add_argument(
        "--color", action="store_true", help="force colour output"
    )
    color.add_argument(
        "--no-color", action="store_true", help="disable colour output"
    )
    parser.add_argument("--version", action="version", version=f"skycast {__version__}")
    return parser


def resolve_location(args: argparse.Namespace) -> str | None:
    if args.location:
        return " ".join(args.location).strip()
    return os.environ.get(ENV_LOCATION) or None


def _use_color(args: argparse.Namespace) -> bool:
    if args.no_color:
        return False
    if args.color:
        return True
    return colors.supported(sys.stdout)


def _as_json(weather: Weather) -> str:
    payload = dataclasses.asdict(weather)
    payload["summary"] = weather.summary
    payload["art_key"] = weather.art_key
    payload["wind_compass"] = weather.wind_compass
    for index, day in enumerate(payload.get("forecast", [])):
        day["summary"] = weather.forecast[index].summary
    return json.dumps(payload, indent=2, sort_keys=True)


def _print(lines: list[str], stream) -> None:
    stream.write("\n".join(lines) + "\n")
    stream.flush()


def animate(
    weather: Weather,
    painter: colors.Painter,
    fps: float,
    duration: float | None,
    show_forecast: bool,
    stream=None,
) -> None:
    """Redraw the report in place until interrupted or ``duration`` elapses."""
    stream = stream or sys.stdout
    delay = 1.0 / fps if fps > 0 else 0.5
    deadline = None if duration is None else time.monotonic() + duration
    height = 0

    stream.write(HIDE_CURSOR)
    try:
        index = 0
        while True:
            lines = layout.report(
                weather, painter, frame=index, show_forecast=show_forecast
            )
            if height:
                stream.write(f"\033[{height}A")
            stream.write(
                "".join(f"{line}{CLEAR_LINE}\n" for line in lines)
            )
            stream.flush()
            height = len(lines)
            index += 1

            if deadline is not None and time.monotonic() >= deadline:
                return
            time.sleep(delay)
    except KeyboardInterrupt:
        return
    finally:
        stream.write(SHOW_CURSOR)
        stream.flush()


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    location = resolve_location(args)
    if not location and not args.here:
        build_parser().print_usage(sys.stderr)
        sys.stderr.write(
            f"skycast: give a location, pass --here, or set {ENV_LOCATION}\n"
        )
        return 2

    try:
        place = api.locate_by_ip() if args.here else None
        weather = api.fetch(
            location=None if place else location,
            place=place,
            system=args.units,
            days=args.days,
        )
    except SkycastError as exc:
        sys.stderr.write(f"skycast: {exc}\n")
        return 1

    if args.json:
        print(_as_json(weather))
        return 0

    painter = colors.Painter(enabled=_use_color(args))
    show_forecast = not args.no_forecast

    if args.animate:
        animate(weather, painter, args.fps, args.duration, show_forecast)
    else:
        _print(
            layout.report(weather, painter, show_forecast=show_forecast),
            sys.stdout,
        )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
