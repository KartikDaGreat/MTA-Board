# Self-contained 3x5 monospace bitmap font, digits only.
# Row-major, '#' = lit, '.' = unlit. No external font file needed.

GLYPH_WIDTH = 3
GLYPH_HEIGHT = 5

DIGITS = {
    "0": ["###", "#.#", "#.#", "#.#", "###"],
    "1": [".#.", "##.", ".#.", ".#.", "###"],
    "2": ["###", "..#", "###", "#..", "###"],
    "3": ["###", "..#", "###", "..#", "###"],
    "4": ["#.#", "#.#", "###", "..#", "..#"],
    "5": ["###", "#..", "###", "..#", "###"],
    "6": ["###", "#..", "###", "#.#", "###"],
    "7": ["###", "..#", "..#", "..#", "..#"],
    "8": ["###", "#.#", "###", "#.#", "###"],
    "9": ["###", "#.#", "###", "..#", "###"],
    " ": ["...", "...", "...", "...", "..."],
    "-": ["...", "...", "###", "...", "..."],
    ":": ["...", ".#.", "...", ".#.", "..."],
}


def glyph_pixels(char):
    """Return list of (x, y) lit-pixel offsets for a single glyph."""
    rows = DIGITS[char]
    return [(x, y) for y, row in enumerate(rows) for x, c in enumerate(row) if c == "#"]
