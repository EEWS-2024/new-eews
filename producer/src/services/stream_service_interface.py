from abc import ABC, abstractmethod


class StreamServiceInterface(ABC):
    @abstractmethod
    def start_trace(self):
        pass