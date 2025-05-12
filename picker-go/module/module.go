package module

import (
	"picker-go/core/poller/port"
	"picker-go/internal/config"
	"picker-go/internal/poller"
	"picker-go/internal/poller/adapter"
)

func Initialize() (*config.Config, *poller.Poller, error) {
	cfg, err := config.LoadConfig()
	if err != nil {
		return nil, nil, err
	}

	var consumer port.BrokerConsumer
	consumer, err = adapter.NewConsumer(cfg.KafkaBootstrapServers, cfg.KafkaGroupID)
	if err != nil {
		return nil, nil, err
	}

	p := poller.NewPoller(consumer)
	return cfg, p, nil
}
