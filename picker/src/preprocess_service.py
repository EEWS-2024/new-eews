from datetime import datetime, timedelta
import time
from typing import Dict, List

class PreprocessService:
    def __init__(self):
        self.station_start_time: Dict[str, datetime] = {}

    def reset(self):
        self.station_start_time: Dict[str, datetime] = {}

    def run(self, trace_data: Dict):
        start_time = datetime.strptime(
            str(trace_data["start_time"]),
            '%Y-%m-%dT%H:%M:%S.%fZ'
        )
        station = trace_data["station"]
        channel = trace_data["channel"]
        sampling_rate = trace_data["sampling_rate"]

        if not station in self.station_start_time:
            self.station_start_time[station] = start_time

        data = self.__impute(
            trace_data["data"],
            start_time,
            sampling_rate,
            station
        )

        time_to_add = timedelta(seconds=len(data) / sampling_rate)
        end_time = self.station_start_time[station] + time_to_add

        return {
            "type": "trace",
            "network": trace_data["network"],
            "station": station,
            "channel": channel,
            "location": trace_data["location"],
            "start_time": self.station_start_time[station].isoformat(),
            "end_time": end_time.isoformat(),
            "delta": trace_data["delta"],
            "npts": trace_data["npts"],
            "calib": trace_data["calib"],
            "data": data,
            "len": len(data),
            "sampling_rate": trace_data["sampling_rate"],
            "published_at": time.time(),
        }

    def __impute(self, data: List[int], start_time: datetime, sampling_rate: float, station: str):
        time_diff = start_time - self.station_start_time[station]

        missing_samples = int(time_diff.total_seconds() * sampling_rate)
        if missing_samples > 0:
            missing_data = [0] * missing_samples
            data = missing_data + data

        return data