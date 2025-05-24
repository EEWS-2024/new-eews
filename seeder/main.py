import math
import os
import sys

import psycopg2
import requests
from dotenv import load_dotenv
from psycopg2.extras import execute_values

load_dotenv()

TRESHOLD_DISTANCE = 1000

conn = psycopg2.connect(
    dbname=os.environ.get("DB_NAME"),
    user=os.environ.get("DB_USER"),
    password=os.environ.get("DB_PASSWORD"),
    host=os.environ.get("DB_HOST"),
    port=os.environ.get("DB_PORT")
)
cur = conn.cursor()

def haversine(lat1, lon1, lat2, lon2):
    # Radius of the Earth in kilometers
    R = 6371.0

    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Difference in coordinates
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Haversine formula
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c

    return distance

def seed_data():
    print("Seeding data...")
    url = "https://geofon.gfz-potsdam.de/fdsnws/station/1/query?net=GE&level=channel&format=text"
    response = requests.get(url)
    if response.status_code != 200:
        exit(0)

    items = response.text.split("\n")[1:]

    stored_stations = []
    stations = []
    channels = []
    channel_counts = {}
    for item in items:
        if item == "":
            continue
        network, station, location, channel, latitude, longitude, elevation, depth, azimuth, dip, sensor, scale, scale_frequency, scale_unit, sample_rate, start_time, end_time = item.split("|")

        if channel not in ["BHZ", "BHN", "BHE"]:
            continue

        if station not in stored_stations:
            stored_stations.append(station)
            stations.append({
                "station": station,
                "latitude": latitude,
                "longitude": longitude,
                "elevation": elevation,
            })

        channels.append({
            "station": station,
            "channel": channel,
            "depth": float(depth),
            "azimuth": float(azimuth),
            "dip": float(dip),
            "sample_rate": float(sample_rate),
        })

        channel_counts[station] = channel_counts.get(station, 0) + 1

    for station in stations:
        if station["station"] not in channel_counts:
            stations.remove(station)
            continue

        if channel_counts[station["station"]] < 3:
            stations.remove(station)
            for channel in channels:
                if channel["station"] == station["station"]:
                    channels.remove(channel)

    for station1 in stations:
        nearest_stations = []
        for station2 in stations:
            if station1["station"] == station2["station"]:
                continue

            distance = haversine(
                float(station1["latitude"]),
                float(station1["longitude"]),
                float(station2["latitude"]),
                float(station2["longitude"])
            )

            if distance > TRESHOLD_DISTANCE:
                continue

            if len(nearest_stations) < 3:
                nearest_stations.append((station2["station"], distance))
            else:
                farthest_station = max(nearest_stations, key=lambda x: x[1])
                if distance < farthest_station[1]:
                    nearest_stations.remove(farthest_station)
                    nearest_stations.append((station2["station"], distance))

        station1["nearest_stations"] = [
            code for code, _ in sorted(nearest_stations)
        ]

    station_rows = [
        (s["station"], float(s["latitude"]), float(s["longitude"]), float(s["elevation"]), s["nearest_stations"])
        for s in stations
    ]

    execute_values(
        cur,
        """
        INSERT INTO stations (code, latitude, longitude, elevation, nearest_stations)
        VALUES %s
        ON CONFLICT (code) DO NOTHING
        """,
        station_rows
    )

    channel_rows = [
        (c["station"], c["channel"], c["depth"], c["azimuth"], c["dip"], c["sample_rate"])
        for c in channels
    ]

    execute_values(
        cur,
        """
        INSERT INTO channels (station_code, channel, depth, azimuth, dip, sample_rate)
        VALUES %s
        ON CONFLICT (station_code, channel) DO NOTHING
        """,
        channel_rows
    )

    conn.commit()
    cur.close()
    conn.close()

def create_tables():
    print("Creating tables...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stations (
            code VARCHAR(255) PRIMARY KEY,
            latitude FLOAT NOT NULL,
            longitude FLOAT NOT NULL,
            elevation FLOAT NOT NULL,
            nearest_stations VARCHAR(255)[] NOT NULL DEFAULT '{}',
            is_enabled BOOLEAN NOT NULL DEFAULT TRUE
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            id SERIAL PRIMARY KEY,
            station_code VARCHAR(255) REFERENCES stations(code),
            channel VARCHAR(10) NOT NULL,
            depth FLOAT NOT NULL,
            azimuth FLOAT NOT NULL,
            dip FLOAT NOT NULL,
            sample_rate FLOAT NOT NULL,
            UNIQUE (station_code, channel)
        )
    """)
    conn.commit()


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "init":
        create_tables()
    seed_data()
