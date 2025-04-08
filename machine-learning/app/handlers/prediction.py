from typing import List, Tuple

import numpy as np
from flask_sqlalchemy import SQLAlchemy
from redis import Redis
from datetime import datetime, timedelta

from sqlalchemy import desc
from tensorflow.keras.models import load_model
from tensorflow.keras.optimizers import Adam

from app.handlers.pipeline import Slope, Square, AddChannels, Log1P, MultiExponentialSmoothing, PairwiseRatio, SlidingWindow
from app.models import StationWave, StationTime


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
        self.DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
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

        custom_objects = {'Custom>Adam': Adam}

        self.p_model = load_model("models/model_p_2_1_best.h5", custom_objects=custom_objects)
        self.s_model = load_model("models/model_s_2_1_best.h5", custom_objects=custom_objects)
        self.mag_model = load_model("models/model_mag_1.h5", custom_objects=custom_objects)
        self.dist_model = load_model("models/model_dist_1.h5", custom_objects=custom_objects)

        self.redis = redis
        self.db = db

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

        predicted_p_wave = self.p_model.predict(X)

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
            predicted_s_wave: np.ndarray = self.s_model.predict(X)

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
            # "p_arr_id": f"{station_code}~{p_arr_id}",
            "new_p_event": is_new_p_event,
            "s_arr": is_s_arrival_detected,
            "s_arr_time": s_arrival_time.strftime(self.DATETIME_FORMAT),
            # "s_arr_id": f"{station_code}~{s_arr_id}",
            "new_s_event": is_new_s_event,
        }
