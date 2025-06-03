package accessor

import (
	"context"
	"errors"
	sq "github.com/Masterminds/squirrel"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"time"
)

type WaveForm struct {
	PickTime    time.Time `json:"pick_time"`
	StationCode string    `json:"station_code"`
	Depth       float64   `json:"depth"`
	Distance    float64   `json:"distance"`
	Magnitude   float64   `json:"magnitude"`
}

type WaveFormAccessor struct {
	db *pgxpool.Pool
	sb sq.StatementBuilderType
}

func NewWaveFormAccessor(db *pgxpool.Pool) *WaveFormAccessor {
	sb := sq.StatementBuilder.
		PlaceholderFormat(sq.Dollar)
	return &WaveFormAccessor{
		sb: sb,
		db: db,
	}
}

func (a *WaveFormAccessor) GetLatestByStationCode(stationCode string) (waveForm *WaveForm, err error) {
	queryStatement := a.sb.Select("pick_time", "station_code", "depth", "distance", "magnitude").From("waveforms").Where(sq.And{
		sq.Eq{"station_code": stationCode},
		sq.Eq{"is_new": true},
	}).
		OrderBy("pick_time DESC").
		Limit(1)

	query, args, err := queryStatement.ToSql()
	if err != nil {
		return nil, err
	}

	waveForm = &WaveForm{}

	if err = a.db.QueryRow(context.Background(), query, args...).Scan(
		&waveForm.PickTime,
		&waveForm.StationCode,
		&waveForm.Depth,
		&waveForm.Distance,
		&waveForm.Magnitude,
	); err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, nil
		}

		return nil, err
	}

	return waveForm, nil
}

func (a *WaveFormAccessor) Create(waveForm *WaveForm) (err error) {
	queryStatement := a.sb.Insert("waveforms").Columns("pick_time", "station_code", "depth", "distance", "magnitude").Values(waveForm.PickTime, waveForm.StationCode, waveForm.Depth, waveForm.Distance, waveForm.Magnitude)

	query, args, err := queryStatement.ToSql()
	if err != nil {
		return err
	}

	if _, err = a.db.Exec(context.Background(), query, args...); err != nil {
		return err
	}

	return nil
}

func (a *WaveFormAccessor) Deactivate(pickTimes []time.Time) (err error) {
	queryStatement := a.sb.Update("waveforms").
		Set("is_new", false).
		Where(sq.Eq{"pick_time": pickTimes})

	query, args, err := queryStatement.ToSql()
	if err != nil {
		return err
	}

	if _, err = a.db.Exec(context.Background(), query, args...); err != nil {
		return err
	}

	return nil
}
