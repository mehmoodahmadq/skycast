"""Data models and WMO weather-code mapping."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# Art keys understood by ``skycast.art``. Keep this list in sync with ART.
CLEAR = "clear"
CLEAR_NIGHT = "clear_night"
PARTLY = "partly"
PARTLY_NIGHT = "partly_night"
CLOUDY = "cloudy"
FOG = "fog"
DRIZZLE = "drizzle"
RAIN = "rain"
HEAVY_RAIN = "heavy_rain"
SNOW = "snow"
SLEET = "sleet"
THUNDER = "thunder"

# WMO 4677 weather codes as emitted by Open-Meteo.
# code -> (human label, day art key, night art key)
WMO_CODES: Dict[int, Tuple[str, str, str]] = {
    0: ("Clear sky", CLEAR, CLEAR_NIGHT),
    1: ("Mainly clear", CLEAR, CLEAR_NIGHT),
    2: ("Partly cloudy", PARTLY, PARTLY_NIGHT),
    3: ("Overcast", CLOUDY, CLOUDY),
    45: ("Fog", FOG, FOG),
    48: ("Depositing rime fog", FOG, FOG),
    51: ("Light drizzle", DRIZZLE, DRIZZLE),
    53: ("Moderate drizzle", DRIZZLE, DRIZZLE),
    55: ("Dense drizzle", RAIN, RAIN),
    56: ("Light freezing drizzle", SLEET, SLEET),
    57: ("Dense freezing drizzle", SLEET, SLEET),
    61: ("Slight rain", DRIZZLE, DRIZZLE),
    63: ("Moderate rain", RAIN, RAIN),
    65: ("Heavy rain", HEAVY_RAIN, HEAVY_RAIN),
    66: ("Light freezing rain", SLEET, SLEET),
    67: ("Heavy freezing rain", SLEET, SLEET),
    71: ("Slight snowfall", SNOW, SNOW),
    73: ("Moderate snowfall", SNOW, SNOW),
    75: ("Heavy snowfall", SNOW, SNOW),
    77: ("Snow grains", SNOW, SNOW),
    80: ("Slight rain showers", DRIZZLE, DRIZZLE),
    81: ("Moderate rain showers", RAIN, RAIN),
    82: ("Violent rain showers", HEAVY_RAIN, HEAVY_RAIN),
    85: ("Slight snow showers", SNOW, SNOW),
    86: ("Heavy snow showers", SNOW, SNOW),
    95: ("Thunderstorm", THUNDER, THUNDER),
    96: ("Thunderstorm with slight hail", THUNDER, THUNDER),
    99: ("Thunderstorm with heavy hail", THUNDER, THUNDER),
}

_UNKNOWN = ("Unknown conditions", CLOUDY, CLOUDY)


def describe(code: int) -> str:
    """Human-readable label for a WMO weather code."""
    return WMO_CODES.get(code, _UNKNOWN)[0]


def art_key(code: int, is_day: bool = True) -> str:
    """Art key for a WMO weather code, picking the day or night variant."""
    entry = WMO_CODES.get(code, _UNKNOWN)
    return entry[1] if is_day else entry[2]


_COMPASS = (
    "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
    "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
)


def compass(degrees: float) -> str:
    """Convert a wind bearing in degrees to a 16-point compass label."""
    return _COMPASS[int((degrees % 360) / 22.5 + 0.5) % 16]


@dataclass(frozen=True)
class Place:
    """A resolved geographic location."""

    name: str
    latitude: float
    longitude: float
    country: Optional[str] = None
    admin: Optional[str] = None

    @property
    def label(self) -> str:
        parts = [self.name]
        if self.admin and self.admin != self.name:
            parts.append(self.admin)
        if self.country:
            parts.append(self.country)
        return ", ".join(parts)


@dataclass(frozen=True)
class Day:
    """One day of forecast."""

    date: str
    code: int
    high: float
    low: float
    precip_chance: Optional[int] = None

    @property
    def summary(self) -> str:
        return describe(self.code)


@dataclass(frozen=True)
class Units:
    """Unit labels for a rendered report."""

    temperature: str = "C"
    wind: str = "km/h"
    precipitation: str = "mm"

    @classmethod
    def for_system(cls, system: str) -> "Units":
        if system == "imperial":
            return cls(temperature="F", wind="mph", precipitation="in")
        return cls()


@dataclass(frozen=True)
class Weather:
    """Current conditions plus a short forecast for one place."""

    place: Place
    code: int
    temperature: float
    feels_like: float
    humidity: int
    wind_speed: float
    wind_direction: float
    precipitation: float
    is_day: bool
    observed_at: str
    units: Units = field(default_factory=Units)
    forecast: List[Day] = field(default_factory=list)

    @property
    def summary(self) -> str:
        return describe(self.code)

    @property
    def art_key(self) -> str:
        return art_key(self.code, self.is_day)

    @property
    def wind_compass(self) -> str:
        return compass(self.wind_direction)
