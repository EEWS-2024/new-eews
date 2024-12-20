from datetime import datetime, timedelta
import time
from typing import Dict

from obspy import Trace

from producer.src.services.preprocess_service_interface import PreprocessServiceInterface


class PreprocessService(PreprocessServiceInterface):
    def __init__(self):
        self.station_start_time: Dict[str, datetime] = {}

    def reset(self):
        self.station_start_time: Dict[str, datetime] = {}

    def impute(self, trace_data: Trace):
        start_time = datetime.strptime(
            str(trace_data.stats.starttime),
            '%Y-%m-%dT%H:%M:%S.%fZ'
        )
        station = trace_data.stats.station
        channel = trace_data.stats.channel
        sampling_rate = trace_data.stats.sampling_rate
        data = trace_data.data.tolist()

        if not station in self.station_start_time:
            self.station_start_time[station] = start_time

        time_diff = start_time - self.station_start_time[station]

        missing_samples = int(time_diff.total_seconds() * sampling_rate)
        if missing_samples > 0:
            missing_data = [0] * missing_samples
            data = missing_data + data

        time_to_add = timedelta(seconds=len(data) / sampling_rate)
        end_time = self.station_start_time[station] + time_to_add

        return {
            "type": "trace",
            "network": trace_data.stats.network,
            "station": station,
            "channel": channel,
            "location": trace_data.stats.location,
            "start_time": self.station_start_time[station].isoformat(),
            "end_time": end_time.isoformat(),
            "delta": trace_data.stats.delta,
            "npts": trace_data.stats.npts,
            "calib": trace_data.stats.calib,
            "data": data,
            "len": len(data),
            "sampling_rate": trace_data.stats.sampling_rate,
            "published_at": time.time(),
        }