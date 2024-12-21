import json
from typing import Any, Optional

from confluent_kafka import Producer
from fastapi.params import Depends

from .broker_port import BrokerPort
from ...services.config_service import ConfigService


class KafkaAdapter(BrokerPort):
    def __init__(self, config: ConfigService = Depends(ConfigService)):
        self.producer = Producer({"bootstrap.servers": config.BOOTSTRAP_SERVERS})
        self.kafka_topic = config.KAFKA_TOPIC

        try:
            self.partitions = len(
                self.producer.list_topics(self.kafka_topic).topics.get(self.kafka_topic).partitions
            )
        except Exception as e:
            print(e)
            self.partitions = 3

    def start_trace(self):
        for i in range(0, self.partitions):
            self.producer.produce(
                self.kafka_topic,
                value=json.dumps({"type": "start"}),
                partition=i,
                key="start",
            )
        self.producer.flush()

    def stop_trace(self):
        for i in range(0, self.partitions):
            self.producer.produce(
                self.kafka_topic,
                value=json.dumps({"type": "stop"}),
                partition=i,
                key="stop",
            )
        self.producer.flush()

    def produce_message(self, value: Any, key: Optional[str] = None):
        self.producer.produce(
            self.kafka_topic,
            value=json.dumps(value),
            key=key,
        )

        self.producer.flush()