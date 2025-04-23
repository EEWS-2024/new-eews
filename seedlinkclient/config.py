import os

from flask.cli import load_dotenv

load_dotenv()

class Config:
    SEEDLINK_URL = os.getenv('SEEDLINK_URL', 'http://localhost:8000')
    KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'trace')
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:postgres@localhost:5432/seismic'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False