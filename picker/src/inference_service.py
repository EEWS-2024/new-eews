from datetime import datetime, timedelta
from typing import Dict, Tuple

import numpy as np
from tensorflow.keras.saving import load_model

from picker.src.config_service import Config
from picker.src.pipeline_service import PipelineService, PipelineHasNotBeenInitializedException


class InferenceService:
    def __init__(self, config: Config):
        self.config = config
        self.pipelines: Dict[str, PipelineService] = {}
        self.state: Dict[str, Dict[str, any]] = {}
        self.p_inference_model = load_model(self.config.P_INFERENCE_MODEL_PATH)
        self.s_inference_model = load_model(self.config.S_INFERENCE_MODEL_PATH)
        self.magnitude_inference_model = load_model(self.config.MAGNITUDE_INFERENCE_MODEL_PATH)
        self.distance_inference_model = load_model(self.config.DISTANCE_INFERENCE_MODEL_PATH)

    def __reset(self, station: str):
        epoch_time = datetime(1970, 1, 1)
        self.state[station] = {
            "data_p": (0, epoch_time, 0),
            "data_s": (0, epoch_time, 0),
            "timer_s": epoch_time
        }

    def predict(self, station: str, data: list, station_time: datetime):
        if station in self.pipelines:
            pipeline = self.pipelines[station]
        else:
            pipeline = PipelineService(
                station=station,
                pipeline_model_path=self.config.PIPELINE_MODEL_PATH
            )
            self.pipelines[station] = pipeline

        try:
            preprocessed_data = pipeline.process(np.array(data))

            p_prediction_result = self.p_inference_model.predict(preprocessed_data)

            p_arrival_detected, p_arrival_time, p_arr_id, new_p_event = self.examine_prediction(
                p_prediction_result, station, station_time, is_p=True
            )

            # ### S WAVE DETECTION ###
            s_arrival_detected: bool = False
            s_arrival_time: datetime = ""
            s_arr_id = None
            new_s_event = False
            timer_s: datetime = self.state[station]["timer_s"]

            if p_arrival_detected and new_p_event:
                # Create an s timer if new event detected
                timer_s = p_arrival_time
                self.state[station]["timer_s"] = timer_s

            if timer_s - station_time <= timedelta(minutes=1):
                # Make prediction
                prediction_s: np.ndarray = self.s_inference_model.predict(preprocessed_data)

                # Extract insight
                s_arrival_detected, s_arrival_time, s_arr_id, new_s_event = self.examine_prediction(
                    prediction_s, station, station_time, is_p=False
                )

            # ### SUMMARIZE ###
            return {
                "station_code": station,
                "init_end": True,
                "p_arr": p_arrival_detected,
                "p_arr_time": p_arrival_time.strftime("%Y-%m-%d %H:%M:%S.%f"),
                "p_arr_id": f"{station}~{p_arr_id}",
                "new_p_event": new_p_event,
                "s_arr": s_arrival_detected,
                "s_arr_time": s_arrival_time.strftime("%Y-%m-%d %H:%M:%S.%f"),
                "s_arr_id": f"{station}~{s_arr_id}",
                "new_s_event": new_s_event,
            }
        except PipelineHasNotBeenInitializedException:
            return {
                "station_code": station,
                "init_end": False,
                # P wave data
                "p_arr": False,
                "p_arr_time": "",
                "p_arr_id": "",
                "new_p_event": False,
                # S wave data
                "s_arr": False,
                "s_arr_time": "",
                "s_arr_id": "",
                "new_s_event": False,
            }

    def initialize_station(self, station_time: datetime, station: str, data: list):
        self.__reset(station)
        return self.predict(station, data, station_time)

    def examine_prediction(
            self,
            prediction: np.ndarray, station_code: str, begin_time: datetime, is_p: bool
    ) -> Tuple[bool, datetime, int, bool]:
        """Examine the prediction result, returns"""
        # Check for wave arrival
        arrival_detected, arrival_pick_idx, arrival_count = self.pick_arrival(
            prediction, threshold=0.5
        )

        # Present result
        # -- Convert p_arrival_idx to timestamps
        arrival_time = begin_time + timedelta(
            seconds=arrival_pick_idx / 20.0
        )

        # Check last earthquake occurrence, note that le = last earthquake
        le_id, le_time, le_count = self.state[station_code][f"data_{'p' if is_p else 's'}"]

        is_new_earthquake = False
        if arrival_detected:
            # Case if detected earthquake is continuation from previous inference
            if abs(le_time - arrival_time) < timedelta(seconds=6):
                # refine pick time calculation
                arrival_time = le_time + (arrival_time - le_time) * arrival_count / (
                        le_count + arrival_count
                )
                arrival_count += le_count

            # Case if detected earthquake is a new event (not a continuation from previous inference)
            else:
                is_new_earthquake = True
                le_id += 1

            # Save state
            self.state[station_code][f"data_{'p' if is_p else 's'}"] = (le_id, arrival_time, arrival_count)

        return arrival_detected, arrival_time, le_id, is_new_earthquake

    def predict_statistic(self, data: list):
        x = np.array([data])

        # Magnitude
        magnitude = float(self.magnitude_inference_model.predict(x)[0][0])

        # Distance
        distance = float(self.distance_inference_model.predict(x)[0][0])

        # Output
        return {
            "magnitude": magnitude,
            "distance": distance,
            "depth": 0.0,
        }

    @staticmethod
    def pick_arrival(
            prediction: np.ndarray, threshold=0.5, window_size=382
    ) -> Tuple[bool, float, int]:
        """retrieve the existence of p wave, its pick location, and #detection in prediction from given prediction result"""
        # Detect p wave occurrence
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

            # Find mean while excluding outliers
            mean_approx = first_detection_index - (window_size - round(np.mean(deviation)))

            return True, mean_approx, len(detected_indices)

        # Case if no p wave detected
        return False, 0.0, 0