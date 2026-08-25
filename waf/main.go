package main

import (
    "fmt"
    "log"
    "net/http"
    "net/http/httputil"
    "net/url"
    "strings"
    "time"
)

type WAF struct {
    rules []Rule
}

type Rule struct {
    Pattern string
    Action  string
    Phase   int
}

func NewWAF() *WAF {
    waf := &WAF{}
    waf.rules = []Rule{
        {Pattern: "(?i)(union\\s+select|select\\s+.*\\s+from|insert\\s+into|delete\\s+from|drop\\s+table)", Action: "deny", Phase: 2},
        {Pattern: "(?i)(<script|</script>|javascript:|onerror=|onload=|onclick=)", Action: "deny", Phase: 2},
        {Pattern: "(?i)(\\.\\./|\\.\\.\\\\)", Action: "deny", Phase: 1},
        {Pattern: "(?i)(;|\\||&&)\\s*(ls|pwd|cat|echo|wget|curl|nc|bash|sh)", Action: "deny", Phase: 2},
        {Pattern: "(?i)(/admin|/administrator|/wp-admin|/phpmyadmin|/dashboard)", Action: "deny", Phase: 1},
        {Pattern: "(169\\.254\\.169\\.254|metadata\\.google|127\\.0\\.0\\.1|192\\.168\\.|10\\.)", Action: "deny", Phase: 2},
    }
    return waf
}

func (w *WAF) Inspect(path string, query string, body string) bool {
    for _, rule := range w.rules {
        if strings.Contains(strings.ToLower(path), strings.ToLower(rule.Pattern)) {
            return false
        }
        if strings.Contains(strings.ToLower(query), strings.ToLower(rule.Pattern)) {
            return false
        }
        if strings.Contains(strings.ToLower(body), strings.ToLower(rule.Pattern)) {
            return false
        }
    }
    return true
}

func main() {
    waf := NewWAF()
    target, _ := url.Parse("http://api:8000")
    proxy := httputil.NewSingleHostReverseProxy(target)

    http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()

        if !waf.Inspect(r.URL.Path, r.URL.RawQuery, "") {
            w.WriteHeader(403)
            w.Write([]byte("Blocked by WAF"))
            return
        }

        proxy.ServeHTTP(w, r)
        log.Printf("%s %s %s %v", r.Method, r.URL.Path, r.RemoteAddr, time.Since(start))
    })

    log.Println("WAF proxy running on :8080")
    log.Fatal(http.ListenAndServe(":8080", nil))
}
