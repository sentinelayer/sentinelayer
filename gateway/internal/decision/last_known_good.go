package decision

import (
	"container/list"
	"sync"
	"time"
)

type cacheEntry struct {
	key     string
	value   interface{}
	expires time.Time
}

// LastKnownGood bounds path-driven memory and the lifetime of fallback decisions.
type LastKnownGood struct {
	mu    sync.Mutex
	state map[string]*list.Element
	order *list.List
	limit int
	ttl   time.Duration
	now   func() time.Time
}

func NewLastKnownGood() *LastKnownGood {
	return &LastKnownGood{state: make(map[string]*list.Element), order: list.New(), limit: 4096, ttl: 60 * time.Second, now: time.Now}
}

func (l *LastKnownGood) Save(key string, value interface{}) {
	l.mu.Lock()
	defer l.mu.Unlock()
	entry := cacheEntry{key: key, value: value, expires: l.now().Add(l.ttl)}
	if element, ok := l.state[key]; ok {
		element.Value = entry
		l.order.MoveToFront(element)
		return
	}
	l.state[key] = l.order.PushFront(entry)
	if len(l.state) > l.limit {
		oldest := l.order.Back()
		delete(l.state, oldest.Value.(cacheEntry).key)
		l.order.Remove(oldest)
	}
}

func (l *LastKnownGood) Get(key string) (interface{}, bool) {
	l.mu.Lock()
	defer l.mu.Unlock()
	element, ok := l.state[key]
	if !ok {
		return nil, false
	}
	entry := element.Value.(cacheEntry)
	if !l.now().Before(entry.expires) {
		delete(l.state, key)
		l.order.Remove(element)
		return nil, false
	}
	l.order.MoveToFront(element)
	return entry.value, true
}
