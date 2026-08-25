"""Open-Meteo client. Stdlib only, no API key required."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from .models import Day, Place, Units, Weather

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
# Only reached via the explicit --here flag; see README on what it discloses.
IP_LOOKUP_URL = "https://ipapi.co/json/"

USER_AGENT = "skycast (+https://github.com/mehmoodahmadq/skycast)"
DEFAULT_TIMEOUT = 10.0

_LATLON = re.compile(
    r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$"
)


class SkycastError(RuntimeError):
    """Anything that stopped us producing a forecast."""


def _get(url: str, params: dict[str, Any], timeout: float) -> dict[str, Any]:
    query = urllib.parse.urlencode(params, doseq=True)
    request = urllib.request.Request(
        f"{url}?{query}" if query else url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise SkycastError(
            f"weather service returned HTTP {exc.code}"
        ) from exc
    except urllib.error.URLError as exc:
        raise SkycastError(
            f"could not reach the weather service: {exc.reason}"
        ) from exc
    except OSError as exc:  # timeouts, DNS, TLS
        raise SkycastError(f"network error: {exc}") from exc

    try:
        return json.loads(payload)
    except ValueError as exc:
        raise SkycastError("weather service sent malformed JSON") from exc


def geocode(query: str, timeout: float = DEFAULT_TIMEOUT) -> Place:
    """Resolve a place name, or a bare ``lat,lon`` pair, to a :class:`Place`."""
    match = _LATLON.match(query)
    if match:
        lat, lon = float(match.group(1)), float(match.group(2))
        if not -90 <= lat <= 90 or not -180 <= lon <= 180:
            raise SkycastError(f"coordinates out of range: {query}")
        return Place(name=f"{lat:.4f}, {lon:.4f}", latitude=lat, longitude=lon)

    data = _get(
        GEOCODE_URL,
        {"name": query, "count": 1, "language": "en", "format": "json"},
        timeout,
    )
    results = data.get("results") or []
    if not results:
        raise SkycastError(f"no place matched {query!r}")

    top = results[0]
    return Place(
        name=top.get("name") or query,
        latitude=float(top["latitude"]),
        longitude=float(top["longitude"]),
        country=top.get("country"),
        admin=top.get("admin1"),
    )


def locate_by_ip(timeout: float = DEFAULT_TIMEOUT) -> Place:
    """Best-effort location from the caller's IP address.

    This sends a request to a third-party service (ipapi.co) which sees the
    caller's IP. Only used when the user explicitly asks for it.
    """
    data = _get(IP_LOOKUP_URL, {}, timeout)
    if data.get("error") or "latitude" not in data:
        raise SkycastError("IP lookup could not determine a location")
    return Place(
        name=data.get("city") or "Your location",
        latitude=float(data["latitude"]),
        longitude=float(data["longitude"]),
        country=data.get("country_name"),
        admin=data.get("region"),
    )


def _forecast_params(place: Place, system: str, days: int) -> dict[str, Any]:
    params: dict[str, Any] = {
        "latitude": place.latitude,
        "longitude": place.longitude,
        "current": ",".join(
            (
                "temperature_2m",
                "relative_humidity_2m",
                "apparent_temperature",
                "is_day",
                "precipitation",
                "weather_code",
                "wind_speed_10m",
                "wind_direction_10m",
            )
        ),
        "daily": ",".join(
            (
                "weather_code",
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_probability_max",
            )
        ),
        "timezone": "auto",
        "forecast_days": max(1, min(days, 7)),
    }
    if system == "imperial":
        params.update(
            temperature_unit="fahrenheit",
            wind_speed_unit="mph",
            precipitation_unit="inch",
        )
    return params


def _daily(data: dict[str, Any]) -> list[Day]:
    daily = data.get("daily") or {}
    dates = daily.get("time") or []
    codes = daily.get("weather_code") or []
    highs = daily.get("temperature_2m_max") or []
    lows = daily.get("temperature_2m_min") or []
    chances = daily.get("precipitation_probability_max") or []

    out: list[Day] = []
    for index, date in enumerate(dates):
        if index >= len(codes) or index >= len(highs) or index >= len(lows):
            break
        if highs[index] is None or lows[index] is None:
            continue
        chance = chances[index] if index < len(chances) else None
        out.append(
            Day(
                date=date,
                code=int(codes[index] or 0),
                high=float(highs[index]),
                low=float(lows[index]),
                precip_chance=int(chance) if chance is not None else None,
            )
        )
    return out


def fetch(
    location: str | None = None,
    system: str = "metric",
    days: int = 3,
    place: Place | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> Weather:
    """Fetch current conditions and a short forecast.

    Pass either a ``location`` string (place name or ``lat,lon``) or an
    already-resolved ``place``.
    """
    if place is None:
        if not location:
            raise SkycastError("a location is required")
        place = geocode(location, timeout=timeout)

    data = _get(FORECAST_URL, _forecast_params(place, system, days), timeout)
    current = data.get("current") or {}
    if "temperature_2m" not in current:
        raise SkycastError("weather service sent no current conditions")

    return Weather(
        place=place,
        code=int(current.get("weather_code") or 0),
        temperature=float(current["temperature_2m"]),
        feels_like=float(
            current.get("apparent_temperature", current["temperature_2m"])
        ),
        humidity=int(current.get("relative_humidity_2m") or 0),
        wind_speed=float(current.get("wind_speed_10m") or 0.0),
        wind_direction=float(current.get("wind_direction_10m") or 0.0),
        precipitation=float(current.get("precipitation") or 0.0),
        is_day=bool(current.get("is_day", 1)),
        observed_at=str(current.get("time") or ""),
        units=Units.for_system(system),
        forecast=_daily(data),
    )
