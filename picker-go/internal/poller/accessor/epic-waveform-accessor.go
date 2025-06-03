package accessor

import (
	"context"
	sq "github.com/Masterminds/squirrel"
	"github.com/jackc/pgx/v5/pgxpool"
	"time"
)

type EpicWaveForm struct {
	EventTime    time.Time `json:"event_time"`
	StationCodes []string  `json:"station_codes"`
	Latitude     float64   `json:"latitude"`
	Longitude    float64   `json:"longitude"`
	Magnitude    float64   `json:"magnitude"`
}

type EpicWaveFormAccessor struct {
	db *pgxpool.Pool
	sb sq.StatementBuilderType
}

func NewEpicWaveFormAccessor(db *pgxpool.Pool) *EpicWaveFormAccessor {
	sb := sq.StatementBuilder.
		PlaceholderFormat(sq.Dollar)
	return &EpicWaveFormAccessor{
		sb: sb,
		db: db,
	}
}

func (a *EpicWaveFormAccessor) Create(waveForm *EpicWaveForm) (err error) {
	queryStatement := a.sb.Insert("epic_waveforms").Columns(
		"event_time", "station_codes", "latitude", "longitude", "magnitude",
	).Values(waveForm.EventTime, waveForm.StationCodes, waveForm.Latitude, waveForm.Longitude, waveForm.Magnitude)

	query, args, err := queryStatement.ToSql()
	if err != nil {
		return err
	}

	if _, err = a.db.Exec(context.Background(), query, args...); err != nil {
		return err
	}

	return nil
}
