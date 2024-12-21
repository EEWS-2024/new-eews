import os

from dotenv import load_dotenv

load_dotenv()

class Config:
    BOOTSTRAP_SERVERS = os.environ.get("BOOTSTRAP_SERVERS")
    KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC")
    REDIS_HOST = os.environ.get("REDIS_HOST")
    REDIS_PORT = os.environ.get("REDIS_PORT")
    PIPELINE_MODEL_PATH = os.environ.get("PIPELINE_MODEL_PATH", "./static/pipelines/model_p_best.pipeline")
    P_INFERENCE_MODEL_PATH = os.environ.get("P_INFERENCE_MODEL_PATH", "./static/models/model_p_2_1_best.h5")
    S_INFERENCE_MODEL_PATH = os.environ.get("S_INFERENCE_MODEL_PATH", "./static/models/model_s_2_1_best.h5")
    MAGNITUDE_INFERENCE_MODEL_PATH = os.environ.get("MAGNITUDE_INFERENCE_MODEL_PATH", "./static/models/model_mag_1.h5")
    DISTANCE_INFERENCE_MODEL_PATH = os.environ.get("DISTANCE_INFERENCE_MODEL_PATH", "./static/models/model_dist_1.h5")
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")