# skycast

**Real weather. Animated ASCII art. Zero dependencies. No API key.**

```
  Reykjavik, Capital Region, Iceland

       .-.         Moderate rain
      (   ).       7°C  feels 3°C
     (___(__)      wind NW 22 km/h
     ' ' ' ' '     humidity 81%
      ' ' ' '      precip 1.2 mm

  Today 9°C/4°C    Moderate rain         60% precip
  Wed   10°C/5°C   Overcast              20% precip
  Thu   11°C/6°C   Partly cloudy
```

The rain actually falls. The sun actually pulses. Run it with `--animate`.

---

## Install

```bash
pip install skycast
```

Or run it without installing anything:

```bash
pipx run skycast Reykjavik
```

Requires Python 3.9+. That is the entire dependency list — `skycast` is stdlib only.

---

## Use

```bash
skycast Reykjavik              # a place name
skycast San Luis Obispo        # multi-word names need no quotes
skycast 35.01,135.76           # or raw coordinates
skycast Kyoto --animate        # falling rain, drifting snow, pulsing sun
skycast Oslo -u imperial -d 5  # Fahrenheit, five-day forecast
skycast Lima --json            # machine-readable output
```

| Flag | Does |
|------|------|
| `-a`, `--animate` | Redraw in place until Ctrl-C |
| `--fps N` | Animation speed (default 2) |
| `--duration N` | Stop animating after N seconds |
| `-u`, `--units` | `metric` (default) or `imperial` |
| `-d`, `--days` | Forecast days, 1–7 (default 3) |
| `--no-forecast` | Current conditions only |
| `--json` | Print JSON instead of art |
| `--color` / `--no-color` | Override colour detection |
| `--here` | Locate by IP — see [Privacy](#privacy) |

Set `SKYCAST_DEFAULT_LOCATION` so you can just type `skycast`:

```bash
export SKYCAST_DEFAULT_LOCATION="Reykjavik"
```

Colour switches off automatically when output is piped, when `NO_COLOR` is set,
or when `TERM=dumb`.

---

## As a library

```python
import skycast

weather = skycast.fetch("Reykjavik")

print(weather.summary)        # "Moderate rain"
print(weather.temperature)    # 7.4
print(weather.wind_compass)   # "NW"
print(weather.art_key)        # "rain"

print(skycast.render(weather, color=False))
```

`fetch()` returns a frozen `Weather` dataclass. `render()` returns a string;
`report()` returns the same thing as a list of lines, which is what you want if
you are compositing skycast into a bigger TUI.

```python
for frame in range(4):
    print(skycast.render(weather, frame=frame))   # cycle the animation yourself
```

Everything raises `skycast.SkycastError` on failure — bad location, network
trouble, malformed response. There is exactly one exception type to catch.

---

## Where the data comes from

[Open-Meteo](https://open-meteo.com), which is free for non-commercial use and
**requires no API key or signup**. Place names are resolved through Open-Meteo's
geocoding endpoint. Nothing is cached, nothing is stored.

### Privacy

By default skycast sends *only* the location you typed. The `--here` flag is the
one exception: it calls `ipapi.co`, which necessarily sees your IP address in
order to guess where you are. That is why it is an explicit flag and not the
default behaviour.

---

## Adding your own art

Art lives in [`src/skycast/art.py`](src/skycast/art.py) and is deliberately easy
to hack on. Each condition is a list of frames; cycling them animates the scene.

```python
ART["meteor_shower"] = _frames(
    r"""
    \  .  /
      .-.
     (   )
      `-'
    /  '  \
""",
    r"""
     \ . /
      .-.
     (   )
      `-'
     / ' \
""",
)

PALETTES["meteor_shower"] = Palette(
    ["bright_yellow"] * HEIGHT,
    {".": "bright_white", "'": "bright_white"},
)
```

A `Palette` gives a base colour **per line** — weather art is naturally
stratified, with rays on top, the body in the middle and precipitation at the
bottom — plus optional **per-character** overrides applied inside every line.
That covers a rainy grey cloud with blue drops falling out of it without any
per-pixel bookkeeping.

Two rules, both enforced by `tests/test_art.py`:

- every condition needs **at least two frames**, or it cannot animate
- art must be **pure ASCII** — the name of the project is not a suggestion

Frames are padded to a fixed size automatically, so you do not have to count
trailing spaces.

---

## Develop

```bash
git clone https://github.com/mehmoodahmadq/skycast
cd skycast
python -m unittest discover -s tests -t .   # no test dependencies either
PYTHONPATH=src python -m skycast Reykjavik  # run without installing
```

The suite is offline — every network call is mocked — so it runs on a plane.

---

## License

MIT
