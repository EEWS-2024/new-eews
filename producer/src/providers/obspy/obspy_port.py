from abc import ABC, abstractmethod
from typing import Optional, Any

from sqlalchemy.future import select

from producer.src.models.station_model import Station
from producer.src.providers.database.database_port import DatabasePort


class ObspyPort(ABC):
    def __init__(self, database: DatabasePort):
        self.database = database
        self.enabled_station_codes = self.__get_enabled_station_codes()

    def __get_enabled_station_codes(self):
        enabled_stations = self.database.execute(select(Station).where(Station.is_enabled == True)).scalars().all()
        return set([station.code for station in enabled_stations])

    @abstractmethod
    def start_streaming(self, start_time: Optional[Any] = 0, end_time: Optional[Any] = 0):
        raise NotImplementedError()

    @abstractmethod
    def stop_streaming(self):
        raise NotImplementedError()