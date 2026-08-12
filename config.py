# --- Panel / display geometry ---
PANEL_ROWS = 8          # rows per physical panel
PANEL_COLS = 32         # cols per physical panel
NUM_PANELS = 2          # stacked vertically
DISPLAY_WIDTH = PANEL_COLS
DISPLAY_HEIGHT = PANEL_ROWS * NUM_PANELS   # 16
NUM_PIXELS = DISPLAY_WIDTH * DISPLAY_HEIGHT

# Pixel-mapping flags. Verified empirically via calibrate.py on 2026-07-11:
# each panel is wired column-major serpentine (column 0 top->bottom,
# column 1 bottom->top, alternating), NOT row-major as originally assumed.
SERPENTINE_COLUMNS = True
PANEL1_POSITION = "top"     # "top" or "bottom": where Panel 1 (DIN end) physically sits -- confirmed "top"

# --- LED strip ---
GPIO_PIN = "D18"      # must be GPIO18 (PWM0) for WS2812B timing
BRIGHTNESS = 0.1       # strip-level scalar (power/eye-comfort), applies to every mode
COLOR_BRIGHTNESS = 0.3  # applied to every rendered frame before it reaches the strip --
                        # this used to be art-mode-only; now every mode matches it

# --- MTA subway ---
# Numbered lines (1-7, S) share one GTFS-Realtime feed. No API key required.
SUBWAY_FEED_URL = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs"

# GTFS stop IDs near 125 St & Madison Ave, verified against MTA's official
# Stations.csv (http://web.mta.info/developers/data/nyct/subway/Stations.csv):
#   621 = 125 St (Lexington Av line: 4, 5, 6)
#   225 = 125 St (Lenox Av line: 2, 3)
# "S" suffix = southbound = downtown, per GTFS-RT direction convention.
MTA_GREEN = (0, 80, 30)    # darkened from official 4/5/6 bullet color (0,147,60)
MTA_RED = (139, 0, 0)      # deepened from official 2/3 bullet color (238,53,46)
BUS_BLUE = (0, 0, 139)     # dark blue for all bus routes

# "arrow" ("down"/"up") picks which direction icon renderer.py draws in the
# route's colored blob -- unrelated to the GTFS "direction" (N/S) field below.
ROUTES = [
    {"route": "4", "stop_id": "621", "direction": "S", "color": MTA_GREEN, "arrow": "down"},
    {"route": "5", "stop_id": "621", "direction": "S", "color": MTA_GREEN, "arrow": "down"},
    {"route": "6", "stop_id": "621", "direction": "S", "color": MTA_GREEN, "arrow": "down"},
    {"route": "2", "stop_id": "225", "direction": "S", "color": MTA_RED, "arrow": "down"},
    {"route": "3", "stop_id": "225", "direction": "S", "color": MTA_RED, "arrow": "down"},
]

ARRIVALS_PER_ROUTE = 3      # how many upcoming arrivals to keep per route -- rows that
                            # don't have room simply show fewer, so this is safe to raise
FEED_POLL_SECONDS = 20      # MTA feed itself refreshes roughly every 30s
PAGE_SECONDS = 4            # how long each page of routes is shown

# --- Mode cycling ---
# By default the board auto-cycles through every mode (all transit pages,
# then art, then clock, repeat). A sensor blip jumps to the next mode
# immediately and pauses auto-cycling until the sensor's been quiet for
# AUTO_RESUME_SECONDS, so manual browsing doesn't get interrupted mid-look.
MODE_SECONDS = 20           # how long art/clock is shown before auto-advancing
AUTO_RESUME_SECONDS = 120   # 2 minutes of no blips before auto-cycling resumes

TRANSITION_STEPS = 8        # crossfade steps between pages
TRANSITION_STEP_SECONDS = 0.03  # ~240ms total transition

# --- Buses ---
# Bus real-time data is a SEPARATE feed/account system from the subway one
# above and requires a free API key: register at
# https://register.developer.obanyc.com then set the env var below (or
# paste the key directly into BUS_API_KEY).
import os

BUS_API_KEY = os.environ.get("MTA_BUS_API_KEY", "")
BUS_FEED_URL = "https://gtfsrt.prod.obanyc.com/tripUpdates"

# Public stop codes verified against bustime.mta.info on 2026-07-11:
#   405473 = E 125 St/Park Av    -- M60-SBS westbound (toward Broadway/W 106 St)
#   402503 = E 125 St/Lexington Av -- M101 northbound (toward Ft George)
#   402503 = E 125 St/Lexington Av -- M125 westbound (toward Manhattanville, 12 Av)
#     (M101 and M125 share this stop -- bus.py filters by route separately)
# NOTE: the real-time feed's internal stop_id may use a different prefix
# than the public stop code (commonly "MTA_<code>" for OneBusAway-based
# systems, but unverified without a live key). bus.py matches by substring
# containment on both stop_id and route_id so it tolerates that uncertainty --
# if arrivals come back empty once a key is added, print the raw feed's
# stop_ids/route_ids to confirm the actual format.
BUS_ROUTES = [
    {"route": "60", "route_match": "M60+", "stop_code": "405473", "color": BUS_BLUE, "arrow": "up"},
    {"route": "101", "route_match": "M101", "stop_code": "402503", "color": BUS_BLUE, "arrow": "up"},
    {"route": "125", "route_match": "M125", "stop_code": "402503", "color": BUS_BLUE, "arrow": "up"},
]

# --- Greet (website visitor notifications) ---
# The Vercel site POSTs to storage-server.js's /greet endpoint, which writes
# this file; main.py polls its mtime to detect a new visitor. The path is
# duplicated in storage-server.js (Node has no reason to import this
# module) -- keep the two in sync if this ever moves.
GREET_FILE = "/home/admin/Desktop/MTABoard/greet.json"
GREET_POLL_SECONDS = 2        # how often main.py checks the file's mtime -- that
                               # loop is also driving 512 pixels, so this stays coarse
GREET_DURATION_SECONDS = 60   # total time the greet preempts the display, flash included
GREET_FLASH_COUNT = 3         # on/off pulses at the start of the greet, ~3s total
GREET_SCROLL_PIXELS_PER_SECOND = 10  # marquee speed for the top-panel location line
GREET_COLOR = (60, 160, 255)          # light blue, shared by the flash, marquee, and clock text --
                                       # matches renderer.TEXT_COLOR (white refracts/scatters most
                                       # on the diffuser at this brightness)

# --- Ultrasonic sensor (mode switch) ---
# HC-SR04-style sensor. ECHO is 5V and must be stepped down to 3.3V
# (level shifter or resistor divider) before reaching the Pi -- TRIG is a
# Pi output so it connects directly.
ULTRASONIC_TRIG_PIN = 23
ULTRASONIC_ECHO_PIN = 24
ULTRASONIC_THRESHOLD_M = 0.20   # 20cm; a quick pass below this triggers a mode switch

# Keeping something within ULTRASONIC_THRESHOLD_M continuously for this long
# toggles the display on/off instead of switching modes. A pass shorter than
# this is a "wave" (mode switch); this long or longer is a "hold" (power toggle).
HOLD_SECONDS = 1.5

# Keeping the hold going all the way out to this long steps main.FLIP_MODES
# to its next entry (normal -> raster -> logical -> normal), for viewing the
# board correctly through a camera/mirror -- repeat the gesture to reach
# either mode. Since HOLD_SECONDS fires first, the ordinary power-toggle
# hold still happens along the way; on_flip forces the display back on so
# the new mode is actually visible as confirmation.
FLIP_HOLD_SECONDS = 10
