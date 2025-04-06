import pickle
from abc import ABC, abstractmethod
from typing import List, Optional

import numpy as np
from redis import Redis


class Pipeline(ABC):
    def __init__(
        self,
        redis: Optional[Redis] = None,
        function_name: Optional[str] = "",
    ):
        self.redis = redis
        self.function_name = function_name

    @abstractmethod
    def compute(self, x: np.ndarray, station_code: Optional[str] = "") -> np.ndarray:
        pass

    def set_initial_state(self, x: np.ndarray, station_code: str) -> None:
        pass

    def set(self, x: np.ndarray, station_code: str):
        self.redis.set(f"{station_code}_{self.function_name}", x.dumps())

    def get(self, station_code: str) -> np.ndarray | None:
        if not self.redis.exists(f"{station_code}_{self.function_name}"):
            return None
        return pickle.loads(self.redis.get(f"{station_code}_{self.function_name}"))


class Slope(Pipeline):
    def __init__(
        self,
        redis: Redis,
        sampling_rate: float
    ):
        super().__init__(
            redis,
            "slope"
        )
        self.sampling_rate = sampling_rate

    def compute(self, x: np.ndarray, station_code: Optional[str] = "") -> np.ndarray:
        prev_val = self.get(station_code)
        first_slope = (x[0] - prev_val) * self.sampling_rate
        rest_slope = (x[1:] - x[:-1]) * self.sampling_rate
        self.set(rest_slope[-1:], station_code)
        return np.concatenate([first_slope, rest_slope], axis=0)

    def set_initial_state(self, x: np.ndarray, station_code: str) -> None:
        self.set(x[:1], station_code)

class MultiExponentialSmoothing(Pipeline):
    def __init__(
        self,
        redis: Redis,
        alpha: List[float],
        avg_until: int = 0
    ):
        super().__init__(
            redis,
            "mema"
        )

        for a in alpha:
            assert 0.0 <= a <= 1.0, "Alpha must be in range [0.0, 1.0]"

        self.alpha = np.array(alpha)
        self.alpha_ = 1 - self.alpha
        self.avg_until = avg_until

    def compute(self, x: np.ndarray, station_code: Optional[str] = "") -> np.ndarray:
        ema_vals: List[np.ndarray] = []
        prev_ema_val = self.get(station_code)
        for val in x:
            curr_ema_val = prev_ema_val * self.alpha + val * self.alpha_
            prev_ema_val = curr_ema_val
            ema_vals.append(curr_ema_val)
        self.set(ema_vals[-1], station_code)
        return np.array(ema_vals)

    def set_initial_state(self, x: np.ndarray, station_code: str) -> None:
        if self.avg_until > 0:
            self.set(np.mean(x[:self.avg_until], axis=0), station_code)
        else:
            self.set(np.zeros(self.alpha.shape[0]), station_code)


class Square(Pipeline):
    def compute(self, x: np.ndarray, station_code: Optional[str] = "") -> np.ndarray:
        return x*x


class Log1P(Pipeline):
    def compute(self, x: np.ndarray, station_code: Optional[str] = "") -> np.ndarray:
        return np.log1p(x)


class AddChannels(Pipeline):
    def compute(self, x: np.ndarray, station_code: Optional[str] = "") -> np.ndarray:
        return np.sum(x, axis=-1, keepdims=True)


class PairwiseRatio(Pipeline):
    def __init__(
        self,
        alpha: List[float]
    ):
        super().__init__()

        # Generate Order
        idx_area = [(i, 1-a) for i, a in enumerate(alpha)]
        triplets = [(j, i, idx_area[i][1] / idx_area[j][1]) for i in range(len(alpha)) for j in range(len(alpha)) if
                    i > j]
        triplets = sorted(triplets, key=lambda t: t[2])
        self.order = [(t[0], t[1]) for t in triplets]


    def compute(self, x: np.ndarray, station_code: Optional[str] = "") -> np.ndarray:
        new_x = []
        for i, j in self.order:
            new_x.append((x[:,i]+1)/(x[:,j]+1))
        return np.array(new_x).T


class SlidingWindow(Pipeline):
    def __init__(
        self,
        redis: Redis,
        window_size: int,
        normalize_windows: bool =True
    ):
        super().__init__(
            redis,
            "sliwin"
        )

        self.window_size: int = window_size
        self.normalize_windows: bool = normalize_windows

    def compute(self, x: np.ndarray, station_code: Optional[str] = "") -> np.ndarray:

        uncut_windows = []
        cut_windows = []

        # Uncut windows
        for i in range(self.window_size, len(x)):
            uncut_windows.append(x[i-self.window_size:i])
        uncut_windows = np.array(uncut_windows)

        # Cut windows
        prev_window = self.get(station_code)
        for i in range(1, min(self.window_size, len(x))):
            cut_windows.append(np.concatenate([prev_window[i:], x[:i]]))
        cut_windows = np.array(cut_windows)

        # Update last windows
        windows: np.ndarray
        if uncut_windows.any():  # if uncut windows is not empty
            windows = np.concatenate([cut_windows, uncut_windows], axis=0)
        else:
            windows = cut_windows
        self.set(windows[-1], station_code)

        if self.normalize_windows:
            for i in range(len(windows)):
                windows_i = windows[i]
                windows_max = np.max(windows_i, axis=0)
                windows_min = np.min(windows_i, axis=0)

                windows[i] = (windows_i - windows_min) / (windows_max - windows_min)

        return windows

    def set_initial_state(self, x: np.ndarray, station_code: str) -> None:
        self.set(x[:self.window_size], station_code)