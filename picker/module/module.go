package module

import (
	"context"
	"github.com/jackc/pgx/v5/pgxpool"
	"picker/core/poller/port"
	"picker/internal/config"
	"picker/internal/poller"
	"picker/internal/poller/adapter"
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

	db, err := pgxpool.New(context.Background(), cfg.DatabaseUrl)
	if err != nil {
		return nil, nil, err
	}

	p := poller.NewPoller(consumer, cfg, db)
	return cfg, p, nil
}
