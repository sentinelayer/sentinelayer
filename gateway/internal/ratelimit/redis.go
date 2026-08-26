package ratelimit

import (
"context"
"time"
"github.com/redis/go-redis/v9"
)

type RedisRateLimiter struct {
client *redis.Client
limit  int
window time.Duration
}

func NewRedisRateLimiter(addr string, limit int) *RedisRateLimiter {
rdb := redis.NewClient(&redis.Options{
Addr: addr,
})
return &RedisRateLimiter{
client: rdb,
limit:  limit,
window: time.Minute,
}
}

func (r *RedisRateLimiter) Allow(key string) bool {
ctx := context.Background()
now := time.Now().Unix()
windowStart := now - int64(r.window.Seconds())

pipe := r.client.Pipeline()
pipe.ZRemRangeByScore(ctx, key, "0", string(windowStart))
pipe.ZCard(ctx, key)
cmds, err := pipe.Exec(ctx)
if err != nil {
return true
}

count := cmds[1].(*redis.IntCmd).Val()
if count >= int64(r.limit) {
return false
}

pipe.ZAdd(ctx, key, redis.Z{Score: float64(now), Member: now})
pipe.Expire(ctx, key, r.window)
_, err = pipe.Exec(ctx)
return err == nil
}
