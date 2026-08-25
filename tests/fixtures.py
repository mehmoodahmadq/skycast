"""Shared test fixtures."""

from skycast.models import Day, Place, Units, Weather

PLACE = Place(
    name="Reykjavik",
    latitude=64.1466,
    longitude=-21.9426,
    country="Iceland",
    admin="Capital Region",
)


def weather(code: int = 61, is_day: bool = True, days: int = 3) -> Weather:
    return Weather(
        place=PLACE,
        code=code,
        temperature=7.4,
        feels_like=3.1,
        humidity=81,
        wind_speed=22.0,
        wind_direction=315.0,
        precipitation=1.2,
        is_day=is_day,
        observed_at="2026-08-25T12:00",
        units=Units(),
        forecast=[
            Day(
                date="2026-08-2%d" % (5 + index),
                code=61,
                high=9.0 + index,
                low=4.0 + index,
                precip_chance=60,
            )
            for index in range(days)
        ],
    )
