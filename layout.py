import config
import renderer

ROW_HEIGHT = renderer.BLOB_SIZE + 1  # e.g. 2 rows in 16px, 1px gap between them
ROWS_PER_PAGE = config.DISPLAY_HEIGHT // ROW_HEIGHT
ALL_ROUTES = config.ROUTES + config.BUS_ROUTES


def page_count():
    return max(1, -(-len(ALL_ROUTES) // ROWS_PER_PAGE))  # ceil division


def build_frame(arrivals, page):
    image = renderer.new_frame()
    start = (page % page_count()) * ROWS_PER_PAGE
    page_routes = ALL_ROUTES[start : start + ROWS_PER_PAGE]

    y = 1
    for route_config in page_routes:
        route = route_config["route"]
        renderer.draw_route_row(
            image, y, route, route_config["color"], route_config["arrow"], arrivals.get(route, [])
        )
        y += ROW_HEIGHT

    return image
