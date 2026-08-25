"""Lay out a :class:`~skycast.models.Weather` as terminal lines."""

from __future__ import annotations

import datetime as _dt

from . import art
from .colors import Painter
from .models import Day, Weather

GUTTER = "   "
INDENT = "  "


def _weekday(date: str) -> str:
    """Short weekday name for an ISO date, or the input if it will not parse."""
    try:
        parsed = _dt.datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        return date
    return parsed.strftime("%a")


def _temp(value: float, units) -> str:
    return f"{round(value)}°{units.temperature}"


def details(weather: Weather, paint: Painter) -> list[str]:
    """The right-hand column: summary and current readings."""
    units = weather.units
    now = paint(_temp(weather.temperature, units), "bright_white")
    feels = paint(f"feels {_temp(weather.feels_like, units)}", "gray")
    wind = f"{round(weather.wind_speed, 1):g} {units.wind}"
    precip = f"{round(weather.precipitation, 2):g} {units.precipitation}"
    return [
        paint(weather.summary, "bold"),
        f"{now}  {feels}",
        f"{paint('wind', 'gray')} {weather.wind_compass} {wind}",
        f"{paint('humidity', 'gray')} {weather.humidity}%",
        f"{paint('precip', 'gray')} {precip}",
    ]


DAY_WIDTH = 6
TEMP_WIDTH = 11
SUMMARY_WIDTH = 22


def forecast_rows(days: list[Day], weather: Weather, paint: Painter) -> list[str]:
    """The forecast strip printed under the art.

    The API is asked for the location's own timezone, so the first row is
    always "today" where the weather is -- not where the reader is.
    """
    units = weather.units
    rows = []
    for index, day in enumerate(days):
        label = "Today" if index == 0 else _weekday(day.date)
        temps = f"{_temp(day.high, units)}/{_temp(day.low, units)}"
        chance = ""
        if day.precip_chance:
            chance = paint(f"{day.precip_chance}% precip", "bright_blue")
        summary = paint(day.summary.ljust(SUMMARY_WIDTH), "gray")
        row = (
            f"{INDENT}{label.ljust(DAY_WIDTH)}"
            f"{temps.ljust(TEMP_WIDTH)}{summary}{chance}"
        )
        rows.append(row.rstrip())
    return rows


def report(
    weather: Weather,
    painter: Painter | None = None,
    frame: int = 0,
    show_forecast: bool = True,
) -> list[str]:
    """Render a full report as a list of lines (no trailing newlines)."""
    paint = painter or Painter(enabled=False)

    lines: list[str] = [
        "{}{}".format(INDENT, paint(weather.place.label, "bold")),
        "",
    ]

    panel = art.paint(weather.art_key, frame, paint)
    column = details(weather, paint)
    rows = max(len(panel), len(column))
    for index in range(rows):
        left = panel[index] if index < len(panel) else " " * art.WIDTH
        right = column[index] if index < len(column) else ""
        lines.append((f"{INDENT}{left}{GUTTER}{right}").rstrip())

    if show_forecast and weather.forecast:
        lines.append("")
        lines.extend(forecast_rows(weather.forecast, weather, paint))

    return lines


def render(
    weather: Weather,
    color: bool = True,
    frame: int = 0,
    show_forecast: bool = True,
) -> str:
    """Render a report as a single string."""
    return "\n".join(
        report(
            weather,
            Painter(enabled=color),
            frame=frame,
            show_forecast=show_forecast,
        )
    )
