from sqlalchemy.orm import sessionmaker

from picker.src.config_service import Config
from sqlalchemy import create_engine


class DatabaseService:
    def __init__(self, config: Config):
        self.engine = create_engine(config.SQLALCHEMY_DATABASE_URI)

        session_local = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        self.session = session_local()

    def execute(self, statement):
        return self.session.execute(statement)