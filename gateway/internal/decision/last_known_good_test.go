package decision

import (
	"testing"
	"time"
)

func TestFallbackExpiryDoesNotSlideOnRead(t *testing.T) {
	cache := NewLastKnownGood()
	now := time.Unix(2000000000, 0)
	cache.now = func() time.Time { return now }
	cache.Save("tenant:path:version", "allow")
	now = now.Add(59 * time.Second)
	if _, ok := cache.Get("tenant:path:version"); !ok {
		t.Fatal("early expiry")
	}
	now = now.Add(time.Second)
	if _, ok := cache.Get("tenant:path:version"); ok {
		t.Fatal("read extended stale fallback")
	}
}

func TestFallbackEvictionPreservesRecentlyUsedEntries(t *testing.T) {
	cache := NewLastKnownGood()
	cache.limit = 2
	cache.Save("a", "a")
	cache.Save("b", "b")
	cache.Get("a")
	cache.Save("c", "c")
	if _, ok := cache.Get("b"); ok {
		t.Fatal("least recently used entry retained")
	}
	if _, ok := cache.Get("a"); !ok {
		t.Fatal("recently used entry evicted")
	}
	for i := 0; i < 100; i++ {
		cache.Save(string(rune(i)), i)
	}
	if len(cache.state) != 2 || cache.order.Len() != 2 {
		t.Fatal("cache bound exceeded")
	}
}
