"""Greet: a PREEMPTION triggered by main.py when the website's /greet POST
writes a newer greet.json, not a fourth entry in MODES -- it must never
join the auto-cycle or it'd resurface with stale data. main.py drives this
the same way it drives art.py: enter() resets the clock, build_frame() is
called every tick.

Phase 1 (first ~3s): both panels flash. Phase 2 (remaining ~57s): the top
panel scrolls "CITY, REGION, COUNTRY - ORG" and the bottom panel shows the
static local NYC time, reusing clock.py's own formatting/drawing so the
digits match what clock mode normally shows.
"""
import json
import os
import time

from PIL import Image

import config
import renderer
from clock import NYC_TZ, PANEL_HEIGHT, TEXT_Y_OFFSET, _draw_text, _format, _text_width

# Gap (in px) between one marquee loop and the next, so the text doesn't
# immediately re-enter from the right the instant it exits on the left.
LOOP_GAP = config.DISPLAY_WIDTH

# Fixed per-pulse timing (not configurable -- GREET_FLASH_COUNT is the only
# knob config.py exposes for this) works out to ~3s for the default count of 3.
_PULSE_SECONDS = 0.5
_FLASH_SECONDS = config.GREET_FLASH_COUNT * 2 * _PULSE_SECONDS

_state = {"start": 0.0, "payload": None}


def file_mtime():
    """Last-modified time of the greet file, or None if the website hasn't
    POSTed yet. main.py polls this every ~2s to detect a new visitor."""
    try:
        return os.path.getmtime(config.GREET_FILE)
    except FileNotFoundError:
        return None


def _load_payload():
    with open(config.GREET_FILE) as f:
        data = json.load(f)
    return {key: data.get(key, "") for key in ("city", "region", "country", "org")}


def _marquee_text(payload):
    """'CITY, REGION, COUNTRY - ORG', dropping any empty field instead of
    leaving behind a stray ', ' or ' - '."""
    location = ", ".join(part for part in (payload["city"], payload["region"], payload["country"]) if part)
    if payload["org"]:
        return f"{location} - {payload['org']}" if location else payload["org"]
    return location


def enter():
    """Call once when a new greet is triggered -- loads the payload and
    resets the flash/scroll clock, same pattern as art.enter()."""
    _state["payload"] = _load_payload()
    _state["start"] = time.monotonic()


def _flash_frame(t):
    lit = int(t // _PULSE_SECONDS) % 2 == 0
    color = config.GREET_COLOR if lit else renderer.BLACK
    return Image.new("RGB", (config.DISPLAY_WIDTH, config.DISPLAY_HEIGHT), color)


def _scroll_frame(t):
    image = renderer.new_frame()
    payload = _state["payload"]

    text = _marquee_text(payload)
    if text:
        width = _text_width(text)
        cycle = width + config.DISPLAY_WIDTH + LOOP_GAP
        scroll_elapsed = t - _FLASH_SECONDS
        x = config.DISPLAY_WIDTH - int(scroll_elapsed * config.GREET_SCROLL_PIXELS_PER_SECOND) % cycle
        _draw_text(image, text, x, TEXT_Y_OFFSET, config.GREET_COLOR)

    clock_text = _format(NYC_TZ)
    clock_x = (config.DISPLAY_WIDTH - _text_width(clock_text)) // 2
    _draw_text(image, clock_text, clock_x, PANEL_HEIGHT + TEXT_Y_OFFSET, config.GREET_COLOR)

    return image


def build_frame():
    t = time.monotonic() - _state["start"]
    if t < _FLASH_SECONDS:
        return _flash_frame(t)
    return _scroll_frame(t)
