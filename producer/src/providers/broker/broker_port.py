from abc import ABC, abstractmethod
from typing import Any, Optional


class BrokerPort(ABC):
    @abstractmethod
    def start_trace(self):
        raise NotImplementedError()

    @abstractmethod
    def stop_trace(self):
        raise NotImplementedError()

    @abstractmethod
    def produce_message(self, value: Any, key: Optional[str] = None):
        raise NotImplementedError()