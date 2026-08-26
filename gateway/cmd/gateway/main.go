package main

import (
"encoding/json"
"log"
"net/http"
"strings"
"time"
)

type WAFEngine struct {
Rules []string
}

func NewWAFEngine() *WAFEngine {
return &WAFEngine{
Rules: []string{
"(?i)(select|insert|update|delete|drop|union|exec|master|script|--|;|\\b(OR|AND)\\s+\\d+\\s*=\\s*\\d+)",
"(?i)(<script|alert\\(|onerror=|onclick=|onload=|javascript:|<iframe|document\\.cookie)",
"(\\.\\./|\\.\\.\\\\)",
"(?i)(\\||;|\\&\\&|`|\\$\\(|ping\\s|wget\\s|curl\\s|nmap\\s|python\\s-c)",
},
}
}

func (w *WAFEngine) Process(input string) bool {
for _, rule := range w.Rules {
if strings.Contains(input, rule) {
return true
}
}
return false
}

type RateLimiter struct {
requests map[string][]int64
limit    int
window   int64
}

func NewRateLimiter(limit int) *RateLimiter {
return &RateLimiter{
requests: make(map[string][]int64),
limit:    limit,
window:   60,
}
}

func (r *RateLimiter) Allow(key string) bool {
now := time.Now().Unix()
windowStart := now - r.window

reqs := r.requests[key]
valid := []int64{}
for _, ts := range reqs {
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

func main() {
waf := NewWAFEngine()
limiter := NewRateLimiter(60)

mux := http.NewServeMux()

mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
// WAF
for key, value := range r.URL.Query() {
if waf.Process(value[0]) {
w.WriteHeader(http.StatusForbidden)
json.NewEncoder(w).Encode(map[string]string{"error": "WAF Blocked"})
return
}
}

// Rate Limit
clientIP := r.RemoteAddr
if !limiter.Allow(clientIP) {
w.WriteHeader(http.StatusTooManyRequests)
json.NewEncoder(w).Encode(map[string]string{"error": "Rate limit exceeded"})
return
}

w.WriteHeader(http.StatusOK)
json.NewEncoder(w).Encode(map[string]string{"status": "ok", "message": "SentinelLayer Gateway"})
})

mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
json.NewEncoder(w).Encode(map[string]string{"status": "healthy"})
})

server := &http.Server{
Addr:         ":8080",
Handler:      mux,
ReadTimeout:  10 * time.Second,
WriteTimeout: 10 * time.Second,
IdleTimeout:  120 * time.Second,
}

log.Println("Gateway running on :8080")
log.Fatal(server.ListenAndServe())
}
