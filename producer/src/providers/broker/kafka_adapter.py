import json
import pickle
from typing import Any, Optional

from confluent_kafka import Producer
from fastapi.params import Depends

from .broker_port import BrokerPort
from ...services.config_service import ConfigService


class KafkaAdapter(BrokerPort):
    def __init__(self, config: ConfigService = Depends(ConfigService)):
        self.producer = Producer({"bootstrap.servers": config.BOOTSTRAP_SERVERS})
        self.producer_topic = config.PRODUCER_TOPIC
        self.serializer = pickle.dumps

        try:
            self.partitions = len(
                self.producer.list_topics(self.producer_topic).topics.get(self.producer_topic).partitions
            )
        except Exception as e:
            print(e)
            self.partitions = 3

    def start_trace(self):
        for i in range(0, self.partitions):
            self.producer.produce(
                self.producer_topic,
                value=self.serializer(json.dumps({"type": "start"})),
                partition=i,
                key="start",
            )
        self.producer.flush()

    def stop_trace(self):
        for i in range(0, self.partitions):
            self.producer.produce(
                self.producer_topic,
                value=self.serializer(json.dumps({"type": "stop"})),
                partition=i,
                key="stop",
            )
        self.producer.flush()

    def produce_message(self, value: Any, key: Optional[str] = None):
        self.producer.produce(
            self.producer_topic,
            value=self.serializer(json.dumps(value)),
            key=key,
        )

        self.producer.flush()