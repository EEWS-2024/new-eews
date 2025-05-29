import math
from typing import List, Tuple

import numpy as np
from flask_sqlalchemy import SQLAlchemy
from redis import Redis
from datetime import datetime, timedelta

from sqlalchemy import desc
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.optimizers import Adam

from app.handlers.pipeline import Slope, Square, AddChannels, Log1P, MultiExponentialSmoothing, PairwiseRatio, SlidingWindow
from app.models import StationWave, StationTime
import warnings
warnings.filterwarnings("ignore")

# Configure TensorFlow to avoid eager mode issues
tf.compat.v1.disable_eager_execution()
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

class PredictionHandler:
    def __init__(
        self,
        redis: Redis,
        db: SQLAlchemy
    ):
        self.P_THRESHOLD = 0.5
        self.S_THRESHOLD = 0.5
        self.SAMPLING_RATE = 20.0
        self.WINDOW_SIZE = 382
        self.DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        self.EARTHQUAKE_PICK_TIME_THRESHOLD = timedelta(seconds=6)
        self.S_WAVE_DETECTION_DURATION = timedelta(minutes=1)

        self.START_TIME = datetime(1970, 1, 1).strftime(self.DATETIME_FORMAT)

        self.slope = Slope(redis, 20.0)
        self.square = Square()
        self.add_channels = AddChannels()
        self.log1p = Log1P()
        self.multi_exponential_smoothing = MultiExponentialSmoothing(
            redis,
            [0.9, 0.92375, 0.9475, 0.97125, 0.995],
            100
        )
        self.pairwise_ratio = PairwiseRatio([0.9, 0.92375, 0.9475, 0.97125, 0.995])
        self.sliding_window = SlidingWindow(redis, 382)

        # Initialize models with TensorFlow session management
        self.graph = tf.compat.v1.Graph()
        self.sess = tf.compat.v1.Session(graph=self.graph)
        
        with self.graph.as_default():
            with self.sess.as_default():
                custom_objects = {'Custom>Adam': Adam}
                
                try:
                    self.p_model = load_model("models/custom/model_p_2_1_best.h5", custom_objects=custom_objects)
                    self.s_model = load_model("models/custom/model_s_2_1_best.h5", custom_objects=custom_objects)
                    self.mag_model = load_model("models/custom/model_mag_1.h5", custom_objects=custom_objects)
                    self.dist_model = load_model("models/custom/model_dist_1.h5", custom_objects=custom_objects)
                    print("Custom models loaded successfully")
                except Exception as e:
                    print(f"Error loading custom models: {e}")
                    self.p_model = None
                    self.s_model = None
                    self.mag_model = None
                    self.dist_model = None

        self.redis = redis
        self.db = db

    def _predict_with_session(self, model, X):
        """Helper method to predict using the correct TensorFlow session"""
        with self.graph.as_default():
            with self.sess.as_default():
                return model.predict(X)

    def __get_station_wave(self, station_code: str, wave_type: str):
        station_wave = StationWave.query.filter_by(
            station_code=station_code,
            type=wave_type,
        ).order_by(desc(StationWave.id)).first()

        if not station_wave:
            station_wave = StationWave(
                station_code=station_code,
                type=wave_type,
            )
            self.db.session.add(station_wave)
            self.db.session.commit()

        return station_wave

    def __pick_arrival(
        self,
        prediction: np.ndarray,
        window_size,
        threshold=0.5
    ) -> Tuple[bool, float, int]:
        detected_indices = np.where((prediction > threshold).any(axis=1))[
            0
        ]  # Index where p wave arrival is detected

        # Case if p wave is detected
        if detected_indices.any():
            first_detection_index = detected_indices[0]
            ideal_deviation = (
                    np.array(detected_indices) - first_detection_index
            )  # Location of p wave arrival ideally follows # this value

            # For all triggered windows, find its argmax
            argmax = np.array(
                prediction[detected_indices].argmax(axis=1)
            )  # p wave pick index in every windows
            deviation = argmax + ideal_deviation  # predicted deviation

            mean_approx = first_detection_index - (window_size - round(np.mean(deviation)))

            return True, mean_approx, len(detected_indices)

        # Case if no p wave detected
        return False, 0.0, 0

    def __examine_prediction(
            self,
            prediction: np.ndarray,
            station_code: str,
            begin_time: datetime,
            station_wave: StationWave
    ) -> Tuple[bool, datetime, bool]:
        arrival_detected, arrival_pick_idx, arrival_count = self.__pick_arrival(
            prediction,
            window_size=self.WINDOW_SIZE,
            threshold=self.P_THRESHOLD
        )

        arrival_time = begin_time + timedelta(
            seconds=arrival_pick_idx / self.SAMPLING_RATE
        )

        is_new_earthquake = False
        if arrival_detected:
            # Case if detected earthquake is continuation from previous inference
            if abs(station_wave.time - arrival_time) < self.EARTHQUAKE_PICK_TIME_THRESHOLD:
                # refine pick time calculation
                station_wave.time = station_wave.time + (arrival_time - station_wave.time) * arrival_count / (
                        station_wave.count + arrival_count
                )
                station_wave.count += arrival_count
            # Case if detected earthquake is a new event (not a continuation from previous inference)
            else:
                new_station_wave = StationWave(
                    station_code=station_code,
                    time=arrival_time,
                    count=arrival_count,
                    type=station_wave.type,
                )
                self.db.session.add(new_station_wave)
                is_new_earthquake = True

            self.db.session.commit()

        return arrival_detected, arrival_time, is_new_earthquake

    def predict(self, x: List[float], start_time: str, station_code: str):
        station_primary_wave = self.__get_station_wave(
            station_code,
            "primary",
        )

        station_time = StationTime.query.filter_by(station_code=station_code).first()

        if not station_time:
            station_time = StationTime(
                station_code=station_code,
            )
            self.db.session.add(station_time)
            self.db.session.commit()

        start_time = datetime.strptime(start_time, self.DATETIME_FORMAT)

        X = np.array(x)
        if self.slope.get(station_code) is None:
            self.slope.set_initial_state(X, station_code)
        X = self.slope.compute(X, station_code)
        X = self.square.compute(X)
        X = self.add_channels.compute(X)
        X = self.log1p.compute(X)
        if self.multi_exponential_smoothing.get(station_code) is None:
            self.multi_exponential_smoothing.set_initial_state(X, station_code)
        X = self.multi_exponential_smoothing.compute(X, station_code)
        X = self.pairwise_ratio.compute(X)
        if self.sliding_window.get(station_code) is None:
            self.sliding_window.set_initial_state(X, station_code)
        X = self.sliding_window.compute(X, station_code)

        if self.p_model is None:
            # Return default response if model not loaded
            return {
                "station_code": station_code,
                "init_end": True,
                "p_arr": False,
                "p_arr_time": start_time.strftime(self.DATETIME_FORMAT),
                "new_p_event": False,
                "s_arr": False,
                "s_arr_time": start_time.strftime(self.DATETIME_FORMAT),
                "new_s_event": False,
                "error": "Custom models not loaded"
            }
            
        predicted_p_wave = self._predict_with_session(self.p_model, X)

        is_p_arrival_detected, p_arrival_time, is_new_p_event = self.__examine_prediction(
            predicted_p_wave,
            station_code,
            start_time,
            station_primary_wave
        )

        is_s_arrival_detected: bool = False
        s_arrival_time: datetime = datetime(1970, 1, 1)
        is_new_s_event = False

        if is_p_arrival_detected and is_new_p_event:
            station_time.time = p_arrival_time

        if station_time.time - start_time <= self.S_WAVE_DETECTION_DURATION:
            predicted_s_wave: np.ndarray = self._predict_with_session(self.s_model, X)

            station_secondary_wave = self.__get_station_wave(
                station_code,
                "secondary",
            )

            is_s_arrival_detected, s_arrival_time, is_new_s_event = self.__examine_prediction(
                predicted_s_wave,
                station_code,
                start_time,
                station_secondary_wave
            )

        return {
            "station_code": station_code,
            "init_end": True,
            "p_arr": is_p_arrival_detected,
            "p_arr_time": p_arrival_time.strftime(self.DATETIME_FORMAT),
            "new_p_event": is_new_p_event,
            "s_arr": is_s_arrival_detected,
            "s_arr_time": s_arrival_time.strftime(self.DATETIME_FORMAT),
            "new_s_event": is_new_s_event,
        }

    def predict_stats(self, x: List[float], station_code: str):
        if self.mag_model is None or self.dist_model is None:
            return {
                "station_code": station_code,
                "magnitude": 0.0,
                "depth": 0.0,
                "distance": 0.0,
                "error": "Custom models not loaded"
            }
            
        X = np.array([x])
        magnitude = float(self._predict_with_session(self.mag_model, X)[0][0])
        distance = float(self._predict_with_session(self.dist_model, X)[0][0])

        return {
            "station_code": station_code,
            "magnitude": magnitude,
            "depth": 0.0,
            "distance": distance,
        }

    def __haversine(self, lat1, lon1, lat2, lon2):
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

    def recalculate(
        self,
        station_codes: List[str],
        latitudes:  List[float],
        longitudes: List[float],
        magnitudes: List[float],
        distances: List[float],
    ):
        magnitudes: np.ndarray = np.array(magnitudes)
        distances: np.ndarray = np.array(distances).astype(np.complex128)
        latitudes: np.ndarray = np.array(
            latitudes
        ).astype(np.complex128)
        longitudes: np.ndarray = np.array(
            longitudes
        ).astype(np.complex128)

        latitudes_rad = latitudes / 180.0 * np.pi * 6371.0
        longitudes_rad = longitudes / 180.0 * np.pi * 6371.0

        magnitude = np.mean(magnitudes)

        points = []
        for i in range(len(latitudes) - 1):
            for j in range(i + 1, len(latitudes)):
                # distance between two stations
                R = self.__haversine(
                    latitudes[i],
                    longitudes[i],
                    latitudes[j],
                    longitudes[j],
                )

                # Radians position of two stations
                xi = latitudes_rad[i]
                yi = longitudes_rad[i]
                xj = latitudes_rad[j]
                yj = longitudes_rad[j]
                ri = distances[i]
                rj = distances[j]

                x_delta = (
                        0.5
                        * np.sqrt(
                    2 * (ri ** 2 + rj ** 2) / R ** 2 - (ri ** 2 - rj ** 2) ** 2 / R ** 4 - 1
                )
                        * (yj - yi)
                )

                y_delta = (
                        0.5
                        * np.sqrt(
                    2 * (ri ** 2 + rj ** 2) / R ** 2 - (ri ** 2 - rj ** 2) ** 2 / R ** 4 - 1
                )
                        * (xi - xj)
                )

                x_base = 0.5 * (xi + xj) + (ri ** 2 - rj ** 2) / (2 * R ** 2) * (xj - xi)

                y_base = 0.5 * (yi + yj) + (ri ** 2 - rj ** 2) / (2 * R ** 2) * (yj - yi)

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

        return {
            "station_codes": station_codes,
            "magnitude": float(magnitude),
            "latitude": float(ans[0]),
            "longitude": float(ans[1]),
        }