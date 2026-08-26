package normalize

import "net/http"

func NormalizeRequest(r *http.Request) {
    if r.URL.Path == "" {
        r.URL.Path = "/"
    }
    if r.Header.Get("X-Forwarded-For") == "" {
        r.Header.Set("X-Forwarded-For", r.RemoteAddr)
    }
}
