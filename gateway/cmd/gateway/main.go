package main

import (
"encoding/json"
"log"
"net/http"
"net/http/httputil"
"net/url"
"os"
"regexp"
"time"
"gateway/internal/ratelimit"
)

func main() {
wafRules := []*regexp.Regexp{
regexp.MustCompile(`(?i)(select|insert|update|delete|drop|union|exec|master|script|--|;|\b(OR|AND)\s+\d+\s*=\s*\d+)`),
regexp.MustCompile(`(?i)(<script|alert\(|onerror=|onclick=|onload=|javascript:|<iframe|document\.cookie)`),
regexp.MustCompile(`(\.\./|\.\.\\)`),
regexp.MustCompile(`(?i)(\||;|&&|` + "`" + `|\$\(|ping\s|wget\s|curl\s|nmap\s|python\s-c)`),
}

rateLimiter := ratelimit.NewRedisRateLimiter(os.Getenv("REDIS_ADDR"), 60)

upstream, _ := url.Parse(os.Getenv("UPSTREAM_URL"))
proxy := httputil.NewSingleHostReverseProxy(upstream)

mux := http.NewServeMux()

mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
for _, value := range r.URL.Query() {
for _, rule := range wafRules {
if rule.MatchString(value[0]) {
w.WriteHeader(http.StatusForbidden)
json.NewEncoder(w).Encode(map[string]string{"error": "WAF Blocked"})
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
