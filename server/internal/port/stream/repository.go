package port

import (
	"context"
	"server/internal/domain"
)

type StreamRepository interface {
	Create(ctx context.Context, status string, streamingType string) (err error)
	Update(ctx context.Context, data map[string]any, status string, streamingType string) (err error)
	GetBy(ctx context.Context, conditions interface{}) (streams []domain.Stream, err error)
}
