package main

import (
    "fmt"
    "log"
    "net/http"
    "net/http/httputil"
    "net/url"
)

func main() {
    target, _ := url.Parse("http://localhost:8000")
    proxy := httputil.NewSingleHostReverseProxy(target)

    http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
        proxy.ServeHTTP(w, r)
    })

    fmt.Println("WAF proxy running on :8080")
    log.Fatal(http.ListenAndServe(":8080", nil))
}
