package decision

import "sync"

type LastKnownGood struct {
    mu    sync.RWMutex
    state map[string]interface{}
}

func NewLastKnownGood() *LastKnownGood {
    return &LastKnownGood{
        state: make(map[string]interface{}),
    }
}

func (l *LastKnownGood) Save(key string, value interface{}) {
    l.mu.Lock()
    defer l.mu.Unlock()
    l.state[key] = value
}

func (l *LastKnownGood) Get(key string) (interface{}, bool) {
    l.mu.RLock()
    defer l.mu.RUnlock()
    val, ok := l.state[key]
    return val, ok
}
