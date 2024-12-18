import os

from dotenv.main import load_dotenv

load_dotenv()

class ConfigService:
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")
    SEED_LINK_URL = os.environ.get("SEED_LINK_URL")
    BOOTSTRAP_SERVERS = os.environ.get("BOOTSTRAP_SERVERS")
    PRODUCER_TOPIC = os.environ.get("PRODUCER_TOPIC")
    REDIS_HOST = os.environ.get("REDIS_HOST")
    REDIS_PORT = os.environ.get("REDIS_PORT")
