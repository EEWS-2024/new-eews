import os

from flask_sqlalchemy import SQLAlchemy
from redis import Redis


db = SQLAlchemy()

def init_redis():
    return Redis(
        host=os.getenv(
            "REDIS_HOST",
            "localhost"
        ),
        port=int(os.getenv(
            "REDIS_PORT",
            "6379"
        )),
    )