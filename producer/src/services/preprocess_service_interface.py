from abc import ABC, abstractmethod

from obspy import Trace


class PreprocessServiceInterface(ABC):
    @abstractmethod
    def reset(self):
        raise NotImplementedError()
    @abstractmethod
    def impute(self, trace_data: Trace):
        raise NotImplementedError()