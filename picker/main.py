from picker.injector import InjectorContainer
from picker.src.config_service import Config


def main():
    container = InjectorContainer()
    container.provider_config.from_dict({
        'kafka_config': {
            'bootstrap.servers': Config.BOOTSTRAP_SERVERS,
            'group.id': 'picker',
            'auto.offset.reset': 'latest',
        }
    }, True)

    processor = container.processor()
    processor.consume(Config.CONSUMER_TOPIC)

if __name__ == "__main__":
    main()