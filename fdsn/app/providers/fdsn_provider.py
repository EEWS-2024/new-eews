import json
import threading
from datetime import timedelta
from typing import List

from confluent_kafka import Producer
from obspy.clients.fdsn import Client

from config import Config


class FdsnProvider:
    def __init__(self):
        self.network = "GE"
        self.channel = "BH?"
        self.selected_channels = ["BHZ", "BHN", "BHE"]
        self.stop_event = threading.Event()
        self.producer = Producer({
            "bootstrap.servers": Config.KAFKA_BOOTSTRAP_SERVERS,
        })

    def clear_stream(self):
        self.stop_event.clear()

    def stop_stream(self):
        self.stop_event.set()

    def stream_data(
        self,
        stations: List[str],
        start_time: str,
        end_time: str,
        app
    ):
        with app.app_context():
            client = Client(base_url=Config.FDSN_URL)
            traces = client.get_waveforms_bulk(
                bulk=[
                    (self.network, station, "*", self.channel, start_time, end_time)
                    for station in stations
                ]
            )

            for trace in traces:
                if trace.stats.channel in self.selected_channels:
                    trace_data_point = trace.data.tolist()
                    trace_start_time = trace.stats.starttime
                    while len(trace_data_point) > 382:
                        data_points = trace_data_point[:382]
                        trace_end_time = trace_start_time + timedelta(seconds=20)
                        data = {
                            "network": trace.stats.network,
                            "station": trace.stats.station,
                            "channel": trace.stats.channel,
                            "location": trace.stats.location,
                            "start_time": str(trace_start_time),
                            "end_time": str(trace_end_time),
                            "delta": trace.stats.delta,
                            "npts": len(data_points),
                            "calib": trace.stats.calib,
                            "data": data_points,
                            "sampling_rate": trace.stats.sampling_rate,
                        }
                        self.producer.produce(
                            Config.KAFKA_TOPIC,
                            value=json.dumps(data),
                            key=f"{trace.stats.station}",
                        )
                        self.producer.flush()
                        print(f"Produced message for station {trace.stats.station}")
                        trace_start_time = trace_end_time
                        trace_data_point = trace_data_point[382:]

