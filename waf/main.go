package main

import (
    "fmt"
    "log"
    "net/http"
    "net/http/httputil"
    "net/url"
    "strings"
)

func main() {
    target, _ := url.Parse("http://localhost:8000")
    proxy := httputil.NewSingleHostReverseProxy(target)

    http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
        path := r.URL.Path
        query := r.URL.RawQuery

        sql_patterns := []string{"SELECT", "UNION", "INSERT", "DELETE", "DROP", "--", ";"}
        xss_patterns := []string{"<script", "javascript:", "onerror", "onload"}
        path_patterns := []string{"../", "/etc/passwd", "/proc/self"}

        for _, p := range sql_patterns {
            if strings.Contains(strings.ToUpper(query), p) {
                w.WriteHeader(403)
                w.Write([]byte("Blocked by WAF"))
                return
            }
        }

        for _, p := range xss_patterns {
            if strings.Contains(strings.ToLower(query), p) {
                w.WriteHeader(403)
                w.Write([]byte("Blocked by WAF"))
                return
            }
        }

        for _, p := range path_patterns {
            if strings.Contains(path, p) {
                w.WriteHeader(403)
                w.Write([]byte("Blocked by WAF"))
                return
            }
        }

        proxy.ServeHTTP(w, r)
    })

    fmt.Println("WAF proxy running on :8080")
    log.Fatal(http.ListenAndServe(":8080", nil))
}
