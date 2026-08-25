import unittest

from skycast import art
from skycast.models import WMO_CODES, Place, Units, art_key, compass, describe

from .fixtures import weather


class CodeTests(unittest.TestCase):
    def test_known_code_describes(self):
        self.assertEqual(describe(95), "Thunderstorm")

    def test_unknown_code_is_not_fatal(self):
        self.assertEqual(describe(4242), "Unknown conditions")
        self.assertEqual(art_key(4242), "cloudy")

    def test_every_mapped_art_key_exists(self):
        for code, (_, day, night) in WMO_CODES.items():
            with self.subTest(code=code):
                self.assertIn(day, art.ART)
                self.assertIn(night, art.ART)

    def test_day_and_night_variants_differ_for_clear_sky(self):
        self.assertEqual(art_key(0, is_day=True), "clear")
        self.assertEqual(art_key(0, is_day=False), "clear_night")

    def test_rain_looks_the_same_at_night(self):
        self.assertEqual(art_key(63, is_day=True), art_key(63, is_day=False))


class CompassTests(unittest.TestCase):
    def test_cardinals(self):
        self.assertEqual(compass(0), "N")
        self.assertEqual(compass(90), "E")
        self.assertEqual(compass(180), "S")
        self.assertEqual(compass(270), "W")

    def test_wraps_past_360(self):
        self.assertEqual(compass(360), "N")
        self.assertEqual(compass(-90), "W")

    def test_intercardinal(self):
        self.assertEqual(compass(315), "NW")
        self.assertEqual(compass(22.5), "NNE")


class PlaceTests(unittest.TestCase):
    def test_label_joins_parts(self):
        place = Place("Kyoto", 35.0, 135.8, country="Japan", admin="Kyoto")
        self.assertEqual(place.label, "Kyoto, Japan")

    def test_label_keeps_distinct_admin(self):
        place = Place("Springfield", 0.0, 0.0, country="USA", admin="Illinois")
        self.assertEqual(place.label, "Springfield, Illinois, USA")

    def test_label_without_country(self):
        self.assertEqual(Place("Nowhere", 0.0, 0.0).label, "Nowhere")


class UnitTests(unittest.TestCase):
    def test_imperial(self):
        units = Units.for_system("imperial")
        self.assertEqual((units.temperature, units.wind), ("F", "mph"))

    def test_metric_is_the_default(self):
        self.assertEqual(Units.for_system("metric"), Units())
        self.assertEqual(Units.for_system("nonsense"), Units())


class WeatherTests(unittest.TestCase):
    def test_derived_properties(self):
        current = weather(code=61)
        self.assertEqual(current.summary, "Slight rain")
        self.assertEqual(current.art_key, "drizzle")
        self.assertEqual(current.wind_compass, "NW")


if __name__ == "__main__":
    unittest.main()
