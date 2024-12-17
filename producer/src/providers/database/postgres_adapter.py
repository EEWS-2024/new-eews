from fastapi.params import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from producer.src.providers.database.database_port import DatabasePort
from producer.src.services.config_service import ConfigService


class PostgresAdapter(DatabasePort):
    def __init__(self, config: ConfigService = Depends(ConfigService)):
        self.engine = create_engine(config.SQLALCHEMY_DATABASE_URI)

        session_local = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        self.session = session_local()

    def execute(self, statement):
        return self.session.execute(statement)