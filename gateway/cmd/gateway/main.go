package main

import (
"encoding/json"
"log"
"net/http"
"net/http/httputil"
"net/url"
"os"
"regexp"
"sync"
"time"
"gateway/internal/waf"
)

type RateLimiter struct {
mu       sync.Mutex
requests map[string][]int64
limit    int
window   int64
}

func NewRateLimiter(limit int) *RateLimiter {
return &RateLimiter{requests: make(map[string][]int64), limit: limit, window: 60}
}

func (r *RateLimiter) Allow(key string) bool {
r.mu.Lock()
defer r.mu.Unlock()
now := time.Now().Unix()
start := now - r.window
valid := []int64{}
for _, ts := range r.requests[key] {
if ts > start {
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

func main() {
coraza := waf.NewCorazaEngine()
coraza.LoadCRS("waf/rules")

regexRules := []*regexp.Regexp{
regexp.MustCompile(`(?i)(select|insert|update|delete|drop|union|exec|master|script|--|;|\b(OR|AND)\s+\d+\s*=\s*\d+)`),
regexp.MustCompile(`(?i)(<script|alert\(|onerror=|onclick=|onload=|javascript:|<iframe|document\.cookie)`),
regexp.MustCompile(`(\.\./|\.\.\\)`),
regexp.MustCompile(`(?i)(\||;|&&|` + "`" + `|\$\(|ping\s|wget\s|curl\s|nmap\s|python\s-c)`),
}

rateLimiter := NewRateLimiter(60)
upstream, _ := url.Parse(os.Getenv("UPSTREAM_URL"))
proxy := httputil.NewSingleHostReverseProxy(upstream)

mux := http.NewServeMux()

mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
for _, value := range r.URL.Query() {
if coraza.Match(value[0]) {
w.WriteHeader(http.StatusForbidden)
json.NewEncoder(w).Encode(map[string]string{"error": "WAF Blocked (Coraza)"})
return
}
for _, rule := range regexRules {
if rule.MatchString(value[0]) {
w.WriteHeader(http.StatusForbidden)
json.NewEncoder(w).Encode(map[string]string{"error": "WAF Blocked (Regex)"})
return
}
}
}
if !rateLimiter.Allow(r.RemoteAddr) {
w.WriteHeader(http.StatusTooManyRequests)
json.NewEncoder(w).Encode(map[string]string{"error": "Rate limit exceeded"})
return
}
proxy.ServeHTTP(w, r)
})

mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
json.NewEncoder(w).Encode(map[string]string{"status": "healthy"})
})

server := &http.Server{Addr: ":8080", Handler: mux, ReadTimeout: 10 * time.Second, WriteTimeout: 10 * time.Second}
log.Println("Gateway on :8080")
log.Fatal(server.ListenAndServe())
}
