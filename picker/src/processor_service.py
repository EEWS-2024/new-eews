import json
import math
from datetime import datetime
from typing import Dict, Any

import numpy as np
from confluent_kafka import Consumer
from sqlalchemy.future import select

from picker.src.database_model.station_model import Station
from picker.src.database_service import DatabaseService
from picker.src.inference_service import InferenceService
from picker.src.pooling_service import PoolingService
from picker.src.preprocess_service import PreprocessService
from picker.src.redis_service import RedisService

ML_URL = "http://localhost:8100"
PRED_URL = f"{ML_URL}/predict"
INIT_URL = f"{ML_URL}/restart"
STAT_URL = f"{ML_URL}/approx_earthquake_statistics"
REC_URL = f"{ML_URL}/recalculate"

class ProcessorService:
    def __init__(
            self,
            preprocess: PreprocessService,
            data_pooling: PoolingService,
            inference: InferenceService,
            database: DatabaseService,
            consumer: Consumer,
            redis: RedisService
    ):
        self.data_pooling = data_pooling
        self.preprocess = preprocess
        self.inference = inference
        self.database = database
        self.consumer = consumer
        self.redis = redis
        self.partitions = []
        self.nearest_stations, self.station_locations = self.__get_stations()

    def __get_stations(self):
        enabled_stations = self.database.execute(select(Station).where(Station.is_enabled == True)).scalars().all()

        nearest_stations = {station.code: station.nearest_stations  for station in enabled_stations}
        station_locations = {station.code: [station.lat, station.long] for station in enabled_stations}

        return nearest_stations, station_locations


    def consume(self, consumer_topic: str):
        self.consumer.subscribe([consumer_topic])

        while True:
            message = self.consumer.poll(10)
            self.partitions = self.consumer.assignment()

            if message is None:
                continue
            if message.error():
                print(f"Error: {message.error()}")
                continue

            trace_data = json.loads(message.value())

            if trace_data['type'] == 'trace':
                preprocessed_data = self.preprocess.run(trace_data)
                self.__process_data(preprocessed_data)


    def __process_data(self, trace_data: Dict[str, Any]):
        station = trace_data["station"]
        channel = trace_data["channel"]
        start_time = datetime.fromisoformat(trace_data["start_time"])
        data = trace_data["data"]

        self.data_pooling.set_station_start_time(station, start_time)
        self.data_pooling.extend_data_points(station, channel, data)

        is_ready_to_init = self.data_pooling.is_ready_to_init(station)
        has_initiated = self.data_pooling.has_initiated(station)

        if not has_initiated and not is_ready_to_init:
            return

        if not has_initiated and is_ready_to_init:
            init_result = self.inference.initialize_station(
                station_time=self.data_pooling.get_station_time(station),
                station=station,
                data=self.__transpose(self.data_pooling.get_data_to_init(station))
            )

            if init_result["init_end"]:
                self.data_pooling.add_initiated_station(station)
            else:
                self.data_pooling.reset_ps(station)

            return

        is_ready_to_predict = self.data_pooling.is_ready_to_predict(station)
        #
        if is_ready_to_predict:
            self.__predict(
                station_time=self.data_pooling.get_station_time(station),
                station=station,
                data=self.__transpose(self.data_pooling.get_data_to_predict(station))
            )

    @staticmethod
    def __transpose(data: list[list[int]]) -> list[list[int]]:
        return [list(x) for x in zip(*data)]

    def __predict(self, station: str, data: list, station_time: datetime) -> None:
        prediction_result = self.inference.predict(station, data, station_time)

        if not prediction_result["init_end"]:
            self.data_pooling.set_caches(station, data)
            return

        if not prediction_result["p_arr"]:
            self.data_pooling.set_caches(station, data)
            return

        p_arr = prediction_result["p_arr"]
        s_arr = prediction_result["s_arr"]

        # if p_arr or s_arr:
        #     result = prediction_result["result"]
            # result["process_time"] = prediction_result["process_time"]
            # result["type"] = "ps"
            # result["station"] = station
            # self.producer.produce(result)
        prev_p_time_exists = station in self.data_pooling.station_p_time
        prev_s_time_exists = station in self.data_pooling.station_s_time

        p_time = datetime.strptime(prediction_result["p_arr_time"], "%Y-%m-%d %H:%M:%S.%f")
        s_time = datetime.strptime(prediction_result["s_arr_time"], "%Y-%m-%d %H:%M:%S.%f")

        if not prev_p_time_exists and not prev_s_time_exists and p_arr and s_arr:
            self.data_pooling.set_caches(station, data, True)
            self.__pred_stats(station, station_time)
            return

        if prev_p_time_exists and not prev_s_time_exists:
            diff_secs = (station_time - self.data_pooling.station_p_time[station]).total_seconds()
            if (diff_secs >= 60 and not s_arr) or s_arr:
                self.data_pooling.set_caches(station, data, True)
                self.__pred_stats(station, station_time)
                return

        if not prev_p_time_exists and p_arr:
            self.data_pooling.station_p_time[station] = p_time

        if not prev_s_time_exists and s_arr:
            self.data_pooling.station_s_time[station] = s_time

        self.data_pooling.set_caches(station, data)

    def __pred_stats(self, station: str, station_time: datetime):
        statistic_prediction_result = self.inference.predict_statistic(
            data=self.__transpose(self.data_pooling.get_cache(station)),
        )

        # result = res["result"]
        # result["process_time"] = res["process_time"]
        statistic_prediction_result["station"] = station
        self.redis.save_waveform(station, statistic_prediction_result)
        wf3 = self.redis.get_3_waveform(
            station,
            self.nearest_stations,
            self.station_locations
        )
        # self.producer.produce({"wf3": wf3})
        if wf3 is not None and len(wf3) >= 3:
            epic = self.__get_epic_ml(wf3)
            payload = {
                "time": station_time.isoformat(),
                **epic,
                "station": "PARAMS",
                "type": "params",
            }
            # self.producer.produce(payload)
            self.redis.remove_3_waveform_dict(wf3)
            # self.mongo.create(payload)
            print("SAVED TO MONGODB: ", payload)

        self.data_pooling.reset_ps(station)

    def __get_epic_ml(self, wf: list[dict]):
        # print("get_epic_ml")
        stations = []
        station_latitudes = []
        station_longitudes = []
        magnitudes = []
        distances = []
        depths = []

        for w in wf:
            stations.append(w["station"])
            station_latitudes.append(w["location"][0])
            station_longitudes.append(w["location"][1])
            magnitudes.append(float(w["magnitude"]))
            distances.append(float(w["distance"]))
            depths.append(float(w["depth"]))

        payload = {
            "stations": stations,
            "station_latitudes": station_latitudes,
            "station_longitudes": station_longitudes,
            "magnitudes": magnitudes,
            "distances": distances,
            "depths": depths,
        }
        res = self.recalculate(payload)

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

                radius = self.haversine(
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
                        2 * (ri**2 + rj**2) / radius**2 - (ri**2 - rj**2) ** 2 / radius**4 - 1
                    )
                    * (yj - yi)
                )

                y_delta = (
                    0.5
                    * np.sqrt(
                        2 * (ri**2 + rj**2) / radius**2 - (ri**2 - rj**2) ** 2 / radius**4 - 1
                    )
                    * (xi - xj)
                )

                x_base = 0.5 * (xi + xj) + (ri**2 - rj**2) / (2 * radius**2) * (xj - xi)

                y_base = 0.5 * (yi + yj) + (ri**2 - rj**2) / (2 * radius**2) * (yj - yi)

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
            "stations": input_data["stations"],
            "magnitude": float(magnitude),
            "latitude": float(ans[0]),
            "longitude": float(ans[1]),
            "depth": 0.0,
        }

        return output

    @staticmethod
    def haversine(lat1, lon1, lat2, lon2):
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = (
                math.sin(dlat / 2) ** 2
                + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance = 6371.0 * c

        return distance