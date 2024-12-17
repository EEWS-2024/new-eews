from abc import ABC, abstractmethod


class StreamServiceInterface(ABC):
    @abstractmethod
    def start_trace(self):
        raise NotImplementedError()
    @abstractmethod
    def stop_trace(self):
        raise NotImplementedError()