import datetime
import json
import threading
import time
from typing import List

from confluent_kafka import Producer
from obspy.clients.seedlink import EasySeedLinkClient
from obspy.clients.seedlink.slpacket import SLPacket

from app.config import Config


class SeedlinkProvider:
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

    def stream_data(self, stations: List[str], ):
        client = EasySeedLinkClient(server_url=Config.SEEDLINK_URL)
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
                        trace_data = {
                            "network": trace.stats.network,
                            "station": trace.stats.station,
                            "channel": trace.stats.channel,
                            "location": trace.stats.location,
                            "starttime": str(trace.stats.starttime),
                            "endtime": str(trace.stats.endtime),
                            "delta": trace.stats.delta,
                            "npts": trace.stats.npts,
                            "calib": trace.stats.calib,
                            "data": trace.data.tolist(),
                            "len": len(trace.data.tolist()),
                            "sampling_rate": trace.stats.sampling_rate,
                            "arrival_time": arrival_time,
                        }

                        self.producer.produce(
                            Config.KAFKA_TOPIC,
                            value=json.dumps(trace_data),
                            key=f"{trace.stats.station}",
                        )
                        self.producer.flush()
                        print(f"Produced message for station {trace.stats.station}")