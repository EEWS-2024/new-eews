package accessor

import (
	"context"
	"errors"
	sq "github.com/Masterminds/squirrel"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

type Station struct {
	Code            string   `json:"code"`
	Latitude        float64  `json:"latitude"`
	Longitude       float64  `json:"longitude"`
	Elevation       float64  `json:"elevation"`
	NearestStations []string `json:"nearest_stations"`
	IsEnabled       bool     `json:"is_enabled"`
}

type StationAccessor struct {
	db *pgxpool.Pool
	sb sq.StatementBuilderType
}

func NewStationAccessor(db *pgxpool.Pool) *StationAccessor {
	sb := sq.StatementBuilder.
		PlaceholderFormat(sq.Dollar)
	return &StationAccessor{
		sb: sb,
		db: db,
	}
}

func (a *StationAccessor) GetByStationCode(code string) (station *Station, err error) {
	queryStatement := a.sb.Select(
		"code", "latitude", "longitude",
		"elevation", "nearest_stations", "is_enabled",
	).From("stations").Where(sq.Eq{"code": code, "is_enabled": true})

	query, args, err := queryStatement.ToSql()
	if err != nil {
		return nil, err
	}

	ctx := context.Background()

	station = &Station{}

	if err = a.db.QueryRow(ctx, query, args...).Scan(
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

func (a *StationAccessor) GetByStationCodes(codes []string) (stations []*Station, err error) {
	queryStatement := a.sb.Select(
		"code", "latitude", "longitude",
		"elevation", "nearest_stations", "is_enabled",
	).From("stations").Where(sq.Eq{"code": codes})

	query, args, err := queryStatement.ToSql()
	if err != nil {
		return nil, err
	}

	rows, err := a.db.Query(context.Background(), query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	for rows.Next() {
		station := Station{}

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

		stations = append(stations, &station)
	}

	return stations, nil
}
