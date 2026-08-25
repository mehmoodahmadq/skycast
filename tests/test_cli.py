import io
import json
import unittest
from unittest import mock

from skycast import cli
from skycast.api import SkycastError
from skycast.colors import Painter

from .fixtures import weather


class ParserTests(unittest.TestCase):
    def test_defaults(self):
        args = cli.build_parser().parse_args(["Oslo"])
        self.assertEqual(args.location, ["Oslo"])
        self.assertEqual(args.units, "metric")
        self.assertEqual(args.days, 3)
        self.assertFalse(args.animate)

    def test_multi_word_locations_are_joined(self):
        args = cli.build_parser().parse_args(["San", "Luis", "Obispo"])
        self.assertEqual(cli.resolve_location(args), "San Luis Obispo")

    def test_env_var_is_the_fallback(self):
        args = cli.build_parser().parse_args([])
        with mock.patch.dict("os.environ", {cli.ENV_LOCATION: "Lisbon"}):
            self.assertEqual(cli.resolve_location(args), "Lisbon")

    def test_argument_beats_env_var(self):
        args = cli.build_parser().parse_args(["Porto"])
        with mock.patch.dict("os.environ", {cli.ENV_LOCATION: "Lisbon"}):
            self.assertEqual(cli.resolve_location(args), "Porto")

    def test_colour_flags_are_mutually_exclusive(self):
        with mock.patch("sys.stderr", io.StringIO()):
            with self.assertRaises(SystemExit):
                cli.build_parser().parse_args(["Oslo", "--color", "--no-color"])


class ColorChoiceTests(unittest.TestCase):
    def _args(self, argv):
        return cli.build_parser().parse_args(argv)

    def test_no_color_wins(self):
        self.assertFalse(cli._use_color(self._args(["Oslo", "--no-color"])))

    def test_force_color(self):
        self.assertTrue(cli._use_color(self._args(["Oslo", "--color"])))

    def test_otherwise_asks_the_terminal(self):
        with mock.patch.object(cli.colors, "supported", return_value=False):
            self.assertFalse(cli._use_color(self._args(["Oslo"])))


class MainTests(unittest.TestCase):
    def test_missing_location_exits_two(self):
        stderr = io.StringIO()
        with mock.patch.dict("os.environ", {}, clear=True):
            with mock.patch("sys.stderr", stderr):
                code = cli.main([])
        self.assertEqual(code, 2)
        self.assertIn(cli.ENV_LOCATION, stderr.getvalue())

    def test_network_failure_exits_one(self):
        stderr = io.StringIO()
        with mock.patch.object(cli.api, "fetch", side_effect=SkycastError("boom")):
            with mock.patch("sys.stderr", stderr):
                code = cli.main(["Oslo"])
        self.assertEqual(code, 1)
        self.assertIn("boom", stderr.getvalue())

    def test_renders_a_report(self):
        stdout = io.StringIO()
        with mock.patch.object(cli.api, "fetch", return_value=weather()):
            with mock.patch("sys.stdout", stdout):
                code = cli.main(["Reykjavik", "--no-color"])
        self.assertEqual(code, 0)
        self.assertIn("Reykjavik", stdout.getvalue())
        self.assertIn("Slight rain", stdout.getvalue())

    def test_json_output_is_valid_and_annotated(self):
        stdout = io.StringIO()
        with mock.patch.object(cli.api, "fetch", return_value=weather()):
            with mock.patch("sys.stdout", stdout):
                code = cli.main(["Reykjavik", "--json"])
        self.assertEqual(code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["summary"], "Slight rain")
        self.assertEqual(payload["art_key"], "drizzle")
        self.assertEqual(payload["place"]["name"], "Reykjavik")
        self.assertEqual(payload["forecast"][0]["summary"], "Slight rain")

    def test_here_uses_ip_lookup_instead_of_geocoding(self):
        stdout = io.StringIO()
        current = weather()
        with mock.patch.object(
            cli.api, "locate_by_ip", return_value=current.place
        ) as locate, mock.patch.object(cli.api, "fetch", return_value=current) as fetch:
            with mock.patch("sys.stdout", stdout):
                code = cli.main(["--here", "--no-color"])
        self.assertEqual(code, 0)
        locate.assert_called_once()
        self.assertIs(fetch.call_args.kwargs["place"], current.place)
        self.assertIsNone(fetch.call_args.kwargs["location"])


class AnimateTests(unittest.TestCase):
    def test_stops_after_duration_and_restores_the_cursor(self):
        stream = io.StringIO()
        cli.animate(
            weather(),
            Painter(enabled=False),
            fps=100.0,
            duration=0.0,
            show_forecast=True,
            stream=stream,
        )
        output = stream.getvalue()
        self.assertTrue(output.startswith(cli.HIDE_CURSOR))
        self.assertTrue(output.endswith(cli.SHOW_CURSOR))
        self.assertIn("Reykjavik", output)

    def test_redraws_in_place_on_later_frames(self):
        stream = io.StringIO()
        cli.animate(
            weather(),
            Painter(enabled=False),
            fps=1000.0,
            duration=0.05,
            show_forecast=True,
            stream=stream,
        )
        # A cursor-up sequence means frame two painted over frame one.
        self.assertIn("\033[", stream.getvalue())
        self.assertIn("A", stream.getvalue())


if __name__ == "__main__":
    unittest.main()
