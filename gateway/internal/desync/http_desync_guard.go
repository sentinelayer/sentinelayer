package desync

import (
    "net/http"
    "strconv"
    "strings"
)

func GuardDesync(r *http.Request) bool {
    contentLength := r.Header.Get("Content-Length")
    transferEncoding := r.Header.Get("Transfer-Encoding")

    if transferEncoding == "chunked" && contentLength != "" {
        return true
    }

    if strings.Contains(transferEncoding, "chunked") && strings.Contains(transferEncoding, "gzip") {
        return true
    }

    if contentLength != "" {
        if _, err := strconv.Atoi(contentLength); err != nil {
            return true
        }
    }

    return false
}
