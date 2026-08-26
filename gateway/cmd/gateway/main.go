package main

import (
"encoding/json"
"log"
"net/http"
"net/http/httputil"
"net/url"
"os"
"time"

"github.com/sentinelayer/gateway/internal/desync"
"github.com/sentinelayer/gateway/internal/ratelimit"
"github.com/sentinelayer/gateway/internal/waf"
)

func main() {
crsDir := os.Getenv("CRS_RULES_DIR") // optional path to OWASP CRS .conf files
wafEngine, err := waf.NewEngine(crsDir)
if err != nil {
log.Fatalf("WAF init failed: %v", err)
}
log.Println("Coraza WAF initialized")

rateLimiter := ratelimit.NewRedisRateLimiter(os.Getenv("REDIS_ADDR"), 60)
upstreamURL := os.Getenv("UPSTREAM_URL")
if upstreamURL == "" {
upstreamURL = "http://127.0.0.1:8000"
}
upstream, err := url.Parse(upstreamURL)
if err != nil {
log.Fatalf("invalid UPSTREAM_URL: %v", err)
}
proxy := httputil.NewSingleHostReverseProxy(upstream)

mux := http.NewServeMux()

mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
if desync.GuardDesync(r) {
w.Header().Set("Content-Type", "application/json")
w.WriteHeader(http.StatusBadRequest)
json.NewEncoder(w).Encode(map[string]string{"error": "HTTP desync detected"})
return
}

blocked, ruleID, msg := wafEngine.ProcessRequest(r)
if blocked {
w.Header().Set("Content-Type", "application/json")
w.WriteHeader(http.StatusForbidden)
json.NewEncoder(w).Encode(map[string]interface{}{
"error":   "WAF Blocked",
"rule_id": ruleID,
"msg":     msg,
})
return
}

if !rateLimiter.Allow(r.RemoteAddr) {
w.Header().Set("Content-Type", "application/json")
w.WriteHeader(http.StatusTooManyRequests)
json.NewEncoder(w).Encode(map[string]string{"error": "Rate limit exceeded"})
return
}

proxy.ServeHTTP(w, r)
})

mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
w.Header().Set("Content-Type", "application/json")
json.NewEncoder(w).Encode(map[string]string{"status": "healthy", "waf": "coraza"})
})

server := &http.Server{
Addr:         ":8080",
Handler:      mux,
ReadTimeout:  10 * time.Second,
WriteTimeout: 10 * time.Second,
}
log.Println("Gateway on :8080 (Coraza WAF)")
log.Fatal(server.ListenAndServe())
}
