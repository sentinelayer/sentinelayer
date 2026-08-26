package ratelimit

import (
"context"
"fmt"
"strconv"
"time"

"github.com/redis/go-redis/v9"
)

type RedisRateLimiter struct {
client *redis.Client
limit  int
window time.Duration
}

func NewRedisRateLimiter(addr string, limit int) *RedisRateLimiter {
if addr == "" {
addr = "127.0.0.1:6379"
}
rdb := redis.NewClient(&redis.Options{Addr: addr})
return &RedisRateLimiter{client: rdb, limit: limit, window: time.Minute}
}

func (r *RedisRateLimiter) Allow(key string) bool {
if r == nil || r.client == nil {
return true
}
ctx, cancel := context.WithTimeout(context.Background(), 50*time.Millisecond)
defer cancel()
now := time.Now().Unix()
windowStart := now - int64(r.window.Seconds())
member := strconv.FormatInt(now, 10) + ":" + strconv.FormatInt(time.Now().UnixNano(), 10)

pipe := r.client.Pipeline()
pipe.ZRemRangeByScore(ctx, key, "0", fmt.Sprintf("%d", windowStart))
card := pipe.ZCard(ctx, key)
_, err := pipe.Exec(ctx)
if err != nil {
// fail-open on redis error (Section 10.23 redis)
return true
}
if card.Val() >= int64(r.limit) {
return false
}
pipe2 := r.client.Pipeline()
pipe2.ZAdd(ctx, key, redis.Z{Score: float64(now), Member: member})
pipe2.Expire(ctx, key, r.window)
_, err = pipe2.Exec(ctx)
return err == nil
}
