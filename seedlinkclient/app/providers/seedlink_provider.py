import datetime
import json
import threading
import time
from typing import List

from confluent_kafka import Producer
from obspy.clients.seedlink import EasySeedLinkClient
from obspy.clients.seedlink.slpacket import SLPacket

from app.handlers.missing_data_handler import MissingDataHandler
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
        self.missing_data_handler: MissingDataHandler | None = None

    def clear_stream(self):
        self.stop_event.clear()

    def stop_stream(self):
        self.stop_event.set()

    def publish(
            self,
            stats,
            data,
            arrival_time
    ):
        current_time = stats.starttime.datetime
        if (
                stats.station in self.missing_data_handler.last_processed_time
                and stats.channel in self.missing_data_handler.last_processed_time[stats.station]
        ):
            current_time = self.missing_data_handler.last_processed_time[stats.station][stats.channel]

        self.missing_data_handler.data_pool[stats.station][stats.channel].extend(data)

        while len(self.missing_data_handler.data_pool[stats.station][stats.channel]) >= 382:
            data_to_send = self.missing_data_handler.data_pool[stats.station][stats.channel][:382]
            self.missing_data_handler.data_pool[stats.station][stats.channel] = self.missing_data_handler.data_pool[
                stats.station
            ][stats.channel][382:]
            time_to_add = datetime.timedelta(seconds=382 / stats.sampling_rate)

            trace_data = {
                "network": stats.network,
                "station": stats.station,
                "channel": stats.channel,
                "location": stats.location,
                "start_time": str(current_time),
                "end_time": str(current_time + time_to_add),
                "delta": stats.delta,
                "npts": stats.npts,
                "calib": stats.calib,
                "data": data_to_send,
                "sampling_rate": stats.sampling_rate,
                "arrival_time": arrival_time,
                "type": "live",
            }

            self.producer.produce(
                Config.KAFKA_TOPIC,
                value=json.dumps(trace_data),
                key=f"{stats.station}",
            )
            self.producer.flush()
            print(f"Produced message for station {stats.station}")
            current_time = current_time + time_to_add


    def stream_data(self, stations: List[str], app, missing_data_handler):
        with app.app_context():
            client = EasySeedLinkClient(server_url=Config.SEEDLINK_URL)
            self.missing_data_handler = missing_data_handler()
            for station in stations:
                client.select_stream(net=self.network, station=station, selector=self.channel)

            while not self.stop_event.is_set():
                data = client.conn.collect()
                arrival_time = time.time()
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
                            self.missing_data_handler.handle_missing_data(
                                trace.stats.station,
                                trace.stats.channel,
                                trace.stats.starttime.datetime,
                                trace.stats.sampling_rate,
                            )
                            self.publish(
                                trace.stats,
                                trace.data.tolist(),
                                arrival_time,
                            )
