import os
from app.container import KafkaContainer
from dotenv import load_dotenv

load_dotenv()

BOOTSTRAP_SERVERS = os.getenv("BOOTSTRAP_SERVERS", "85.209.163.202:9103")
TOPIC_CONSUMER = os.getenv("BOOTSTRAP_SERVERS", "p_arrival")
REDIS_HOST = os.getenv("REDIS_HOST", "85.209.163.202")
REDIS_PORT = os.getenv("REDIS_PORT", "6381")
MONGO_DB = os.getenv("MONGO_DB", "eews")
MONGO_HOST = os.getenv("MONGO_HOST", "85.209.163.202")
MONGO_PORT = os.getenv("MONGO_PORT", "27019")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "parameters")

if __name__ == "__main__":
    container = KafkaContainer()
    container.config.from_dict(
        {
            "bootstrap_servers": BOOTSTRAP_SERVERS,
            "kafka_config": {
                "bootstrap.servers": BOOTSTRAP_SERVERS,
                "group.id": "picker",
                "auto.offset.reset": "latest",
            },
            "redis": {
                "host": REDIS_HOST,
                "port": int(REDIS_PORT),
            },
            "mongo": {
                "db_name": MONGO_DB,
                "host": MONGO_HOST,
                "port": int(MONGO_PORT),
                "collection": MONGO_COLLECTION,
            },
        },
        True,
    )
    
    data_processor = container.data_processor()
    print("=" * 20 + f"Consuming Data From {TOPIC_CONSUMER} Topic" + "=" * 20)
    data_processor.consume(TOPIC_CONSUMER)
