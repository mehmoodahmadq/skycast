import unittest

from skycast import art
from skycast.colors import Painter


class ArtShapeTests(unittest.TestCase):
    def test_every_condition_has_at_least_two_frames(self):
        for key, frames in art.ART.items():
            with self.subTest(key=key):
                self.assertGreaterEqual(len(frames), 2, "%s cannot animate" % key)

    def test_frames_are_normalised(self):
        for key, frames in art.ART.items():
            for index, frame in enumerate(frames):
                with self.subTest(key=key, frame=index):
                    self.assertEqual(len(frame), art.HEIGHT)
                    for line in frame:
                        self.assertEqual(len(line), art.WIDTH)

    def test_art_is_pure_ascii(self):
        for key, frames in art.ART.items():
            for frame in frames:
                with self.subTest(key=key):
                    "".join(frame).encode("ascii")

    def test_every_condition_has_a_palette(self):
        self.assertEqual(set(art.ART), set(art.PALETTES))

    def test_palettes_cover_every_line(self):
        for key, palette in art.PALETTES.items():
            with self.subTest(key=key):
                self.assertEqual(len(palette.lines), art.HEIGHT)


class PaintTests(unittest.TestCase):
    def test_disabled_painter_returns_raw_art(self):
        painter = Painter(enabled=False)
        for key in art.ART:
            with self.subTest(key=key):
                self.assertEqual(art.paint(key, 0, painter), art.frame(key, 0))

    def test_enabled_painter_preserves_visible_text(self):
        painter = Painter(enabled=True)
        for key in art.ART:
            painted = art.paint(key, 1, painter)
            plain = art.frame(key, 1)
            for line, expected in zip(painted, plain):
                with self.subTest(key=key):
                    self.assertEqual(_strip_ansi(line), expected)

    def test_frame_index_cycles(self):
        frames = art.frames("rain")
        self.assertEqual(art.frame("rain", len(frames)), frames[0])

    def test_unknown_key_falls_back(self):
        self.assertEqual(art.frames("blizzard_of_frogs"), art.ART["cloudy"])


def _strip_ansi(text):
    import re

    return re.sub(r"\033\[[0-9;?]*[a-zA-Z]", "", text)


if __name__ == "__main__":
    unittest.main()
