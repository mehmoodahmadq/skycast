import unittest
from unittest import mock

from skycast import api
from skycast.api import SkycastError

FORECAST_PAYLOAD = {
    "current": {
        "time": "2026-08-25T12:00",
        "temperature_2m": 7.4,
        "relative_humidity_2m": 81,
        "apparent_temperature": 3.1,
        "is_day": 1,
        "precipitation": 1.2,
        "weather_code": 63,
        "wind_speed_10m": 22.0,
        "wind_direction_10m": 315,
    },
    "daily": {
        "time": ["2026-08-25", "2026-08-26"],
        "weather_code": [63, 3],
        "temperature_2m_max": [9.0, 11.0],
        "temperature_2m_min": [4.0, 5.0],
        "precipitation_probability_max": [60, 10],
    },
}

GEOCODE_PAYLOAD = {
    "results": [
        {
            "name": "Reykjavik",
            "latitude": 64.1466,
            "longitude": -21.9426,
            "country": "Iceland",
            "admin1": "Capital Region",
        }
    ]
}


class GeocodeTests(unittest.TestCase):
    def test_parses_bare_coordinates_without_a_request(self):
        with mock.patch.object(api, "_get", side_effect=AssertionError) as get:
            place = api.geocode(" 35.01, 135.76 ")
        get.assert_not_called()
        self.assertAlmostEqual(place.latitude, 35.01)
        self.assertAlmostEqual(place.longitude, 135.76)

    def test_rejects_out_of_range_coordinates(self):
        with self.assertRaises(SkycastError):
            api.geocode("120,0")

    def test_resolves_a_name(self):
        with mock.patch.object(api, "_get", return_value=GEOCODE_PAYLOAD):
            place = api.geocode("reykjavik")
        self.assertEqual(place.label, "Reykjavik, Capital Region, Iceland")

    def test_empty_results_raise(self):
        with mock.patch.object(api, "_get", return_value={"results": []}):
            with self.assertRaises(SkycastError):
                api.geocode("zzzzzz")


class FetchTests(unittest.TestCase):
    def test_builds_weather_from_payload(self):
        with mock.patch.object(api, "_get", return_value=FORECAST_PAYLOAD):
            weather = api.fetch(place=api.Place("Test", 0.0, 0.0))
        self.assertEqual(weather.code, 63)
        self.assertEqual(weather.summary, "Moderate rain")
        self.assertEqual(weather.wind_compass, "NW")
        self.assertTrue(weather.is_day)
        self.assertEqual(len(weather.forecast), 2)
        self.assertEqual(weather.forecast[0].precip_chance, 60)

    def test_requires_a_location(self):
        with self.assertRaises(SkycastError):
            api.fetch()

    def test_missing_current_block_raises(self):
        with mock.patch.object(api, "_get", return_value={"daily": {}}):
            with self.assertRaises(SkycastError):
                api.fetch(place=api.Place("Test", 0.0, 0.0))

    def test_imperial_units_are_requested(self):
        params = api._forecast_params(api.Place("Test", 0.0, 0.0), "imperial", 3)
        self.assertEqual(params["temperature_unit"], "fahrenheit")
        self.assertEqual(params["wind_speed_unit"], "mph")

    def test_metric_sends_no_unit_overrides(self):
        params = api._forecast_params(api.Place("Test", 0.0, 0.0), "metric", 3)
        self.assertNotIn("temperature_unit", params)

    def test_forecast_days_are_clamped(self):
        place = api.Place("Test", 0.0, 0.0)
        self.assertEqual(api._forecast_params(place, "metric", 99)["forecast_days"], 7)
        self.assertEqual(api._forecast_params(place, "metric", 0)["forecast_days"], 1)


class DailyTests(unittest.TestCase):
    def test_skips_days_with_missing_temperatures(self):
        payload = {
            "daily": {
                "time": ["2026-08-25", "2026-08-26"],
                "weather_code": [63, 3],
                "temperature_2m_max": [9.0, None],
                "temperature_2m_min": [4.0, 5.0],
                "precipitation_probability_max": [60],
            }
        }
        days = api._daily(payload)
        self.assertEqual(len(days), 1)
        self.assertEqual(days[0].precip_chance, 60)

    def test_empty_payload_is_empty_list(self):
        self.assertEqual(api._daily({}), [])


if __name__ == "__main__":
    unittest.main()
