import time

import requests
from google.transit import gtfs_realtime_pb2

import config


def fetch_arrivals():
    """Return {route: [minutes_until_arrival, ...]} for config.BUS_ROUTES.
    Returns all-empty if no API key is configured yet."""
    arrivals = {r["route"]: [] for r in config.BUS_ROUTES}
    if not config.BUS_API_KEY:
        return arrivals

    feed = gtfs_realtime_pb2.FeedMessage()
    response = requests.get(
        config.BUS_FEED_URL, params={"key": config.BUS_API_KEY}, timeout=10
    )
    response.raise_for_status()
    feed.ParseFromString(response.content)

    now = time.time()

    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue
        route_id = entity.trip_update.trip.route_id
        matching_routes = [r for r in config.BUS_ROUTES if r["route_match"] in route_id]
        if not matching_routes:
            continue
        for stop_time_update in entity.trip_update.stop_time_update:
            for r in matching_routes:
                if r["stop_code"] not in stop_time_update.stop_id:
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
                    arrivals[r["route"]].append(minutes)

    for route in arrivals:
        arrivals[route] = [round(m) for m in sorted(arrivals[route])[: config.ARRIVALS_PER_ROUTE]]

    return arrivals
