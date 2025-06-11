package app

import (
	"context"
	"server/internal/domain"
	port "server/internal/port/station"
)

type StationService struct {
	stationRepo port.StationRepository
}

func NewStationService(stationRepo port.StationRepository) *StationService {
	return &StationService{
		stationRepo: stationRepo,
	}
}

func (s *StationService) GetAll(ctx context.Context) (stations []domain.Station, err error) {
	return s.stationRepo.GetAll(ctx)
}

func (s *StationService) Get(ctx context.Context, code string) (station *domain.Station, err error) {
	return s.stationRepo.Get(ctx, code)
}

func (s *StationService) Toggle(ctx context.Context, code string, isEnabled bool) (err error) {
	return s.stationRepo.Update(
		ctx,
		map[string]any{
			"is_enabled": isEnabled,
		},
		code,
	)
}
