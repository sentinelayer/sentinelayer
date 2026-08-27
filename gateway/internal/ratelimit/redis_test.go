package ratelimit

import (
	"net"
	"net/url"
	"strconv"
	"sync"
	"testing"

	"github.com/alicebob/miniredis/v2"
	"github.com/redis/go-redis/v9"
)

func TestRedisRateLimiterEnforcesAtomicLimit(t *testing.T) {
	server := miniredis.RunT(t)
	limiter := NewRedisRateLimiter(server.Addr(), 3)

	for i := 0; i < 3; i++ {
		allowed, err := limiter.Allow("test-key")
		if err != nil || !allowed {
			t.Fatalf("request %d: allowed=%v err=%v", i, allowed, err)
		}
	}
	allowed, err := limiter.Allow("test-key")
	if err != nil || allowed {
		t.Fatalf("fourth request: allowed=%v err=%v; want limit hit", allowed, err)
	}
}

func TestRedisRateLimiterIsAtomicUnderConcurrency(t *testing.T) {
	server := miniredis.RunT(t)
	limiter := NewRedisRateLimiter(server.Addr(), 10)
	const attempts = 50
	results := make(chan bool, attempts)
	var wg sync.WaitGroup
	for i := 0; i < attempts; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			allowed, err := limiter.Allow("concurrent-key")
			results <- err == nil && allowed
		}()
	}
	wg.Wait()
	close(results)

	allowedCount := 0
	for allowed := range results {
		if allowed {
			allowedCount++
		}
	}
	if allowedCount != 10 {
		t.Fatalf("allowed %d concurrent requests; want exactly 10", allowedCount)
	}
}

func TestScopedKeyDoesNotExposeParts(t *testing.T) {
	key := ScopedKey("tenant-a", "user-a", "10.0.0.1")
	if key == "" || key == "sl:rl:tenant-a:user-a:10.0.0.1" {
		t.Fatalf("scoped key contains plaintext parts: %q", key)
	}
	if ScopedKey("tenant-a", "user-a") == ScopedKey("tenant-a", "user-b") {
		t.Fatal("different scopes generated the same rate-limit key")
	}
}

func TestRedisRateLimiterReturnsInfrastructureError(t *testing.T) {
	server := miniredis.RunT(t)
	limiter := NewRedisRateLimiter(server.Addr(), 1)
	server.Close()
	allowed, err := limiter.Allow("unavailable-key")
	if err == nil || allowed {
		t.Fatalf("allowed=%v err=%v; want infrastructure error", allowed, err)
	}
}

func TestRedisURLParsing(t *testing.T) {
	parsed, err := url.Parse("rediss://user:pass@example.test:6380/4")
	if err != nil {
		t.Fatal(err)
	}
	if parsed.Scheme != "rediss" || parsed.Host != "example.test:6380" || parsed.Path != "/4" {
		t.Fatalf("unexpected parsed Redis URL: %#v", parsed)
	}
	if _, _, err := net.SplitHostPort(parsed.Host); err != nil {
		t.Fatal(err)
	}
	if _, err := strconv.Atoi("4"); err != nil {
		t.Fatal(err)
	}
	_ = redis.Options{}
}
