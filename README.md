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

The rain actually falls. The snow drifts. The sun pulses and the lightning
flashes. Run it with `--animate`.

---

## Contents

- [Why](#why)
- [Install](#install)
- [Quick start](#quick-start)
- [CLI reference](#cli-reference)
- [Library reference](#library-reference)
- [Weather conditions](#weather-conditions)
- [Adding your own art](#adding-your-own-art)
- [How it works](#how-it-works)
- [Data source and privacy](#data-source-and-privacy)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Contributing](#contributing)
- [License](#license)

---

## Why

Most terminal weather tools want an API key, a config file, and a handful of
dependencies before they will tell you it is raining.

skycast wants a place name.

- **No API key, no signup.** Powered by [Open-Meteo](https://open-meteo.com),
  which is free for non-commercial use.
- **No dependencies.** Standard library only. The install is one wheel.
- **Actually animated.** Twelve hand-drawn conditions, each with multiple
  frames, redrawn in place.
- **A real library, not just a CLI.** Frozen dataclasses, one exception type,
  and a renderer you can compose into your own TUI.
- **Polite by default.** Colour switches itself off when piped. Your IP is
  never sent anywhere unless you explicitly ask for it.

---

## Install

```bash
pip install skycast
```

Run it without installing anything at all:

```bash
pipx run skycast Reykjavik
```

From source:

```bash
git clone https://github.com/mehmoodahmadq/skycast
cd skycast
pip install -e .
```

**Requires Python 3.9 or newer.** That is the complete dependency list.

---

## Quick start

```bash
skycast Reykjavik              # a place name
skycast San Luis Obispo        # multi-word names need no quotes
skycast 35.01,135.76           # or raw "lat,lon" coordinates
skycast Kyoto --animate        # falling rain, drifting snow, pulsing sun
skycast Oslo -u imperial -d 5  # Fahrenheit, five-day forecast
skycast Lima --json            # machine-readable output
skycast --here                 # locate me by IP (see Privacy)
```

Set a default so you can just type `skycast`:

```bash
export SKYCAST_DEFAULT_LOCATION="Reykjavik"
skycast
```

---

## CLI reference

```
skycast [-h] [--here] [-u {metric,imperial}] [-d DAYS] [-a] [--fps FPS]
        [--duration DURATION] [--no-forecast] [--json]
        [--color | --no-color] [--version] [location ...]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `location` | Place name (`Kyoto`, `San Luis Obispo`) or coordinates (`35.01,135.76`). Multiple words are joined, so quotes are optional. Falls back to `$SKYCAST_DEFAULT_LOCATION`. |

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `-a`, `--animate` | off | Redraw the report in place until Ctrl-C |
| `--fps N` | `2` | Animation frames per second |
| `--duration N` | none | Stop animating after N seconds (useful for demos and recordings) |
| `-u`, `--units` | `metric` | `metric` (°C, km/h, mm) or `imperial` (°F, mph, in) |
| `-d`, `--days` | `3` | Forecast days, clamped to 1–7 |
| `--no-forecast` | off | Current conditions only, no forecast strip |
| `--json` | off | Print JSON instead of art |
| `--here` | off | Locate by IP address — see [Privacy](#privacy) |
| `--color` | auto | Force colour on |
| `--no-color` | auto | Force colour off |
| `--version` | | Print version and exit |
| `-h`, `--help` | | Print help and exit |

`--color` and `--no-color` are mutually exclusive.

### Environment variables

| Variable | Effect |
|----------|--------|
| `SKYCAST_DEFAULT_LOCATION` | Used when no location argument is given |
| `NO_COLOR` | If set to anything, disables colour ([no-color.org](https://no-color.org)) |
| `TERM=dumb` | Disables colour |

### Exit codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Could not produce a forecast — unknown place, network failure, bad response |
| `2` | Usage error — no location given and no default set |

This makes skycast safe to use in scripts:

```bash
if skycast "$CITY" --json > weather.json; then
    jq -r .summary weather.json
else
    echo "no weather for $CITY" >&2
fi
```

### Colour behaviour

Colour is enabled only when **all** of these hold:

1. `NO_COLOR` is not set
2. `TERM` is not `dumb`
3. stdout is a TTY

So `skycast Oslo | less` and `skycast Oslo > file.txt` produce clean text
automatically, with no flag needed. `--color` overrides the check when you
want codes through a pipe (for `less -R`, for example).

### JSON output

`--json` prints the full `Weather` record, plus three derived fields
(`summary`, `art_key`, `wind_compass`) so consumers do not have to reimplement
the WMO code table.

```bash
skycast Reykjavik --json -d 1
```

```json
{
  "art_key": "cloudy",
  "code": 3,
  "feels_like": 6.4,
  "forecast": [
    {
      "code": 3,
      "date": "2026-08-25",
      "high": 10.6,
      "low": 7.4,
      "precip_chance": 12,
      "summary": "Overcast"
    }
  ],
  "humidity": 69,
  "is_day": true,
  "observed_at": "2026-08-25T19:30",
  "place": {
    "admin": "Capital Region",
    "country": "Iceland",
    "latitude": 64.13548,
    "longitude": -21.89541,
    "name": "Reykjavik"
  },
  "precipitation": 0.0,
  "summary": "Overcast",
  "temperature": 9.5,
  "units": { "precipitation": "mm", "temperature": "C", "wind": "km/h" },
  "wind_compass": "WSW",
  "wind_direction": 255.0,
  "wind_speed": 11.9
}
```

Keys are sorted, so the output diffs cleanly between runs.

---

## Library reference

```python
import skycast

weather = skycast.fetch("Reykjavik")
print(skycast.render(weather, color=False))
```

Everything below is importable straight from the `skycast` package.

### Fetching

#### `fetch(location=None, system="metric", days=3, place=None, timeout=10.0) -> Weather`

Fetch current conditions plus a short forecast. Pass **either** a `location`
string (place name or `"lat,lon"`) **or** an already-resolved `place`.

```python
skycast.fetch("Kyoto")
skycast.fetch("35.01,135.76", system="imperial", days=7)
skycast.fetch(place=skycast.geocode("Kyoto"))   # reuse a resolved Place
```

`days` is clamped to 1–7. Raises `SkycastError`.

#### `geocode(query, timeout=10.0) -> Place`

Resolve a place name to coordinates. A bare `"lat,lon"` string is parsed
locally and **makes no network request**, so this is cheap when you already
have coordinates. Raises `SkycastError` if nothing matches or coordinates are
out of range.

#### `locate_by_ip(timeout=10.0) -> Place`

Best-effort location from the caller's IP. Sends a request to a third-party
service — see [Privacy](#privacy). Raises `SkycastError`.

### Rendering

#### `render(weather, color=True, frame=0, show_forecast=True) -> str`

Render a complete report as one string.

#### `report(weather, painter=None, frame=0, show_forecast=True) -> list[str]`

The same report as a list of lines, with no trailing newlines. This is what you
want when compositing skycast into a larger TUI. `painter` takes a
`skycast.colors.Painter`; the default is colourless.

```python
from skycast.colors import Painter

lines = skycast.report(weather, Painter(enabled=True), frame=2)
```

Increment `frame` to drive the animation yourself:

```python
for step in range(4):
    print(skycast.render(weather, frame=step))
```

Line count is identical for every `frame` value and whether or not colour is
on — the layout never jitters mid-animation. There are tests pinning both.

### Data model

All models are **frozen dataclasses**.

#### `Weather`

| Field | Type | Notes |
|-------|------|-------|
| `place` | `Place` | Where this is for |
| `code` | `int` | WMO weather code |
| `temperature` | `float` | In `units.temperature` |
| `feels_like` | `float` | Apparent temperature |
| `humidity` | `int` | Percent |
| `wind_speed` | `float` | In `units.wind` |
| `wind_direction` | `float` | Degrees |
| `precipitation` | `float` | In `units.precipitation` |
| `is_day` | `bool` | Drives day/night art |
| `observed_at` | `str` | ISO timestamp in the location's timezone |
| `units` | `Units` | Unit labels |
| `forecast` | `list[Day]` | May be empty |

Derived properties: `summary` (human label), `art_key` (art to draw, day/night
aware), `wind_compass` (`"NW"`).

#### `Place`

`name`, `latitude`, `longitude`, `country`, `admin`. The `label` property joins
them sensibly and drops a redundant admin region — `Place("Kyoto", …,
country="Japan", admin="Kyoto").label` is `"Kyoto, Japan"`, not
`"Kyoto, Kyoto, Japan"`.

#### `Day`

`date` (ISO), `code`, `high`, `low`, `precip_chance` (percent or `None`), plus
a `summary` property.

#### `Units`

`temperature`, `wind`, `precipitation` label strings.
`Units.for_system("imperial")` returns `("F", "mph", "in")`; anything else
returns metric.

### Helpers

| Function | Description |
|----------|-------------|
| `describe(code)` | WMO code → `"Moderate rain"`. Unknown codes give `"Unknown conditions"`, never raise. |
| `art_key(code, is_day=True)` | WMO code → art key, picking the day or night variant |
| `compass(degrees)` | `315` → `"NW"`. Handles wrap-around and negatives. |

### Errors

There is exactly one exception type to catch:

```python
try:
    weather = skycast.fetch("Xyzzyville")
except skycast.SkycastError as exc:
    print("no luck:", exc)
```

`SkycastError` (a `RuntimeError`) covers unknown places, out-of-range
coordinates, DNS and TLS failures, timeouts, HTTP errors, and malformed
responses. Nothing else escapes the library.

---

## Weather conditions

Twelve conditions, each with at least two animation frames, mapped from
[WMO 4677](https://open-meteo.com/en/docs) codes as emitted by Open-Meteo.

| Art key | WMO codes | Meaning |
|---------|-----------|---------|
| `clear` | 0, 1 | Clear / mainly clear, daytime |
| `clear_night` | 0, 1 | Clear / mainly clear, night |
| `partly` | 2 | Partly cloudy, daytime |
| `partly_night` | 2 | Partly cloudy, night |
| `cloudy` | 3 | Overcast |
| `fog` | 45, 48 | Fog, rime fog |
| `drizzle` | 51, 53, 61, 80 | Drizzle, slight rain, slight showers |
| `rain` | 55, 63, 81 | Dense drizzle, moderate rain, showers |
| `heavy_rain` | 65, 82 | Heavy rain, violent showers |
| `sleet` | 56, 57, 66, 67 | Freezing drizzle and freezing rain |
| `snow` | 71, 73, 75, 77, 85, 86 | Snowfall, snow grains, snow showers |
| `thunder` | 95, 96, 99 | Thunderstorms, with or without hail |

Unknown codes fall back to `cloudy` rather than crashing.

See them all at once, without waiting for the right weather to happen
somewhere in the world:

```bash
python examples/gallery.py
```

```
rain  WMO 55, 63, 81
        .-.                .-.
       (   ).             (   ).
      (___(__)           (___(__)
      ' ' ' ' '           ' ' ' '
       ' ' ' '           ' ' ' ' '

thunder  WMO 95, 96, 99
        .-.                .-.
       (   ).             (   ).
      (___(__)           (___(__)
        /_/              /_/ /_/
         /                /   /
```

---

## Adding your own art

Art lives in [`src/skycast/art.py`](src/skycast/art.py) and is deliberately
easy to hack on. Each condition is a list of frames; cycling them animates the
scene.

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

### How colour works

A `Palette` gives a base colour **per line** — weather art is naturally
stratified, with rays on top, the body in the middle and precipitation at the
bottom — plus optional **per-character** overrides applied inside every line.

```python
Palette(["gray"] * HEIGHT, {"'": "bright_blue"})
```

That is a grey cloud with blue drops falling out of it, with no per-pixel
bookkeeping. Available colours are the keys of `skycast.colors.CODES`:

`default`, `gray`, `red`, `green`, `yellow`, `blue`, `magenta`, `cyan`,
`white`, `bright_red`, `bright_yellow`, `bright_blue`, `bright_magenta`,
`bright_cyan`, `bright_white`, `bold`, `dim`.

### The rules

Two of them, both enforced by [`tests/test_art.py`](tests/test_art.py):

- **At least two frames per condition**, or it cannot animate.
- **Pure ASCII.** The name of the project is not a suggestion.

Frames are padded to a fixed 5×15 panel automatically, so you never have to
count trailing spaces. A deliberate blank first line floats the art down the
panel — that is how `cloudy` gets its cloud to hover in the middle.

---

## How it works

```
src/skycast/
  __init__.py   Public API surface and version
  __main__.py   Enables `python -m skycast`
  api.py        Open-Meteo client: geocoding, forecast, IP lookup
  models.py     Frozen dataclasses + the WMO code table
  art.py        ASCII frames and colour palettes
  colors.py     ANSI painter and terminal capability detection
  layout.py     Composes art + readings + forecast into lines
  cli.py        Argument parsing, animation loop, exit codes
```

The dependency direction is one-way: `cli` → `layout` → `art` → `models`, with
`api` depending only on `models`. Nothing imports `cli`.

**Animation** is a redraw, not a screen clear. Each frame writes `\033[<n>A` to
walk the cursor back up, then reprints every line with `\033[K` to clear
trailing residue. The cursor is hidden during animation and restored in a
`finally` block, so Ctrl-C never leaves your terminal without a cursor.

Because the layout is fixed-width, the report has the same line count on every
frame — which is what makes the in-place redraw hold still.

---

## Data source and privacy

Weather and geocoding both come from [Open-Meteo](https://open-meteo.com),
free for non-commercial use and requiring **no API key or signup**. Forecasts
are requested with `timezone=auto`, so the first forecast row is "today" where
the *weather* is, not where you are.

Nothing is cached and nothing is stored. There is no config file.

### Privacy

By default, skycast sends only the location you typed.

`--here` is the single exception: it calls `ipapi.co`, which necessarily sees
your IP address in order to guess your location. That is precisely why it is an
explicit opt-in flag rather than the default behaviour. If you would rather not
use it, pass a location or set `SKYCAST_DEFAULT_LOCATION`.

---

## Development

```bash
git clone https://github.com/mehmoodahmadq/skycast
cd skycast

# Run without installing
PYTHONPATH=src python -m skycast Reykjavik

# Or install editable
python -m venv .venv && .venv/bin/pip install -e .
.venv/bin/skycast Reykjavik
```

### Tests

```bash
python -m unittest discover -s tests -t . -v
```

64 tests, **no test dependencies** and **no network** — every API call is
mocked, so the suite runs on a plane. `pytest` works too if you prefer it;
the tests are plain `unittest.TestCase`, which pytest collects natively.

| File | Covers |
|------|--------|
| `test_api.py` | Payload parsing, coordinate handling, unit params, error paths |
| `test_art.py` | Frame shape, ASCII-only, palette coverage, colour round-trip |
| `test_layout.py` | Column alignment, stable line counts, colour isolation |
| `test_models.py` | WMO mapping, compass, place labels, units |
| `test_cli.py` | Flags, env fallback, exit codes, JSON, animation teardown |

### Linting

```bash
ruff check .
```

### CI

GitHub Actions runs the suite on Python 3.9 through 3.13, lints with Ruff, and
builds the wheel then smoke-tests the installed `skycast` command. See
[`.github/workflows/ci.yml`](.github/workflows/ci.yml).

---

## Troubleshooting

**"no place matched 'X'"** — the geocoder did not recognise the name. Try a
larger nearby city, add a country (`Springfield, Illinois`), or pass
coordinates directly: `skycast 39.80,-89.64`.

**Wrong Springfield.** Geocoding takes the top match. Disambiguate with
coordinates, which are never ambiguous and never hit the network.

**No colour.** Output is probably piped or redirected — that is deliberate.
Force it with `--color`, and check `NO_COLOR` is not set in your shell profile.

**Colour codes as literal text in a pager.** Use `skycast Oslo --color | less -R`.

**Animation flickers or leaves debris.** Your terminal may not support cursor
movement. Use plain `skycast Oslo` without `--animate`.

**"could not reach the weather service".** Network, DNS, or proxy trouble.
skycast makes plain HTTPS requests to `api.open-meteo.com` and
`geocoding-api.open-meteo.com`; both need to be reachable.

**Temperatures look wrong.** Check `--units`. The default is metric.

---

## FAQ

**Does it need an API key?** No. That is the point.

**Does it work offline?** No — it fetches real weather. The *test suite* runs
offline.

**Why Python 3.9?** It is what ships on a lot of machines, macOS included.
There is nothing in skycast that needs anything newer.

**Why not `rich` / `requests`?** Both are excellent and both are dependencies.
A toy weather CLI that pulls in a dependency tree is a toy weather CLI people
uninstall. `urllib` and about forty lines of ANSI handling cover it.

**Can I use it commercially?** skycast is MIT. Open-Meteo's free tier is for
non-commercial use — check [their terms](https://open-meteo.com/en/terms) for
commercial deployments.

**Why is the first forecast row "Today" when it is tomorrow for me?**
Because it is today where the weather is. Forecasts are fetched in the
location's own timezone.

---

## Contributing

Pull requests welcome, especially new art.

1. Keep it dependency-free. That constraint is the product.
2. Art must be pure ASCII with at least two frames.
3. Add a test. The suite is fast and has no setup.
4. Run `python -m unittest discover -s tests -t .` and `ruff check .` first.

---

## License

MIT — see [LICENSE](LICENSE).
