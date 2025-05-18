import datetime
import json
import threading
from typing import List

from confluent_kafka import Producer
from obspy.clients.seedlink import EasySeedLinkClient
from obspy.clients.seedlink.slpacket import SLPacket

from app.handlers.data_poll_handler import DataPollHandler
from config import Config


class SeedlinkProvider:
    def __init__(
        self,
    ):
        self.network = "GE"
        self.channel = "BH?"
        self.selected_channels = ["BHZ", "BHN", "BHE"]
        self.stop_event = threading.Event()
        self.producer = Producer({
            "bootstrap.servers": Config.KAFKA_BOOTSTRAP_SERVERS,
        })
        self.poll_data_handler: DataPollHandler | None = None

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
        time_to_add = datetime.timedelta(seconds=382 / stats.sampling_rate)

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
            "type": "live",
        }

        self.producer.produce(
            Config.KAFKA_TOPIC,
            value=json.dumps(trace_data),
            key=f"{stats.station}",
        )
        self.producer.flush()
        print(f"Produced message for station {stats.station}")


    def stream_data(self, stations: List[str], app, poll_data):
        with app.app_context():
            client = EasySeedLinkClient(server_url=Config.SEEDLINK_URL)

            self.poll_data_handler = poll_data()
            for station in stations:
                client.select_stream(net=self.network, station=station, selector=self.channel)

            while not self.stop_event.is_set():
                data = client.conn.collect()
                if data == SLPacket.SLTERMINATE:
                    # Send termination status to core server
                    print("Connection terminated")
                    client.on_terminate()
                if data == SLPacket.SLERROR:
                    # Send error status to core server
                    print("Connection error")
                    client.on_seedlink_error()
                if isinstance(data, SLPacket):
                    packet_type = data.get_type()
                    if packet_type not in (SLPacket.TYPE_SLINF, SLPacket.TYPE_SLINFT):
                        trace = data.get_trace()
                        if trace.stats.channel in self.selected_channels:
                            client.on_data(trace)
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
