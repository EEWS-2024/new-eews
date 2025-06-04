import math
import os
import sys
import json

import psycopg2
import requests
from dotenv import load_dotenv
from psycopg2.extras import execute_values

load_dotenv()

TRESHOLD_DISTANCE = 1000

conn = psycopg2.connect(
    dbname=os.environ.get("DB_NAME", "picker_db"),
    user=os.environ.get("DB_USER", "guncang"),
    password=os.environ.get("DB_PASSWORD", "guncang"),
    host=os.environ.get("DB_HOST", "85.209.163.202"),
    port=os.environ.get("DB_PORT", 9205)
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
    with open("data.json", "r") as f:
        stations = json.load(f)

        channels = []
        for station1 in stations:
            nearest_stations = []
            for station2 in stations:
                if station1["code"] == station2["code"]:
                    continue

                distance = haversine(
                    float(station1["lat"]),
                    float(station1["long"]),
                    float(station2["lat"]),
                    float(station2["long"])
                )

                if distance > TRESHOLD_DISTANCE:
                    continue

                if len(nearest_stations) < 3:
                    nearest_stations.append((station2["code"], distance))
                else:
                    farthest_station = max(nearest_stations, key=lambda x: x[1])
                    if distance < farthest_station[1]:
                        nearest_stations.remove(farthest_station)
                        nearest_stations.append((station2["code"], distance))

            station1["nearest_stations"] = [
                code for code, _ in sorted(nearest_stations)
            ]

            for channel in station1["channels"]:
                channels.append({
                    "code": station1["code"],
                    "channel": channel["code"],
                    "depth": channel["depth"],
                    "azimuth": channel["azimuth"],
                    "dip": channel["dip"],
                    "sample_rate": channel["sample_rate"]
                })

        station_rows = [
            (s["code"], float(s["lat"]), float(s["long"]), float(s["elevation"]), s["nearest_stations"])
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
            (c["code"], c["channel"], c["depth"], c["azimuth"], c["dip"], c["sample_rate"])
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
    cur.execute("""
        CREATE TABLE IF NOT EXISTS waveforms (
            pick_time TIMESTAMPTZ NOT NULL,
            station_code VARCHAR(255) REFERENCES stations(code),
            depth FLOAT NOT NULL,
            distance FLOAT NOT NULL,
            magnitude FLOAT NOT NULL,
            is_new BOOLEAN NOT NULL DEFAULT TRUE
        )
    """)
    cur.execute("""
        SELECT create_hypertable('waveforms', 'pick_time')
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS epic_waveforms (
            event_time TIMESTAMPTZ NOT NULL,
            magnitude FLOAT NOT NULL,
            latitude FLOAT NOT NULL,
            longitude FLOAT NOT NULL,
            station_codes TEXT[] NOT NULL
        )
    """)
    # cur.execute("""
    #        SELECT create_hypertable('epic_waveforms', 'event_time')
    #    """)
    conn.commit()


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "init-only":
        create_tables()
        sys.exit(0)
    if command == "init":
        create_tables()
    seed_data()
