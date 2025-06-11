import datetime
import json
import threading
from typing import List

from confluent_kafka import Producer
from obspy import UTCDateTime
from obspy.clients.fdsn import Client

from app.handlers.data_poll_handler import DataPollHandler
from config import Config


class FdsnProvider:
    def __init__(self):
        self.poll_data_handler: DataPollHandler | None = None
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

    def publish(
        self,
        stats,
        data,
        start_time
    ):
        time_to_add = datetime.timedelta(seconds=600 / stats.sampling_rate)

        trace_data = {
            "network": stats.network,
            "station": stats.station,
            "channel": stats.channel,
            "location": stats.location,
            "start_time": str(start_time),
            "end_time": str(start_time + time_to_add),
            "delta": stats.delta,
            "npts": stats.npts,
            "calib": stats.calib,
            "data": data,
            "sampling_rate": stats.sampling_rate,
            "type": "archive",
        }

        self.producer.produce(
            Config.KAFKA_TOPIC,
            value=json.dumps(trace_data),
            key=f"{stats.station}",
        )
        self.producer.flush()
        print(f"Produced message for station {stats.station}")

    def stream_data(
        self,
        stations: List[str],
        start_time: str,
        end_time: str,
        app,
        poll_data
    ):
        with app.app_context():
            client = Client(base_url=Config.FDSN_URL)
            traces = client.get_waveforms_bulk(
                bulk=[
                    (self.network, station, "*", self.channel, UTCDateTime(start_time), UTCDateTime(end_time))
                    for station in stations
                ]
            )

            self.poll_data_handler = poll_data()

            for trace in traces:
                if trace.stats.channel in self.selected_channels:
                    try:
                        trace_data, start_time = self.poll_data_handler.poll_data(
                            trace.stats.station,
                            trace.stats.channel,
                            trace.stats.starttime.datetime,
                            trace.data.tolist(),
                        )

                        if trace_data:
                            self.publish(
                                trace.stats,
                                trace_data,
                                start_time,
                            )
                    except Exception as e:
                        print(f"Error processing trace data: {e}")
                        continue