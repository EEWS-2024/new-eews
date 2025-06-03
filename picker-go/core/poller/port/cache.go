package port

import "context"

type Cache interface {
	Get(ctx context.Context, key string) (string, error)
	Set(ctx context.Context, key, value string, ttlSeconds int) error
	Delete(ctx context.Context, key string) error
}
