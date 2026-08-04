from datetime import datetime
from zoneinfo import ZoneInfo

import config
import renderer
from fonts.font_4x6 import GLYPH_HEIGHT, GLYPH_WIDTH, glyph_pixels

NYC_TZ = ZoneInfo("America/New_York")
IST_TZ = ZoneInfo("Asia/Kolkata")

NYC_COLOR = (0, 120, 200)   # top panel: cool blue
IST_COLOR = (200, 90, 0)    # bottom panel: warm orange

PANEL_HEIGHT = config.DISPLAY_HEIGHT // config.NUM_PANELS
TEXT_Y_OFFSET = (PANEL_HEIGHT - GLYPH_HEIGHT) // 2


def _text_width(text):
    return len(text) * (GLYPH_WIDTH + 1) - 1 if text else 0


def _draw_text(image, text, x, y, color):
    cursor_x = x
    for char in text:
        for gx, gy in glyph_pixels(char):
            renderer.put_pixel(image, cursor_x + gx, y + gy, color)
        cursor_x += GLYPH_WIDTH + 1


def _format(tz):
    """e.g. '7:45P' -- 12-hour, no leading zero, single-letter AM/PM suffix
    (fitting a full 'AM'/'PM' at this font size would overflow the 32px width)."""
    now = datetime.now(tz)
    hour_minute = now.strftime("%I:%M").lstrip("0")
    suffix = now.strftime("%p")[0]
    return f"{hour_minute}{suffix}"


def build_frame():
    image = renderer.new_frame()
    for panel_index, (tz, color) in enumerate([(NYC_TZ, NYC_COLOR), (IST_TZ, IST_COLOR)]):
        text = _format(tz)
        width = _text_width(text)
        x = (config.DISPLAY_WIDTH - width) // 2
        y = panel_index * PANEL_HEIGHT + TEXT_Y_OFFSET
        _draw_text(image, text, x, y, color)
    return image
