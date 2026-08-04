import time

import requests
from google.transit import gtfs_realtime_pb2

import config


def fetch_arrivals():
    """Return {route: [minutes_until_arrival, ...]} for config.ROUTES,
    sorted ascending, trimmed to config.ARRIVALS_PER_ROUTE, future arrivals only."""
    wanted_stops = {(r["stop_id"] + r["direction"], r["route"]) for r in config.ROUTES}

    feed = gtfs_realtime_pb2.FeedMessage()
    response = requests.get(config.SUBWAY_FEED_URL, timeout=10)
    response.raise_for_status()
    feed.ParseFromString(response.content)

    now = time.time()
    arrivals = {r["route"]: [] for r in config.ROUTES}

    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue
        route_id = entity.trip_update.trip.route_id
        for stop_time_update in entity.trip_update.stop_time_update:
            key = (stop_time_update.stop_id, route_id)
            if key not in wanted_stops:
                continue
            arrival_time = None
            if stop_time_update.HasField("arrival"):
                arrival_time = stop_time_update.arrival.time
            elif stop_time_update.HasField("departure"):
                arrival_time = stop_time_update.departure.time
            if arrival_time is None:
                continue
            minutes = (arrival_time - now) / 60
            if minutes >= 0:
                arrivals[route_id].append(minutes)

    for route in arrivals:
        arrivals[route] = [round(m) for m in sorted(arrivals[route])[: config.ARRIVALS_PER_ROUTE]]

    return arrivals
