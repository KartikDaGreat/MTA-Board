import time

import art
import bus
import clock
import config
import greet
import layout
import mta
import renderer
import sensor
from cache import TTLCache
from display import Display

subway_cache = TTLCache(mta.fetch_arrivals, config.FEED_POLL_SECONDS)
bus_cache = TTLCache(bus.fetch_arrivals, config.FEED_POLL_SECONDS)

MODES = ["transit", "art", "clock"]
state = {
    "mode_index": 0,
    "auto_cycle": True,
    "last_blip_at": 0.0,
    "display_on": True,
    "flipped": False,
    # Greet is a PREEMPTION, not a MODES entry -- it must never join the
    # auto-cycle or it'd resurface with stale visitor data.
    "greet_active": False,
    "abort_greet": False,
}


def crossfade_to(display, old_frame, new_frame):
    for step in range(1, config.TRANSITION_STEPS + 1):
        alpha = step / config.TRANSITION_STEPS
        display.set_image(renderer.blend(old_frame, new_frame, alpha))
        display.show()
        time.sleep(config.TRANSITION_STEP_SECONDS)


def on_wave():
    """A quick wave (in range and back out before HOLD_SECONDS elapses)
    jumps to the next mode immediately and pauses auto-cycling until the
    sensor's been quiet for AUTO_RESUME_SECONDS. While a greet is showing,
    a wave instead aborts it early -- waving it away -- rather than
    touching mode_index, since greet isn't part of the mode cycle."""
    if state["greet_active"]:
        state["abort_greet"] = True
        return
    state["mode_index"] = (state["mode_index"] + 1) % len(MODES)
    state["auto_cycle"] = False
    state["last_blip_at"] = time.monotonic()


def on_hold():
    """Keeping something within range continuously for HOLD_SECONDS toggles
    the display on/off instead of switching modes."""
    state["display_on"] = not state["display_on"]
    state["last_blip_at"] = time.monotonic()


def on_flip():
    """Keeping something within range continuously out to FLIP_HOLD_SECONDS
    (for viewing the board correctly through a camera/mirror) toggles a
    horizontal mirror of the whole display. on_hold has already fired and
    toggled display_on by this point, so force it back on here -- otherwise
    the flip would be invisible until some other gesture wakes it."""
    state["flipped"] = not state["flipped"]
    state["display_on"] = True
    state["last_blip_at"] = time.monotonic()


def mode_duration(mode):
    if mode == "transit":
        return layout.page_count() * config.PAGE_SECONDS
    return config.MODE_SECONDS


def run_greet(display, saved_frame):
    """Crossfades in over saved_frame, holds for GREET_DURATION_SECONDS (or
    until on_wave sets abort_greet), then crossfades back to it. The caller
    resets mode_started_at right after this returns, the same trick main()
    already uses when waking from display_on=False, so the interruption
    doesn't count against whatever mode's timer was running."""
    greet.enter()
    crossfade_to(display, saved_frame, greet.build_frame())

    started_at = time.monotonic()
    while time.monotonic() - started_at < config.GREET_DURATION_SECONDS:
        if state["abort_greet"]:
            break
        display.set_image(greet.build_frame())
        display.show()
        time.sleep(0.05)

    crossfade_to(display, greet.build_frame(), saved_frame)
    state["greet_active"] = False
    state["abort_greet"] = False


def build_mode_frame(mode, arrivals, page):
    if mode == "art":
        return art.build_frame()
    if mode == "clock":
        return clock.build_frame()
    return layout.build_frame(arrivals, page)


def main():
    display = Display()
    sensor.on_gesture(on_wave, on_hold, on_flip)

    page = 0
    next_page_at = time.monotonic() + config.PAGE_SECONDS
    next_greet_poll_at = time.monotonic() + config.GREET_POLL_SECONDS
    last_greet_mtime = greet.file_mtime()
    current_mode = MODES[state["mode_index"]]
    mode_started_at = time.monotonic()
    display_was_on = True
    display_flipped = False

    arrivals = {**subway_cache.get(), **bus_cache.get()}
    current_frame = layout.build_frame(arrivals, page)
    display.set_image(current_frame)
    display.show()

    try:
        while True:
            now = time.monotonic()

            # Poll for a new visitor at most every GREET_POLL_SECONDS -- this
            # loop is also driving 512 pixels, so the file isn't read every
            # iteration, only mtime-checked on this cadence.
            if now >= next_greet_poll_at:
                next_greet_poll_at = now + config.GREET_POLL_SECONDS
                mtime = greet.file_mtime()
                if mtime is not None and mtime != last_greet_mtime:
                    last_greet_mtime = mtime
                    # A panel deliberately held off (a hand over the sensor)
                    # shouldn't wake itself up just because a greet came in.
                    if state["display_on"]:
                        state["greet_active"] = True

            if state["greet_active"]:
                run_greet(display, current_frame)
                mode_started_at = time.monotonic()
                current_frame = build_mode_frame(current_mode, arrivals, page)
                display.set_image(current_frame)
                display.show()
                continue

            if state["display_on"] != display_was_on:
                display_was_on = state["display_on"]
                if not display_was_on:
                    display.clear()
                else:
                    # Redraw immediately on wake instead of waiting for the
                    # next natural refresh, and don't count the off period
                    # toward the current mode's on-screen time.
                    mode_started_at = now
                    current_frame = build_mode_frame(current_mode, arrivals, page)
                    display.set_image(current_frame)
                    display.show()

            if state["flipped"] != display_flipped:
                display_flipped = state["flipped"]
                display.set_flipped(display_flipped)
                if state["display_on"]:
                    current_frame = build_mode_frame(current_mode, arrivals, page)
                    display.set_image(current_frame)
                    display.show()

            if not state["display_on"]:
                time.sleep(0.1)
                continue

            # Resume default auto-cycling once the sensor's been quiet a while.
            if not state["auto_cycle"] and now - state["last_blip_at"] >= config.AUTO_RESUME_SECONDS:
                state["auto_cycle"] = True
                mode_started_at = now

            # Default behavior: cycle through every mode on its own.
            if state["auto_cycle"] and now - mode_started_at >= mode_duration(current_mode):
                state["mode_index"] = (state["mode_index"] + 1) % len(MODES)
                mode_started_at = now

            new_mode = MODES[state["mode_index"]]
            if new_mode != current_mode:
                current_mode = new_mode
                mode_started_at = now
                if current_mode == "art":
                    art.enter()
                elif current_mode == "transit":
                    next_page_at = now + config.PAGE_SECONDS
                new_frame = build_mode_frame(current_mode, arrivals, page)
                crossfade_to(display, current_frame, new_frame)
                current_frame = new_frame

            if current_mode in ("art", "clock"):
                current_frame = build_mode_frame(current_mode, arrivals, page)
                display.set_image(current_frame)
                display.show()
                time.sleep(0.05 if current_mode == "art" else 0.5)
                continue

            arrivals = {**subway_cache.get(), **bus_cache.get()}

            if now >= next_page_at:
                page += 1
                next_page_at = now + config.PAGE_SECONDS
                new_frame = layout.build_frame(arrivals, page)
                crossfade_to(display, current_frame, new_frame)
                current_frame = new_frame
            else:
                current_frame = layout.build_frame(arrivals, page)
                display.set_image(current_frame)
                display.show()

            time.sleep(0.5)
    except KeyboardInterrupt:
        display.clear()


if __name__ == "__main__":
    main()
