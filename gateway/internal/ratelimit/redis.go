package ratelimit

import (
	"context"
	"crypto/sha256"
	"crypto/tls"
	"encoding/hex"
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

var rateLimitScript = redis.NewScript(`
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local member = ARGV[4]
redis.call('ZREMRANGEBYSCORE', KEYS[1], 0, now - window)
local count = redis.call('ZCARD', KEYS[1])
if count >= limit then
  return 0
end
redis.call('ZADD', KEYS[1], now, member)
redis.call('EXPIRE', KEYS[1], math.ceil(window / 1000))
return 1
`)

// NewRedisRateLimiter accepts either host:port (REDIS_ADDR) or a redis URL.
func NewRedisRateLimiter(addrOrURL string, limit int) *RedisRateLimiter {
	if limit < 1 {
		limit = 1
	}
	options := &redis.Options{Addr: "127.0.0.1:6379"}
	if addrOrURL != "" && (strings.HasPrefix(addrOrURL, "redis://") || strings.HasPrefix(addrOrURL, "rediss://")) {
		if parsed, err := url.Parse(addrOrURL); err == nil && parsed.Host != "" {
			options.Addr = parsed.Host
			if parsed.User != nil {
				options.Username = parsed.User.Username()
				if password, ok := parsed.User.Password(); ok {
					options.Password = password
				}
			}
			if database := strings.Trim(parsed.Path, "/"); database != "" {
				if parsedDB, err := strconv.Atoi(database); err == nil && parsedDB >= 0 {
					options.DB = parsedDB
				}
			}
			if parsed.Scheme == "rediss" {
				options.TLSConfig = &tls.Config{MinVersion: tls.VersionTLS12}
			}
		}
	} else if addrOrURL != "" {
		options.Addr = addrOrURL
	}
	return &RedisRateLimiter{client: redis.NewClient(options), limit: limit, window: time.Minute}
}

// Allow atomically checks and records a request. The boolean is false only
// when the configured limit is reached; infrastructure errors are returned so
// the caller can apply the endpoint-specific failure policy.
func (r *RedisRateLimiter) Allow(key string) (bool, error) {
	if r == nil || r.client == nil {
		return true, nil
	}
	ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
	defer cancel()
	now := time.Now()
	member := fmt.Sprintf("%d:%d", now.UnixMilli(), now.UnixNano())
	value, err := rateLimitScript.Run(ctx, r.client, []string{key}, now.UnixMilli(), r.window.Milliseconds(), r.limit, member).Int()
	if err != nil {
		return false, err
	}
	return value == 1, nil
}

// ScopedKey creates a bounded Redis key without storing user-provided values
// in plaintext in the keyspace.
func ScopedKey(parts ...string) string {
	hash := sha256.New()
	for _, part := range parts {
		_, _ = hash.Write([]byte(part))
		_, _ = hash.Write([]byte{0})
	}
	return "sl:rl:" + hex.EncodeToString(hash.Sum(nil))
}
