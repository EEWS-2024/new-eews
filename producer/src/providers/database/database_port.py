from abc import ABC, abstractmethod

from sqlalchemy.orm import Session


class DatabasePort(ABC):
    @abstractmethod
    def execute(self, statement):
        raise NotImplementedError()

