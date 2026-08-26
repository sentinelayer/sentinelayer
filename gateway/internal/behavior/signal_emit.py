package behavior

import "time"

type ThreatIntelCache struct {
    cache map[string]int64
    ttl   int64
}

func NewThreatIntelCache(ttl int64) *ThreatIntelCache {
    return &ThreatIntelCache{
        cache: make(map[string]int64),
        ttl:   ttl,
    }
}

func (t *ThreatIntelCache) Get(key string) (int64, bool) {
    val, ok := t.cache[key]
    if !ok {
        return 0, false
    }
    if time.Now().Unix()-val > t.ttl {
        delete(t.cache, key)
        return 0, false
    }
    return val, true
}

func (t *ThreatIntelCache) Set(key string, value int64) {
    t.cache[key] = value
}
