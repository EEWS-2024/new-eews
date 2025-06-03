package adapter

import (
	"context"
	"fmt"
	"github.com/go-redis/redis/v8"
	"picker-go/core/poller/port"
	"picker-go/internal/config"
	"time"
)

var _ port.Cache = (*RedisAdapter)(nil)

type RedisAdapter struct {
	client *redis.Client
}

func NewRedisAdapter(cfg *config.Config) *RedisAdapter {
	return &RedisAdapter{client: redis.NewClient(&redis.Options{
		Addr: fmt.Sprintf("%s:%d", cfg.RedisHost, cfg.RedisPort),
		DB:   cfg.RedisDB,
	})}
}

func (r *RedisAdapter) Get(ctx context.Context, key string) (string, error) {
	return r.client.Get(ctx, key).Result()
}

func (r *RedisAdapter) Set(ctx context.Context, key, value string, ttlSeconds int) error {
	return r.client.Set(ctx, key, value, time.Duration(ttlSeconds)*time.Second).Err()
}

func (r *RedisAdapter) Delete(ctx context.Context, key string) error {
	return r.client.Del(ctx, key).Err()
}
