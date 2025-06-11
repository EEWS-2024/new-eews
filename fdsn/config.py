import os

from flask.cli import load_dotenv

load_dotenv()

class Config:
    FDSN_URL = os.getenv('FDSN_URL', 'GEOFON')
    KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'archive')
