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

func (l *LastKnownGood) GetLastGood() interface{} {
    l.mu.RLock()
    defer l.mu.RUnlock()
    if len(l.state) == 0 {
        return map[string]string{"action": "ALLOW"}
    }
    for _, v := range l.state {
        return v
    }
    return map[string]string{"action": "ALLOW"}
}
