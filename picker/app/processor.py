import json
from datetime import datetime
from typing import Dict, Any, List
import time as t
import os

from confluent_kafka import Consumer, Producer
import requests
from dotenv import load_dotenv
from .pooler import Pooler
from .redis import Redis
from .mongo import MongoDBClient
import numpy as np
from scipy.optimize import minimize
import math


load_dotenv()

ML_URL = os.getenv("ML_URL", "http://localhost:5000")
PRED_URL = f"{ML_URL}/predict"
STAT_URL = f"{ML_URL}/predict/stats"
TOPIC_PRODUCER = os.getenv("TOPIC_PRODUCER", "pick")


class KafkaDataProcessor:
    def __init__(
        self,
        consumer: Consumer,
        producer: Producer,
        pooler: Pooler,
        redis: Redis,
        mongo: MongoDBClient,
    ):
        self.consumer = consumer
        self.producer = producer
        self.pooler = pooler
        self.redis = redis
        self.mongo = mongo

    # def consume(self, topic: str):
    #     self.consumer.subscribe([topic])
    #     show_nf = True
    #
    #     while True:
    #         try:
    #             msg = self.consumer.poll(0.1)
    #             if msg is None:
    #                 if show_nf:
    #                     print("No message received")
    #                 show_nf = False
    #                 continue
    #             if msg.error():
    #                 print(f"Error: {msg.error()}")
    #                 continue
    #
    #             show_nf = True
    #             value = json.loads(msg.value())
    #
    #             logvalue = copy.copy(value)
    #             logvalue["data"] = None
    #
    #             if "type" in value and value["type"] == "start":
    #                 self.pooler.reset()
    #                 continue
    #             if "type" in value and value["type"] != "trace":
    #                 continue
    #
    #             with open("out/dump.txt", "a", encoding="utf-8") as f:
    #                 f.write(f"{value}\n")
    #             self.__process_received_data(value)
    #
    #         except Exception as e:
    #             print(f"Error: {str(e)}")
    #             continue

    def consume(self, topic: str):
        print("CONSUMING", topic)
        with open("out/dump.json", "r", encoding="utf-8") as f:
            values = json.load(f)
            iterator = 0
            for value in values:
                try:
                    self.__process_received_data(value)
                    iterator += 1
                    print(f"Processed {iterator} data")
                except Exception as e:
                    print("outer error")
                    print(e)
                    print(f"Error: {str(e)}")
                    continue

    def __process_received_data(self, value: Dict[str, Any]):
        station = value["station"]
        channel = value["channel"]
        starttime = datetime.fromisoformat(value["starttime"])
        data = value["data"]
        self.pooler.set_station_first_start_time(station, starttime)
        self.pooler.extend_data_points(station, channel, data)

        is_ready_to_predict = self.pooler.is_ready_to_predict(station)

        if is_ready_to_predict:
            self.__predict(station, value["process_start_time"])

    def __predict(self, station: str, process_start_time: float) -> None:
        station_time = self.pooler.get_station_time(station)
        data = self.pooler.get_data_to_predict(station)
        data_t = [list(x) for x in zip(*data)]

        start_time = station_time.strftime("%Y-%m-%d %H:%M:%S.%f")
        res = self.__req(
            PRED_URL,
            {
                "station_code": station,
                "start_time": start_time,
                "x": data_t,
            },
        )

        if res is None:
            return

        result = res["result"]

        if not result["init_end"]:
            self.pooler.set_caches(station, data)
            return

        if not result["p_arr"]:
            self.pooler.set_caches(station, data)
            return

        p_arr = result["p_arr"]
        s_arr = result["s_arr"]

        if p_arr or s_arr:
            result = res["result"]
            result["process_time"] = res["process_time"]
            result["type"] = "ps"
            result["station"] = station
            self.producer.produce(result)
        prev_p_time_exists = station in self.pooler.station_p_time
        prev_s_time_exists = station in self.pooler.station_s_time

        p_time = datetime.strptime(result["p_arr_time"], "%Y-%m-%d %H:%M:%S.%f")
        s_time = datetime.strptime(result["s_arr_time"], "%Y-%m-%d %H:%M:%S.%f")

        if not prev_p_time_exists and not prev_s_time_exists and p_arr and s_arr:
            self.pooler.set_caches(station, data, True)
            self.__pred_stats(station, station_time, process_start_time)
            return

        if prev_p_time_exists and not prev_s_time_exists:
            diff_secs = (station_time - self.pooler.station_p_time[station]).total_seconds()
            if (diff_secs >= 60 and not s_arr) or s_arr:
                self.pooler.set_caches(station, data, True)
                self.__pred_stats(station, station_time, process_start_time)
                return

        if not prev_p_time_exists and p_arr:
            self.pooler.station_p_time[station] = p_time

        if not prev_s_time_exists and s_arr:
            self.pooler.station_s_time[station] = s_time

        self.pooler.set_caches(station, data)

    def __pred_stats(self, station: str, wf_time: datetime, process_start_time: float):
        data_cache = self.pooler.get_cache(station)
        data_cache_t = self.__transpose(data_cache)
        res = self.__req(
            STAT_URL, {"x": data_cache_t, "station_code": station}, isPred=True
        )

        if res:
            result = res["result"]
            result["process_time"] = res["process_time"]
            self.redis.save_waveform(station, result)
            wf3 = self.redis.get_3_waveform(station)

            if wf3 is not None and len(wf3) >= 3:
                epic = self.__get_epic_ml(wf3)
                payload = {
                    "time": wf_time.isoformat(),
                    **epic,
                    "station": "PARAMS",
                    "type": "params",
                }
                self.producer.produce(payload)
                self.redis.remove_3_waveform_dict(wf3)
                self.mongo.create(payload)
                print("SAVED TO MONGODB: ", payload)

        self.pooler.reset_ps(station)

    def __req(self, url: str, data: Dict[str, Any], isPred=False, retry=3, timeout=30):
        for i in range(retry):
            start_time = datetime.now()
            try:
                response = requests.post(url, data=json.dumps(data), timeout=timeout, headers={
                    "Content-Type": "application/json",
                })
                if response.status_code != 200:
                    print("Error: ", response.json())
                end_time = datetime.now()
                process_time = (end_time - start_time).total_seconds()

                result = json.loads(response.text)
                if isinstance(result, dict):
                    res = {"process_time": process_time, "result": result}
                    return res
            except Exception as e:
                print(f"Error: {str(e)}")
                t.sleep(1)
                continue
        return None

    def __transpose(self, data: List[List[Any]]):
        return [list(x) for x in zip(*data)]

    def to_cartesian(self, lat, lon):
        R = 6371  # Radius bumi dalam kilometer
        phi = np.deg2rad(90 - lat)
        theta = np.deg2rad(lon)

        x = R * np.sin(phi) * np.cos(theta)
        y = R * np.sin(phi) * np.sin(theta)
        z = R * np.cos(phi)

        return np.array([x, y, z])

    def trilaterate(self, p1, p2, p3, r1, r2, r3):
        def error(x, p, r):
            return np.linalg.norm(x - p) - r

        def total_error(x):
            return abs(error(x, p1, r1)) + abs(error(x, p2, r2)) + abs(error(x, p3, r3))

        initial_guess = (p1 + p2 + p3) / 3
        result = minimize(total_error, initial_guess, method="Nelder-Mead")
        # print(result)

        if not result.success:
            raise ValueError("Optimization failed")

        x, y, z = result.x
        lat = 90 - np.rad2deg(np.arccos(z / 6371))
        lon = np.rad2deg(np.arctan2(y, x))

        return lat, lon

    def __get_epic_ml(self, wf: list[dict]):
        # print("get_epic_ml")
        station_codes = []
        station_latitudes = []
        station_longitudes = []
        magnitudes = []
        distances = []
        depths = []

        for w in wf:
            station_codes.append(w["station_code"])
            station_latitudes.append(w["location"][0])
            station_longitudes.append(w["location"][1])
            magnitudes.append(float(w["magnitude"]))
            distances.append(float(w["distance"]))
            depths.append(float(w["depth"]))

        payload = {
            "station_codes": station_codes,
            "station_latitudes": station_latitudes,
            "station_longitudes": station_longitudes,
            "magnitudes": magnitudes,
            "distances": distances,
            "depths": depths,
        }
        # print(f"REC PAYLOAD: {payload}")
        # res = self.__req(REC_URL, payload)
        res = self.recalculate(payload)
        # print(f"REC RES: {res}")

        if res is not None:
            return res
        return {}

    def recalculate(self, input_data: dict) -> dict:
        # Unpack json data
        magnitudes: np.ndarray = np.array(input_data["magnitudes"])
        distances: np.ndarray = np.array(input_data["distances"]).astype(np.complex128)
        station_latitudes: np.ndarray = np.array(
            input_data["station_latitudes"]
        ).astype(np.complex128)
        station_longitudes: np.ndarray = np.array(
            input_data["station_longitudes"]
        ).astype(np.complex128)

        # Cache values
        station_latitudes_rad = station_latitudes / 180.0 * np.pi * 6371.0
        station_longitudes_rad = station_longitudes / 180.0 * np.pi * 6371.0

        # Recalculate magnitude
        magnitude = np.mean(magnitudes)

        # Recalculate location
        # TODO : This formula is only for flat euclidian R2 space,
        #  find another more precise formula for intersection of three spheres.
        points = []
        for i in range(len(station_latitudes) - 1):
            for j in range(i + 1, len(station_latitudes)):
                # distance between two stations
                R = self.haversine(
                    station_latitudes[i],
                    station_longitudes[i],
                    station_latitudes[j],
                    station_longitudes[j],
                )

                # Radians position of two stations
                xi = station_latitudes_rad[i]
                yi = station_longitudes_rad[i]
                xj = station_latitudes_rad[j]
                yj = station_longitudes_rad[j]
                ri = distances[i]
                rj = distances[j]

                x_delta = (
                    0.5
                    * np.sqrt(
                        2 * (ri**2 + rj**2) / R**2 - (ri**2 - rj**2) ** 2 / R**4 - 1
                    )
                    * (yj - yi)
                )

                y_delta = (
                    0.5
                    * np.sqrt(
                        2 * (ri**2 + rj**2) / R**2 - (ri**2 - rj**2) ** 2 / R**4 - 1
                    )
                    * (xi - xj)
                )

                x_base = 0.5 * (xi + xj) + (ri**2 - rj**2) / (2 * R**2) * (xj - xi)

                y_base = 0.5 * (yi + yj) + (ri**2 - rj**2) / (2 * R**2) * (yj - yi)

                x_1 = x_base + x_delta
                x_2 = x_base - x_delta
                y_1 = y_base + y_delta
                y_2 = y_base - y_delta

                points.append(np.array([[x_1, y_1], [x_2, y_2]]))

        # Find points with the least variance
        triplets = []
        variances = []
        for i in range(2):
            for j in range(2):
                for k in range(2):
                    # Generate triplets
                    triplet: np.ndarray = np.array(
                        [points[0][i], points[1][j], points[2][k]]
                    )
                    triplets.append(triplet)

                    # Calculate variance
                    variances.append(triplet.var(axis=0).sum())

        # Select the triplets with the least variance value
        variances = np.array(variances)
        argmin = variances.argmin()

        # Retrieve argmin-th triplet
        triplet: np.ndarray = triplets[argmin]

        # Project triplet into real number
        triplet = triplet.real

        # Take the average
        ans = triplet.mean(axis=0)

        # Convert result back to degree
        ans *= 180 / np.pi / 6371.0

        # Compose output
        output = {
            "station_codes": input_data["station_codes"],
            "magnitude": float(magnitude),
            "latitude": float(ans[0]),
            "longitude": float(ans[1]),
            "depth": 0.0,
        }

        return output

    def haversine(self, lat1, lon1, lat2, lon2):
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

        distance = 6371.0 * c

        return distance
