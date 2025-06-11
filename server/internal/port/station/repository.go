package port

import (
	"context"
	"server/internal/domain"
)

type StationRepository interface {
	GetAll(ctx context.Context) (stations []domain.Station, err error)
	Get(ctx context.Context, code string) (station *domain.Station, err error)
	Update(ctx context.Context, data map[string]any, stationCode string) (err error)
	GetBy(ctx context.Context, conditions interface{}) (stations []domain.Station, err error)
}
