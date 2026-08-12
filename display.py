import board
import neopixel
from PIL import ImageEnhance, ImageOps

import config


def xy_to_index(x, y):
    """Map a logical (x, y) pixel -- x in [0, DISPLAY_WIDTH), y in [0, DISPLAY_HEIGHT) --
    to the physical index in the DIN->DOUT chained strip.

    Verified empirically (calibrate.py, 2026-07-11): each panel is wired
    column-major serpentine -- column 0 runs top->bottom (indices 0-7),
    column 1 bottom->top (indices 8-15), column 2 top->bottom again, etc.
    Panels are stacked with Panel 1 (the DIN end of the chain) at
    config.PANEL1_POSITION (confirmed "top").
    """
    panel_index, row_in_panel = divmod(y, config.PANEL_ROWS)
    if config.PANEL1_POSITION == "bottom":
        panel_index = config.NUM_PANELS - 1 - panel_index

    col_y = row_in_panel
    if config.SERPENTINE_COLUMNS and x % 2 == 1:
        col_y = config.PANEL_ROWS - 1 - row_in_panel

    panel_offset = panel_index * config.PANEL_ROWS * config.PANEL_COLS
    return panel_offset + x * config.PANEL_ROWS + col_y


class Display:
    def __init__(self):
        self.pixels = neopixel.NeoPixel(
            getattr(board, config.GPIO_PIN),
            config.NUM_PIXELS,
            brightness=config.BRIGHTNESS,
            auto_write=False,
        )
        self.flipped = False

    def set_flipped(self, flipped):
        self.flipped = flipped

    def set_image(self, image):
        """image: a PIL Image in RGB mode, sized (DISPLAY_WIDTH, DISPLAY_HEIGHT).
        Every frame (transit, clock, art) passes through here, so scaling by
        COLOR_BRIGHTNESS -- and mirroring when self.flipped -- here applies
        uniformly to all of them."""
        dimmed = ImageEnhance.Brightness(image).enhance(config.COLOR_BRIGHTNESS)
        if self.flipped:
            dimmed = ImageOps.mirror(dimmed)
        px = dimmed.load()
        for y in range(config.DISPLAY_HEIGHT):
            for x in range(config.DISPLAY_WIDTH):
                self.pixels[xy_to_index(x, y)] = px[x, y]

    def show(self):
        self.pixels.show()

    def clear(self):
        self.pixels.fill((0, 0, 0))
        self.pixels.show()
