package adapter

import (
	"context"
	sq "github.com/Masterminds/squirrel"
	"github.com/jackc/pgx/v5/pgxpool"
	"server/internal/domain"
	port "server/internal/port/stream"
)

type streamRepo struct {
	db *pgxpool.Pool
	sb sq.StatementBuilderType
}

func NewStreamRepo(db *pgxpool.Pool) port.StreamRepository {
	return &streamRepo{
		db: db,
		sb: sq.StatementBuilder.PlaceholderFormat(sq.Dollar),
	}
}

func (s streamRepo) Create(ctx context.Context, status string, streamingType string) (err error) {
	query, args, err := s.sb.Insert("streams").Columns("stream_type", "status").Values(streamingType, status).ToSql()
	if err != nil {
		return err
	}

	if _, err = s.db.Exec(ctx, query, args...); err != nil {
		return err
	}

	return nil
}

func (s streamRepo) Update(ctx context.Context, data map[string]any, status string, streamingType string) (err error) {
	queryStatement := s.sb.Update("streams")
	for key, value := range data {
		queryStatement = queryStatement.Set(key, value)
	}

	query, args, err := queryStatement.Where(sq.Eq{"status": status, "stream_type": streamingType}).ToSql()
	if err != nil {
		return err
	}

	if _, err = s.db.Exec(ctx, query, args...); err != nil {
		return err
	}

	return nil
}

func (s streamRepo) GetBy(ctx context.Context, conditions interface{}) (streams []domain.Stream, err error) {
	queryStatement := s.sb.Select(
		"stream_type", "status", "started_at", "finished_at",
	).From("streams").Where(conditions)

	query, args, err := queryStatement.ToSql()
	if err != nil {
		return nil, err
	}

	rows, err := s.db.Query(ctx, query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	for rows.Next() {
		stream := domain.Stream{}

		if err = rows.Scan(
			&stream.StreamType,
			&stream.Status,
			&stream.StartedAt,
			&stream.FinishedAt,
		); err != nil {
			return nil, err
		}

		streams = append(streams, stream)
	}

	return streams, nil
}
