"""Run with sudo. Two modes to figure out / verify the physical pixel mapping.

    sudo python3 calibrate.py raw       # lights raw indices 0..N one at a time
    sudo python3 calibrate.py mapped    # walks logical (x, y) via display.xy_to_index

Use "raw" first to watch the actual physical order LEDs light up in, and
compare it against the assumptions in display.xy_to_index (serpentine rows,
Panel 1 position). Adjust config.SERPENTINE_ROWS / config.PANEL1_POSITION
as needed, then confirm with "mapped" -- a dot should sweep left-to-right,
top-to-bottom, with no jumps.
"""
import sys
import time

import board
import neopixel

import config
import display

pixels = neopixel.NeoPixel(
    getattr(board, config.GPIO_PIN),
    config.NUM_PIXELS,
    brightness=config.BRIGHTNESS,
    auto_write=False,
)


def run_raw(delay=0.05):
    for i in range(config.NUM_PIXELS):
        pixels.fill((0, 0, 0))
        pixels[i] = (255, 255, 255)
        pixels.show()
        print(f"raw index {i}")
        time.sleep(delay)
    pixels.fill((0, 0, 0))
    pixels.show()


def run_mapped(delay=0.05):
    for y in range(config.DISPLAY_HEIGHT):
        for x in range(config.DISPLAY_WIDTH):
            pixels.fill((0, 0, 0))
            pixels[display.xy_to_index(x, y)] = (0, 255, 0)
            pixels.show()
            print(f"(x={x}, y={y})")
            time.sleep(delay)
    pixels.fill((0, 0, 0))
    pixels.show()


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "raw"
    if mode == "raw":
        run_raw()
    elif mode == "mapped":
        run_mapped()
    else:
        print("usage: calibrate.py [raw|mapped]")
