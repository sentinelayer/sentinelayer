package main

import (
"bytes"
"encoding/json"
"io"
"log"
"net/http"
"net/http/httputil"
"net/url"
"os"
"regexp"
"time"
"gateway/internal/ratelimit"
"gateway/internal/desync"
)

func scanBody(body []byte, rules []*regexp.Regexp) bool {
for _, rule := range rules {
if rule.Match(body) {
return true
}
}
return false
}

func main() {
wafRules := []*regexp.Regexp{
regexp.MustCompile(`(?i)(select|insert|update|delete|drop|union|exec|master|script|--|;|\b(OR|AND)\s+\d+\s*=\s*\d+)`),
regexp.MustCompile(`(?i)(<script|alert\(|onerror=|onclick=|onload=|javascript:|<iframe|document\.cookie)`),
regexp.MustCompile(`(\.\./|\.\.\\)`),
regexp.MustCompile(`(?i)(\||;|&&|` + "`" + `|\$\(|ping\s|wget\s|curl\s|nmap\s|python\s-c)`),
}

redisAddr := os.Getenv("REDIS_ADDR")
if redisAddr == "" {
redisAddr = os.Getenv("REDIS_URL")
}
rateLimiter := ratelimit.NewRedisRateLimiter(redisAddr, 60)
upstream, _ := url.Parse(os.Getenv("UPSTREAM_URL"))
proxy := httputil.NewSingleHostReverseProxy(upstream)

mux := http.NewServeMux()

mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
// HTTP Desync Guard
if desync.GuardDesync(r) {
w.WriteHeader(http.StatusBadRequest)
json.NewEncoder(w).Encode(map[string]string{"error": "HTTP desync detected"})
return
}

for _, value := range r.URL.Query() {
for _, rule := range wafRules {
if rule.MatchString(value[0]) {
w.WriteHeader(http.StatusForbidden)
json.NewEncoder(w).Encode(map[string]string{"error": "WAF Blocked"})
return
}
}
}

if r.Body != nil {
body, _ := io.ReadAll(r.Body)
r.Body = io.NopCloser(bytes.NewBuffer(body))
if scanBody(body, wafRules) {
w.WriteHeader(http.StatusForbidden)
json.NewEncoder(w).Encode(map[string]string{"error": "WAF Blocked (body)"})
return
}
}

for _, rule := range wafRules {
if rule.MatchString(r.URL.Path) {
w.WriteHeader(http.StatusForbidden)
json.NewEncoder(w).Encode(map[string]string{"error": "WAF Blocked (path)"})
return
}
}

for key, values := range r.Header {
for _, value := range values {
for _, rule := range wafRules {
if rule.MatchString(key) || rule.MatchString(value) {
w.WriteHeader(http.StatusForbidden)
json.NewEncoder(w).Encode(map[string]string{"error": "WAF Blocked (header)"})
return
}
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
