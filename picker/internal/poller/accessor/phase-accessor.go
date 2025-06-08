package accessor

import (
	"context"
	sq "github.com/Masterminds/squirrel"
	"github.com/jackc/pgx/v5/pgxpool"
	"time"
)

type Phase struct {
	PickTime     time.Time `json:"pick_time"`
	StationCode  string    `json:"station_code"`
	IsPArrived   bool      `json:"is_p_arrived"`
	PArrivalTime time.Time `json:"p_arrival_time"`
	PIndex       int       `json:"p_index"`
	IsSArrived   bool      `json:"is_s_arrived"`
	SArrivalTime time.Time `json:"s_arrival_time"`
	SIndex       int       `json:"s_index"`
}

type PhaseAccessor struct {
	db *pgxpool.Pool
	sb sq.StatementBuilderType
}

func NewPhaseAccessor(db *pgxpool.Pool) *PhaseAccessor {
	sb := sq.StatementBuilder.
		PlaceholderFormat(sq.Dollar)
	return &PhaseAccessor{
		sb: sb,
		db: db,
	}
}

func (a *PhaseAccessor) Create(phase *Phase) (err error) {
	queryStatement := a.sb.Insert("phases").Columns(
		"pick_time", "station_code", "is_p_arrived", "p_arrival_time", "p_index", "is_s_arrived", "s_arrival_time", "s_index",
	).Values(phase.PickTime, phase.StationCode, phase.IsPArrived, phase.PArrivalTime, phase.PIndex, phase.IsSArrived, phase.SArrivalTime, phase.SIndex)

	query, args, err := queryStatement.ToSql()
	if err != nil {
		return err
	}

	if _, err = a.db.Exec(context.Background(), query, args...); err != nil {
		return err
	}

	return nil
}
