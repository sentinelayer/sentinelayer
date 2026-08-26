package normalize

import (
    "bytes"
    "compress/gzip"
    "io"
    "net/http"
)

func NormalizeBody(r *http.Request) ([]byte, error) {
    var body []byte
    if r.Body != nil {
        var err error
        body, err = io.ReadAll(r.Body)
        if err != nil {
            return nil, err
        }
        r.Body = io.NopCloser(bytes.NewBuffer(body))
    }

    if r.Header.Get("Content-Encoding") == "gzip" {
        reader, err := gzip.NewReader(bytes.NewReader(body))
        if err != nil {
            return body, nil
        }
        defer reader.Close()
        decompressed, err := io.ReadAll(reader)
        if err == nil {
            body = decompressed
            r.Header.Del("Content-Encoding")
            r.ContentLength = int64(len(body))
        }
    }

    return body, nil
}
