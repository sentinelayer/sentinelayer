package ratelimit

import (
"context"
"fmt"
"net/url"
"strconv"
"strings"
"time"

"github.com/redis/go-redis/v9"
)

type RedisRateLimiter struct {
client *redis.Client
limit  int
window time.Duration
}

// NewRedisRateLimiter accepts either host:port (REDIS_ADDR) or full redis URL (REDIS_URL).
func NewRedisRateLimiter(addrOrURL string, limit int) *RedisRateLimiter {
addr := "127.0.0.1:6379"
if addrOrURL != "" {
if strings.HasPrefix(addrOrURL, "redis://") || strings.HasPrefix(addrOrURL, "rediss://") {
if u, err := url.Parse(addrOrURL); err == nil && u.Host != "" {
addr = u.Host
}
} else {
addr = addrOrURL
}
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
// fail-open on redis error (Section 10.23)
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
