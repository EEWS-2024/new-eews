from dependency_injector import containers, providers
from confluent_kafka import Consumer

from picker.src.config_service import Config
from picker.src.database_service import DatabaseService
from picker.src.inference_service import InferenceService
from picker.src.pooling_service import PoolingService
from picker.src.preprocess_service import PreprocessService
from picker.src.processor_service import ProcessorService
from picker.src.redis_service import RedisService


class InjectorContainer(containers.DeclarativeContainer):
    provider_config = providers.Configuration()
    consumer = providers.Singleton(
        Consumer,
        provider_config.kafka_config
    )
    config = providers.Singleton(Config)
    redis = providers.Singleton(
        RedisService,
        config=config
    )
    data_pooling = providers.Singleton(PoolingService)
    preprocess = providers.Singleton(PreprocessService)
    database = providers.Singleton(
        DatabaseService,
        config=config
    )
    inference = providers.Singleton(
        InferenceService,
        config=config
    )
    processor = providers.Factory(
        ProcessorService,
        data_pooling=data_pooling,
        preprocess=preprocess,
        inference=inference,
        database=database,
        consumer=consumer,
        redis=redis
    )