import os
import numpy as np
import tensorflow as tf
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from scipy.interpolate import interp1d

from app.handlers.phasenet.model import UNet
from app.handlers.phasenet.detect_peaks import detect_peaks

import warnings
warnings.filterwarnings("ignore")

tf.compat.v1.disable_eager_execution()
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

class PhaseNetHandler:
    def __init__(self):
        self.INPUT_SAMPLING_RATE = 20.0   # Sampling rate for Indonesia (Hz)
        self.PHASENET_SAMPLING_RATE = 100.0  # Sampling rate that PhaseNet requires (Hz)
        self.PHASENET_LENGTH = 3000       # Length of data that PhaseNet requires (points)
        self.MIN_INPUT_LENGTH = 600       # Minimal input data: 3000 * (20/100) = 600 points
        self.X_SHAPE = [3000, 1, 3]       # PhaseNet input shape
        self.DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        
        # Initialize TensorFlow session for PhaseNet
        self.graph = tf.compat.v1.Graph()
        self.sess = tf.compat.v1.Session(graph=self.graph)
        
        try:
            with self.graph.as_default():
                with self.sess.as_default():
                    # Load PhaseNet model
                    self.model = UNet(mode="pred")
                    
                    # Load model weights
                    model_path = "models/phasenet/base"
                    if os.path.exists(model_path):
                        saver = tf.compat.v1.train.Saver()
                        saver.restore(self.sess, tf.train.latest_checkpoint(model_path))
                        print("PhaseNet model loaded successfully")
                        self.model_loaded = True
                    else:
                        print(f"PhaseNet model path not found: {model_path}")
                        self.model_loaded = False
        except Exception as e:
            print(f"Error loading PhaseNet model: {e}")
            self.model_loaded = False

    def preprocess_data(self, data: np.ndarray) -> np.ndarray:
        """
        Preprocess data for PhaseNet with resampling based on sampling rate
        Input: (600+, 3) at 20 Hz -> Output: (1, 3000, 1, 3) at 100 Hz

        This is because PhaseNet requires 3000 points at 100 Hz, but we have 20 Hz data.
        """
        original_length = data.shape[0]
        
        # Check if input data is too short
        if original_length < self.MIN_INPUT_LENGTH:
            raise ValueError(f"Input data is too short. Minimum required is {self.MIN_INPUT_LENGTH} points, "
                 f"but received {original_length} points")
        
        # Calculate the ratio of resampling based on sampling rate
        # From 20 Hz to 100 Hz = 5x more data points
        resample_ratio = self.PHASENET_SAMPLING_RATE / self.INPUT_SAMPLING_RATE  # 100/20 = 5
        
        # Calculate the required input length at 20 Hz to produce 3000 points at 100 Hz
        required_input_length = int(self.PHASENET_LENGTH / resample_ratio)  # 3000/5 = 600
        
        # If input is longer than required, take the first part
        if original_length > required_input_length:
            data = data[:required_input_length, :]
            original_length = required_input_length
        
        # Resample from 20 Hz to 100 Hz using linear interpolation
        target_length = int(original_length * resample_ratio)  # Should produce 3000
        
        # Create interpolation function for each channel
        resampled_data = np.zeros((target_length, 3))
        
        for channel in range(3):
            # Time indices for original data (20 Hz)
            original_time = np.arange(original_length) / self.INPUT_SAMPLING_RATE
            # Time indices for target data (100 Hz)
            target_time = np.arange(target_length) / self.PHASENET_SAMPLING_RATE
            
            # Interpolate
            f = interp1d(original_time, data[:, channel], kind='linear', 
                        bounds_error=False, fill_value='extrapolate')
            resampled_data[:, channel] = f(target_time)
        
        # Make sure data length is exactly 3000 points
        if target_length != self.PHASENET_LENGTH:
            # If not exactly 3000, do interpolation again
            final_data = np.zeros((self.PHASENET_LENGTH, 3))
            for channel in range(3):
                original_indices = np.linspace(0, 1, target_length)
                target_indices = np.linspace(0, 1, self.PHASENET_LENGTH)
                f = interp1d(original_indices, resampled_data[:, channel], kind='linear')
                final_data[:, channel] = f(target_indices)
            resampled_data = final_data
        
        # Normalize data (important for PhaseNet)
        for channel in range(3):
            channel_data = resampled_data[:, channel]
            if np.std(channel_data) > 0:
                resampled_data[:, channel] = (channel_data - np.mean(channel_data)) / np.std(channel_data)
        
        # Reshape for PhaseNet: (1, 3000, 1, 3)
        processed_data = resampled_data.reshape(1, self.PHASENET_LENGTH, 1, 3)
        
        return processed_data

    def postprocess_predictions(self, predictions: np.ndarray, start_time: str, station_code: str) -> Tuple[int, int]:
        """
        Postprocess PhaseNet predictions to get P and S picks
        """
        # PhaseNet output shape: (1, 3000, 1, 3) -> (P, S, N)
        # Channel 0: P-wave probability
        # Channel 1: S-wave probability  
        # Channel 2: Noise probability
        
        pred_p = predictions[0, :, 0, 0]  # P-wave predictions
        pred_s = predictions[0, :, 0, 1]  # S-wave predictions
        
        # Detect peaks with threshold
        p_threshold = 0.3
        s_threshold = 0.3
        mpd = 50  # minimum peak distance
        
        # Detect P-wave picks
        p_indices, p_probs = detect_peaks(pred_p, mph=p_threshold, mpd=mpd)
        
        # Detect S-wave picks
        s_indices, s_probs = detect_peaks(pred_s, mph=s_threshold, mpd=mpd)
        
        # Convert from 3000-point space (100 Hz) to input space (20 Hz)
        # Conversion ratio based on sampling rate
        scale_factor = self.INPUT_SAMPLING_RATE / self.PHASENET_SAMPLING_RATE  # 20/100 = 0.2
        
        p_index = -1
        s_index = -1
        
        if len(p_indices) > 0:
            # Take the first pick with highest confidence
            best_p_idx = np.argmax(p_probs)
            # Convert from 100 Hz space to 20 Hz space
            p_index = int(p_indices[best_p_idx] * scale_factor)
            
        if len(s_indices) > 0:
            # Take the first pick with highest confidence
            best_s_idx = np.argmax(s_probs)
            # Convert from 100 Hz space to 20 Hz space
            s_index = int(s_indices[best_s_idx] * scale_factor)
        
        # Ensure indices are within bounds (maximum 600 for 20 Hz input)
        max_input_index = self.MIN_INPUT_LENGTH - 1
        if p_index >= max_input_index:
            p_index = -1
        if s_index >= max_input_index:
            s_index = -1
            
        return p_index, s_index

    def predict(self, x: List[List[float]], start_time: str, station_code: str) -> Dict[str, Any]:
        """
        Predict P and S waves using PhaseNet model
        """
        if not self.model_loaded:
            return {
                "station_code": station_code,
                "init_end": True,
                "p_arr": False,
                "p_arr_time": start_time,
                "p_arr_index": -1,
                "s_arr": False,
                "s_arr_time": start_time,
                "s_arr_index": -1,
                "model_type": "phasenet_error",
                "error": "PhaseNet model not loaded"
            }
        
        try:
            # Convert to numpy array
            data = np.array(x)  # Shape: (600+, 3) - minimum 600 points for 20 Hz
            
            # Check if input length is valid
            if data.shape[0] < self.MIN_INPUT_LENGTH:
                return {
                    "station_code": station_code,
                    "init_end": True,
                    "p_arr": False,
                    "p_arr_time": start_time,
                    "p_arr_index": -1,
                    "s_arr": False,
                    "s_arr_time": start_time,
                    "s_arr_index": -1,
                    "model_type": "phasenet_error",
                    "error": f"Input data is too short. Minimum required is {self.MIN_INPUT_LENGTH} points, received {data.shape[0]} points"
                }
            
            # Preprocess data for PhaseNet (20 Hz -> 100 Hz resampling)
            processed_data = self.preprocess_data(data)
            
            # Run PhaseNet prediction
            with self.graph.as_default():
                with self.sess.as_default():
                    predictions = self.sess.run(self.model.preds, 
                                              feed_dict={self.model.X: processed_data,
                                                       self.model.drop_rate: 0,
                                                       self.model.is_training: False})
            
            # Postprocess predictions
            p_index, s_index = self.postprocess_predictions(predictions, start_time, station_code)
            
            # Calculate arrival times
            start_dt = datetime.strptime(start_time, self.DATETIME_FORMAT)
            
            if p_index != -1:
                p_arr_time = start_dt + timedelta(seconds=p_index / self.INPUT_SAMPLING_RATE)
                p_arr_time_str = p_arr_time.strftime(self.DATETIME_FORMAT)
                p_detected = True
            else:
                p_arr_time_str = start_time
                p_detected = False
                
            if s_index != -1:
                s_arr_time = start_dt + timedelta(seconds=s_index / self.INPUT_SAMPLING_RATE)
                s_arr_time_str = s_arr_time.strftime(self.DATETIME_FORMAT)
                s_detected = True
            else:
                s_arr_time_str = start_time
                s_detected = False

            return {
                "station_code": station_code,
                "init_end": True,
                "p_arr": p_detected,
                "p_arr_time": p_arr_time_str,
                "p_arr_index": p_index,
                "s_arr": s_detected,
                "s_arr_time": s_arr_time_str,
                "s_arr_index": s_index,
                "model_type": "phasenet"
            }
            
        except Exception as e:
            print(f"Error in PhaseNet prediction: {e}")
            return {
                "station_code": station_code,
                "init_end": True,
                "p_arr": False,
                "p_arr_time": start_time,
                "p_arr_index": -1,
                "s_arr": False,
                "s_arr_time": start_time,
                "s_arr_index": -1,
                "model_type": "phasenet_error",
                "error": str(e)
            }

    def predict_stats(self, x: List[List[float]], station_code: str) -> Dict[str, Any]:
        """
        PhaseNet doesn't predict magnitude/distance, return default values
        """
        return {
            "station_code": station_code,
            "magnitude": 0.0,
            "depth": 0.0,
            "distance": 0.0,
            "model_type": "phasenet",
            "note": "PhaseNet does not predict earthquake statistics"
        } 