import json
from typing import Dict, List

import redis

from picker.src.config_service import Config


class RedisService:
    def __init__(self, config: Config):
        self.redis = redis.Redis(
            host=config.REDIS_HOST,
            port=int(config.REDIS_PORT)
        )

    def get(self, key):
        return self.redis.get(key)

    def set(self, key, value):
        self.redis.set(key, value)

    def delete(self, key):
        self.redis.delete(key)

    def keys(self, pattern):
        return self.redis.keys(pattern)

    def save_waveform(self, station: str, waveform: dict):
        self.redis.set(f"WAVEFORM_{station}", json.dumps(waveform), 60 * 10)

    def get_3_waveform(
        self,
        station: str,
        nearest_stations: Dict[str, List[str]],
        locations: Dict[str, List[float]]
    ):
        print("get_3_waveform")
        nearest_station = nearest_stations.get(station) + [station]
        for st in nearest_station:
            data = self._get_3_waveform(st, nearest_stations, locations)
            if data is not None and len(data) >= 3:
                d = data[:3]
                print(d)
                return d
        return None

    def _get_3_waveform(
            self,
            station: str,
            nearest_stations: Dict[str, List[str]],
            locations: Dict[str, List[float]]
    ):
        if not self.has_3_waveform(station, nearest_stations):
            print("No 3 waveform found")
            return None
        nearest_station = nearest_stations.get(station) + [station]

        data = []
        for stat in nearest_station:
            wf = self.get_waveform(stat)
            loc = locations.get(stat)
            if (wf is None) or (loc is None) or (len(data) >= 3):
                continue
            wf["location"] = loc
            wf["distance"] = float(wf["distance"])
            data.append(wf)
        print("data wfs")
        if len(data) < 3:
            print("Data wfs not enough")
            return []
        return data

    def has_3_waveform(self, station: str, nearest_stations: Dict[str, List[str]]) -> bool:
        nearest_station = nearest_stations.get(station)
        has_2_nearest = len(nearest_station) >= 2
        if not has_2_nearest:
            return False

        nearest_station = nearest_station + [station]
        i = 0
        for stat in nearest_station:
            r = self.get_waveform(stat)
            if r is not None:
                i +=1
        print("has waveform: ", i)
        return i >= 3

    def get_waveform(self, station: str) -> dict | None:
        r = self.redis.get(f"WAVEFORM_{station}")
        if r is None:
            return None
        return json.loads(r)

    def remove_3_waveform_dict(self, wfs: list[dict[str]]) -> None:
        for wf in wfs:
            station = wf["station"]
            self.redis.delete(f"WAVEFORM_{station}")