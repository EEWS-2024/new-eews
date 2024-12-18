from abc import ABC, abstractmethod


class CachePort(ABC):
    @abstractmethod
    def get(self, key):
        raise NotImplementedError()
    @abstractmethod
    def set(self, key, value):
        raise NotImplementedError()
    @abstractmethod
    def destroy(self, key):
        raise NotImplementedError()
    @abstractmethod
    def is_exists(self, key):
        raise NotImplementedError()