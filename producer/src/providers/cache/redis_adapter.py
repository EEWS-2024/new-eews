import redis
from fastapi.params import Depends

from producer.src.providers.cache.cache_port import CachePort
from producer.src.services.config_service import ConfigService


class RedisAdapter(CachePort):
    def __init__(self, config: ConfigService = Depends(ConfigService)):
        self.cache = redis.Redis(
            host=config.REDIS_HOST,
            port=int(config.REDIS_PORT),
        )

    def get(self, key):
        return self.cache.get(key)

    def set(self, key, value):
        self.cache.set(key, value)

    def destroy(self, key):
        self.cache.delete(key)

    def is_exists(self, key):
        return self.cache.exists(key)
