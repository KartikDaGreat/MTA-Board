import math
import random
import time

from PIL import Image, ImageDraw

import config

# Brightness used to be dimmed here specifically; now display.py applies
# config.COLOR_BRIGHTNESS to every mode uniformly, so these effects render
# at full value/intensity and get dimmed once, downstream.

_CUBE_VERTICES = [
    (-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
    (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1),
]

# Face vertex loops (consistent winding) paired with the classic Rubik's
# cube color scheme: white/yellow and blue/green and orange/red are always
# on opposite faces.
_CUBE_FACES = [
    ((0, 1, 2, 3), (0, 158, 71)),      # front  (z=-1) green
    ((5, 4, 7, 6), (0, 81, 186)),      # back   (z=+1) blue
    ((4, 0, 3, 7), (255, 88, 0)),      # left   (x=-1) orange
    ((1, 5, 6, 2), (210, 0, 0)),       # right  (x=+1) red (no blue channel -- avoids a pink cast when dimmed)
    ((4, 5, 1, 0), (255, 255, 255)),   # top    (y=-1) white
    ((3, 2, 6, 7), (255, 213, 0)),     # bottom (y=+1) yellow
]


# Calm, muted palette the whole panel slowly breathes between -- deliberately
# desaturated and slow instead of a full-saturation rainbow cycle, which read
# as a frantic "swirl" at speed.
_BREATHE_PALETTE = [
    (40, 60, 90),   # dusty blue
    (60, 45, 80),   # soft violet
    (80, 55, 45),   # warm amber
    (45, 70, 65),   # sage teal
]
_BREATHE_SECONDS_PER_COLOR = 6.0


def _breathe_frame(t):
    n = len(_BREATHE_PALETTE)
    pos = (t / _BREATHE_SECONDS_PER_COLOR) % n
    i = int(pos)
    frac = pos - i
    # Smoothstep easing so the color lingers near each palette entry instead
    # of drifting through the midpoint at constant speed.
    frac = frac * frac * (3 - 2 * frac)
    c1, c2 = _BREATHE_PALETTE[i], _BREATHE_PALETTE[(i + 1) % n]
    color = tuple(int(a + (b - a) * frac) for a, b in zip(c1, c2))
    return Image.new("RGB", (config.DISPLAY_WIDTH, config.DISPLAY_HEIGHT), color)


_NUM_STARS = 40
_NIGHT_SKY = (5, 8, 20)
_STAR_COLOR = (255, 220, 160)
# Fixed seed so star positions are stable across frames/runs -- only their
# brightness animates, which is what makes it read as "twinkling" rather
# than noise.
_star_rng = random.Random(7)
_STARS = [
    (
        _star_rng.randrange(config.DISPLAY_WIDTH),
        _star_rng.randrange(config.DISPLAY_HEIGHT),
        _star_rng.uniform(0, math.tau),
        _star_rng.uniform(0.6, 1.4),
    )
    for _ in range(_NUM_STARS)
]


def _twinkle_frame(t):
    image = Image.new("RGB", (config.DISPLAY_WIDTH, config.DISPLAY_HEIGHT), _NIGHT_SKY)
    px = image.load()
    for x, y, phase, speed in _STARS:
        brightness = (math.sin(t * speed + phase) + 1) / 2
        px[x, y] = tuple(int(sky + (star - sky) * brightness) for sky, star in zip(_NIGHT_SKY, _STAR_COLOR))
    return image


def _rotate(v, ax, ay):
    x, y, z = v
    y, z = y * math.cos(ax) - z * math.sin(ax), y * math.sin(ax) + z * math.cos(ax)
    x, z = x * math.cos(ay) + z * math.sin(ay), -x * math.sin(ay) + z * math.cos(ay)
    return x, y, z


def _project(v, scale, supersample=1):
    x, y, z = v
    distance = 4
    factor = distance / (distance + z)
    cx = config.DISPLAY_WIDTH * supersample / 2
    cy = config.DISPLAY_HEIGHT * supersample / 2
    return cx + x * factor * scale, cy + y * factor * scale


_SUPERSAMPLE = 4   # render this many times larger, then downscale -- turns
                    # hard jagged polygon edges into smoothly anti-aliased ones


def _cube_frame(t):
    big_size = (config.DISPLAY_WIDTH * _SUPERSAMPLE, config.DISPLAY_HEIGHT * _SUPERSAMPLE)
    image = Image.new("RGB", big_size)
    draw = ImageDraw.Draw(image)

    # Fixed tilt + steady single-axis spin reads as a much smoother, more
    # legible rotation at this resolution than tumbling on two axes at once.
    ax, ay = 0.6, t * 1.0
    rotated = [_rotate(v, ax, ay) for v in _CUBE_VERTICES]
    # scale shrunk from 5.5 -> 4.2 so corners stay inside the frame at all
    # rotation angles instead of getting cropped at the edges
    projected = [_project(v, scale=4.2 * _SUPERSAMPLE, supersample=_SUPERSAMPLE) for v in rotated]

    faces = []
    for indices, color in _CUBE_FACES:
        depth = sum(rotated[i][2] for i in indices) / 4
        points = [projected[i] for i in indices]
        faces.append((depth, points, color))

    # Painter's algorithm: farthest face (largest z) drawn first, nearer
    # faces drawn on top -- correct occlusion for a convex solid like a cube.
    faces.sort(key=lambda f: f[0], reverse=True)
    for _, points, color in faces:
        draw.polygon(points, fill=color)

    return image.resize((config.DISPLAY_WIDTH, config.DISPLAY_HEIGHT), Image.LANCZOS)


_EFFECTS = [_breathe_frame, _cube_frame, _twinkle_frame]

_state = {"effect_index": 0, "start": time.monotonic()}


def enter():
    """Call once when switching into art mode -- rotates to the next visual
    so it's different each time the sensor blip brings you here."""
    _state["effect_index"] = (_state["effect_index"] + 1) % len(_EFFECTS)
    _state["start"] = time.monotonic()


def build_frame():
    t = time.monotonic() - _state["start"]
    return _EFFECTS[_state["effect_index"]](t)
