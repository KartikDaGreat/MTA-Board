from PIL import Image

import config
from fonts.font_3x5 import GLYPH_HEIGHT, GLYPH_WIDTH, glyph_pixels

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

MARGIN = 1               # empty column left untouched on both left and right edges
BLOB_SIZE = 6            # 6x6 colored blob with a plain white arrow
GAP_LABEL_BLOB = 2
GAP_BLOB_ARRIVALS = 2
SEPARATOR_GAP = 4        # space between two arrival numbers, incl. the divider line
LABEL_Y_OFFSET = (BLOB_SIZE - GLYPH_HEIGHT) // 2  # vertically centers digits against the taller blob

# Thin direction arrows in a 6x6 blob. "down" = downtown/inbound, "up" = the
# opposite (uptown/northbound, or westbound for buses).
ARROWS = {
    "down": [
        "......",
        "#####.",
        ".###..",
        "..#...",
        "......",
        "......",
    ],
    "up": [
        "......",
        "......",
        "..#...",
        ".###..",
        "#####.",
        "......",
    ],
}


def new_frame():
    return Image.new("RGB", (config.DISPLAY_WIDTH, config.DISPLAY_HEIGHT), BLACK)


def blend(frame_a, frame_b, alpha):
    """Crossfade between two frames; alpha 0 = frame_a, 1 = frame_b."""
    return Image.blend(frame_a, frame_b, alpha)


def put_pixel(image, x, y, color):
    if MARGIN <= x < config.DISPLAY_WIDTH - MARGIN and 0 <= y < config.DISPLAY_HEIGHT:
        image.load()[x, y] = color


def draw_digits(image, text, x, y, color, spacing=1):
    """Draw a string of digits (3x5 glyphs) with top-left at (x, y). spacing=0
    packs characters edge-to-edge -- glyphs stay full size, just tighter."""
    cursor_x = x
    for char in text:
        for gx, gy in glyph_pixels(char):
            put_pixel(image, cursor_x + gx, y + gy, color)
        cursor_x += GLYPH_WIDTH + spacing


def digits_width(text, spacing=1):
    return len(text) * (GLYPH_WIDTH + spacing) - spacing if text else 0


def draw_separator(image, x, y, color):
    """Vertical line, BLOB_SIZE tall, marking a boundary between two values."""
    for dy in range(BLOB_SIZE):
        put_pixel(image, x, y + dy, color)


def draw_transit_blob(image, x, y, color, direction):
    """route_color-filled BLOB_SIZE square with a white direction arrow on top."""
    for dy in range(BLOB_SIZE):
        for dx in range(BLOB_SIZE):
            put_pixel(image, x + dx, y + dy, color)
    for dy, row in enumerate(ARROWS[direction]):
        for dx, c in enumerate(row):
            if c == "#":
                put_pixel(image, x + dx, y + dy, WHITE)


def _fit_arrivals(cursor_x, right_bound, arrival_minutes):
    """Returns (formatted arrival strings that fit, cursor_x after the last one)."""
    texts = []
    running = cursor_x
    for minutes in arrival_minutes:
        text = str(max(minutes, 0))
        needed = digits_width(text) + (SEPARATOR_GAP if texts else 0)
        if running + needed > right_bound:
            break
        running += needed
        texts.append(text)
    return texts, running


def draw_route_row(image, y, route, route_color, direction, arrival_minutes):
    """One row: white route label, colored direction blob, then as many
    countdowns as fit, separated by route-colored divider lines. y is the
    top of the BLOB_SIZE-tall row; digit text is centered against it.

    The route label's digit spacing is chosen adaptively: normal spacing is
    used unless packing the label tighter (no inter-digit gap) actually
    frees enough room to fit an additional arrival -- so a route like "60"
    only compacts when it buys something, and multi-digit labels don't
    stay needlessly cramped when there's nothing to gain from it."""
    text_y = y + LABEL_Y_OFFSET
    right_bound = config.DISPLAY_WIDTH - MARGIN

    def layout_with(label_spacing, label_gap, blob_gap):
        cursor_x = MARGIN + digits_width(route, spacing=label_spacing) + label_gap + BLOB_SIZE + blob_gap
        texts, running = _fit_arrivals(cursor_x, right_bound, arrival_minutes)
        return label_spacing, label_gap, blob_gap, cursor_x, texts, running

    normal = layout_with(1, GAP_LABEL_BLOB, GAP_BLOB_ARRIVALS)
    compact = layout_with(0, 1, 1)
    label_spacing, label_gap, blob_gap, cursor_x, texts, running = (
        compact if len(compact[4]) > len(normal[4]) else normal
    )

    draw_digits(image, route, MARGIN, text_y, WHITE, spacing=label_spacing)
    draw_transit_blob(
        image, MARGIN + digits_width(route, spacing=label_spacing) + label_gap, y, route_color, direction
    )

    if not arrival_minutes:
        draw_digits(image, "-", cursor_x, text_y, WHITE)
        return

    # If what's left (e.g. from short single-digit minutes) leaves unused
    # width, spend a bit of it as extra breathing room between the numbers
    # instead of leaving it as dead space after the last digit.
    gaps = len(texts) - 1
    extra_gap = min(2, (right_bound - running) // gaps) if gaps > 0 else 0

    for i, text in enumerate(texts):
        if i > 0:
            gap = SEPARATOR_GAP + extra_gap
            draw_separator(image, cursor_x + gap // 2, y, route_color)
            cursor_x += gap
        draw_digits(image, text, cursor_x, text_y, WHITE)
        cursor_x += digits_width(text)
