import datetime
import json
import threading
import time
from typing import List

from confluent_kafka import Producer
from flask_sqlalchemy import SQLAlchemy
from obspy.clients.seedlink import EasySeedLinkClient
from obspy.clients.seedlink.slpacket import SLPacket

from config import Config
from app.models import Seismic


class SeedlinkProvider:
    def __init__(self, db: SQLAlchemy):
        self.network = "GE"
        self.channel = "BH?"
        self.selected_channels = ["BHZ", "BHN", "BHE"]
        self.stop_event = threading.Event()
        self.producer = Producer({
            "bootstrap.servers": Config.KAFKA_BOOTSTRAP_SERVERS,
        })
        self.db = db

    def clear_stream(self):
        self.stop_event.clear()

    def stop_stream(self):
        self.stop_event.set()

    def stream_data(self, stations: List[str], app):
        with app.app_context():
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
                                "start_time": str(trace.stats.starttime),
                                "end_time": str(trace.stats.endtime),
                                "delta": trace.stats.delta,
                                "npts": trace.stats.npts,
                                "calib": trace.stats.calib,
                                "data": trace.data.tolist(),
                                "sampling_rate": trace.stats.sampling_rate,
                                "arrival_time": arrival_time,
                            }

                            try:
                                self.db.session.add(
                                    Seismic(
                                        station_code=trace_data["station"],
                                        network=trace_data["network"],
                                        channel=trace_data["channel"],
                                        location=trace_data["location"],
                                        start_time=datetime.datetime.strptime(
                                            trace_data["start_time"], "%Y-%m-%dT%H:%M:%S.%fZ"
                                        ),
                                        end_time=datetime.datetime.strptime(
                                            trace_data["end_time"], "%Y-%m-%dT%H:%M:%S.%fZ"
                                        ),
                                        delta=trace_data["delta"],
                                        sample_rate=trace_data["sampling_rate"],
                                        length=trace_data["npts"],
                                        calib=trace_data["calib"],
                                        arrival_time=datetime.datetime.fromtimestamp(
                                            trace_data["arrival_time"]
                                        ),
                                        data=trace_data["data"],
                                    )
                                )

                                self.db.session.commit()
                            except Exception as e:
                                self.db.session.rollback()
                                print(f"Error saving to database: {e}")

                            self.producer.produce(
                                Config.KAFKA_TOPIC,
                                value=json.dumps(trace_data),
                                key=f"{trace.stats.station}",
                            )
                            self.producer.flush()
                            print(f"Produced message for station {trace.stats.station}")