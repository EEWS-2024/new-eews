import json
import time
from datetime import datetime
from typing import Optional, Any

from fastapi.params import Depends
from obspy.clients.seedlink import EasySeedLinkClient
from obspy.clients.seedlink.slpacket import SLPacket

from producer.src.providers.broker.broker_port import BrokerPort
from producer.src.providers.broker.kafka_adapter import KafkaAdapter
from producer.src.providers.cache.cache_port import CachePort
from producer.src.providers.cache.redis_adapter import RedisAdapter
from producer.src.providers.database.database_port import DatabasePort
from producer.src.providers.database.postgres_adapter import PostgresAdapter
from producer.src.providers.obspy.obspy_port import ObspyPort
from producer.src.services.config_service import ConfigService
from producer.src.utilities.trace_mapper import trace_mapper


class SeedLinkAdapter(ObspyPort, EasySeedLinkClient):
    def __init__(
            self,
            config: ConfigService = Depends(ConfigService),
            broker: BrokerPort = Depends(KafkaAdapter),
            database: DatabasePort = Depends(PostgresAdapter),
            cache: CachePort = Depends(RedisAdapter)
    ):
        self.broker = broker
        self.cache = cache
        self.database = database
        super().__init__(database)
        EasySeedLinkClient.__init__(self, server_url=config.SEED_LINK_URL)
        self.__select_stream()
        self.experiment_attempt = 0
        self.experiment_execution_times = []
        self.experiment_processed_data = []

    def __select_stream(self):
        for station in self.enabled_station_codes:
            self.select_stream(net="GE", station=station, selector="BH?")

    def __run(self):
        if not len(self.conn.streams):
            raise Exception(
                "No streams specified. Use select_stream() to select a stream"
            )
        print("Starting collection on:", datetime.now())
        service_start_time = time.time()
        experiment_data_count = 0
        while True:  # Stop condition
            experiment_start_time = time.time()

            if not self.cache.is_exists("streaming_flag"):
                self.close()
                break

            print("Collecting data...")
            data = self.conn.collect()

            if data == SLPacket.SLTERMINATE:
                self.on_terminate()
                break
            elif data == SLPacket.SLERROR:
                self.on_seedlink_error()
                continue

            assert isinstance(data, SLPacket)
            packet_type = data.get_type()
            if packet_type not in (SLPacket.TYPE_SLINF, SLPacket.TYPE_SLINFT):
                message = trace_mapper(data.get_trace())
                if message["station"] in self.enabled_station_codes:
                    self.broker.produce_message(message, message["station"])
                    experiment_data_count += 1
                    if time.time() - experiment_start_time >= 1:
                        self.experiment_processed_data.append(experiment_data_count)
                        experiment_data_count = 0

            end_time = time.time()
            self.experiment_execution_times.append(end_time - experiment_start_time)
            if end_time - service_start_time >= 60:
                self.save_experiment()
                self.experiment_attempt += 1
                service_start_time = time.time()
                if self.experiment_attempt == 5:
                    self.stop_streaming()

    def start_streaming(self, start_time: Optional[Any] = 0, end_time: Optional[Any] = 0):
        self.broker.start_trace()
        if not self.cache.is_exists("streaming_flag"):
            self.cache.set("streaming_flag", 1)
            self.__run()

    def stop_streaming(self):
        self.broker.stop_trace()
        self.cache.destroy("streaming_flag")
        print("Stopping SeedLink client")

    def save_experiment(self):
        experiment_execution_time = self.experiment_execution_times[1:] if self.experiment_attempt == 0 else self.experiment_execution_times

        stats_data = {
            "execution_times": experiment_execution_time,
            "processed_data": self.experiment_processed_data
        }
        with open(f"./out/experiment_stats_{self.experiment_attempt}.json", "w") as f:
            json.dump(stats_data, f, indent=4)

        self.experiment_execution_times = []
        self.experiment_processed_data = []