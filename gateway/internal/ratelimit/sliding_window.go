package ratelimit

import (
"sync"
"time"
)

type SlidingWindow struct {
mu       sync.Mutex
requests map[string][]int64
limit    int
window   int64
}

func NewSlidingWindow(limit int, window int64) *SlidingWindow {
return &SlidingWindow{
requests: make(map[string][]int64),
limit:    limit,
window:   window,
}
}

func (r *SlidingWindow) Allow(key string) bool {
r.mu.Lock()
defer r.mu.Unlock()

now := time.Now().Unix()
windowStart := now - r.window

requests := r.requests[key]
valid := []int64{}
for _, ts := range requests {
if ts > windowStart {
valid = append(valid, ts)
}
}

if len(valid) >= r.limit {
return false
}

valid = append(valid, now)
r.requests[key] = valid
return true
}
