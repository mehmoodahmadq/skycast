import re
import unittest
from dataclasses import replace

from skycast import art, layout
from skycast.colors import Painter

from .fixtures import weather

ANSI = re.compile(r"\033\[[0-9;?]*[a-zA-Z]")


class ReportTests(unittest.TestCase):
    def test_includes_place_summary_and_readings(self):
        text = layout.render(weather(), color=False)
        self.assertIn("Reykjavik, Capital Region, Iceland", text)
        self.assertIn("Slight rain", text)
        self.assertIn("7°C", text)
        self.assertIn("NW", text)
        self.assertIn("81%", text)

    def test_no_ansi_when_colour_disabled(self):
        self.assertIsNone(ANSI.search(layout.render(weather(), color=False)))

    def test_ansi_present_when_colour_enabled(self):
        self.assertIsNotNone(ANSI.search(layout.render(weather(), color=True)))

    def test_line_count_is_stable_across_frames(self):
        current = weather()
        counts = {
            len(layout.report(current, Painter(False), frame=index))
            for index in range(6)
        }
        self.assertEqual(len(counts), 1, "animation would jitter the layout")

    def test_colour_does_not_change_line_count(self):
        current = weather()
        plain = layout.report(current, Painter(False))
        painted = layout.report(current, Painter(True))
        self.assertEqual(len(plain), len(painted))

    def test_art_column_is_aligned(self):
        current = weather()
        lines = layout.report(current, Painter(False))
        # Art occupies rows 2..2+HEIGHT; the detail column starts at a fixed offset.
        offset = len(layout.INDENT) + art.WIDTH + len(layout.GUTTER)
        summary_line = lines[2]
        self.assertTrue(summary_line.startswith(" " * len(layout.INDENT)))
        self.assertEqual(summary_line[offset:], current.summary)

    def test_forecast_can_be_hidden(self):
        current = weather()
        with_rows = layout.report(current, Painter(False), show_forecast=True)
        without = layout.report(current, Painter(False), show_forecast=False)
        self.assertGreater(len(with_rows), len(without))

    def test_forecast_rows_show_highs_and_lows(self):
        text = layout.render(weather(), color=False)
        self.assertIn("9°C/4°C", text)
        self.assertIn("60% precip", text)

    def test_first_forecast_row_is_labelled_today(self):
        rows = layout.forecast_rows(weather().forecast, weather(), Painter(False))
        self.assertTrue(rows[0].strip().startswith("Today"))
        self.assertFalse(rows[1].strip().startswith("Today"))

    def test_forecast_columns_align_across_rows(self):
        current = weather()
        # Widen one row's temperatures so a naive format would drift.
        current.forecast[1] = replace(current.forecast[1], high=100.0, low=5.0)
        rows = layout.forecast_rows(current.forecast, current, Painter(False))
        starts = {row.index("%") for row in rows}
        self.assertEqual(len(starts), 1, f"precip column drifted: {rows!r}")

    def test_handles_weather_without_forecast(self):
        current = weather(days=0)
        lines = layout.report(current, Painter(False))
        self.assertTrue(lines)
        self.assertNotIn("", lines[-1:])


class WeekdayTests(unittest.TestCase):
    def test_parses_iso_date(self):
        self.assertEqual(layout._weekday("2026-08-27"), "Thu")

    def test_passes_through_unparseable(self):
        self.assertEqual(layout._weekday("not-a-date"), "not-a-date")


if __name__ == "__main__":
    unittest.main()
