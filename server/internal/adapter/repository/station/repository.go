package adapter

import (
	"context"
	"errors"
	sq "github.com/Masterminds/squirrel"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"server/internal/domain"
	port "server/internal/port/station"
)

type stationRepo struct {
	db *pgxpool.Pool
	sb sq.StatementBuilderType
}

func NewStationRepo(db *pgxpool.Pool) port.StationRepository {
	return &stationRepo{
		db: db,
		sb: sq.StatementBuilder.PlaceholderFormat(sq.Dollar),
	}
}

func (s stationRepo) GetAll(ctx context.Context) (stations []domain.Station, err error) {
	queryStatement := s.sb.Select(
		"code", "latitude", "longitude",
		"elevation", "nearest_stations", "is_enabled",
	).From("stations").OrderBy("code")

	query, args, err := queryStatement.ToSql()
	if err != nil {
		return nil, err
	}

	rows, err := s.db.Query(context.Background(), query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	for rows.Next() {
		station := domain.Station{}

		if err = rows.Scan(
			&station.Code,
			&station.Latitude,
			&station.Longitude,
			&station.Elevation,
			&station.NearestStations,
			&station.IsEnabled,
		); err != nil {
			return nil, err
		}

		stations = append(stations, station)
	}

	return stations, nil
}

func (s stationRepo) Get(ctx context.Context, code string) (station *domain.Station, err error) {
	queryStatement := s.sb.Select(
		"code", "latitude", "longitude",
		"elevation", "nearest_stations", "is_enabled",
	).From("stations").Where(sq.Eq{"code": code})

	query, args, err := queryStatement.ToSql()
	if err != nil {
		return nil, err
	}

	station = &domain.Station{}

	if err = s.db.QueryRow(ctx, query, args...).Scan(
		&station.Code,
		&station.Latitude,
		&station.Longitude,
		&station.Elevation,
		&station.NearestStations,
		&station.IsEnabled,
	); err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, nil
		}

		return nil, err
	}

	return station, nil
}
