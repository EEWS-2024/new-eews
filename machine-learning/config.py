import os

from flask.cli import load_dotenv

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:postgres@localhost:5432/ml_db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False