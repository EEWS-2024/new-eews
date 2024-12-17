from sqlalchemy import MetaData, Table, create_engine, Column, Boolean
from sqlalchemy.orm import registry

from producer.src.services.config_service import ConfigService

mapper_registry = registry()
metadata = MetaData()

station_table = Table(
    "stations",
    metadata,
    autoload_with=create_engine(ConfigService.SQLALCHEMY_DATABASE_URI),
    schema="public"
)

class Station:
    is_enabled = Column(Boolean)

mapper_registry.map_imperatively(Station, station_table)