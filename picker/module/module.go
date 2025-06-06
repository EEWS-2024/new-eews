package module

import (
	"context"
	"github.com/jackc/pgx/v5/pgxpool"
	"picker/internal/config"
	"picker/internal/poller"
)

func Initialize() (*config.Config, *poller.Poller, error) {
	cfg, err := config.LoadConfig()
	if err != nil {
		return nil, nil, err
	}

	db, err := pgxpool.New(context.Background(), cfg.DatabaseUrl)
	if err != nil {
		return nil, nil, err
	}

	p := poller.NewPoller(cfg, db)
	return cfg, p, nil
}
