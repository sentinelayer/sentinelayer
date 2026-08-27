package normalize

import (
	"bytes"
	"compress/gzip"
	"errors"
	"io"
	"net/http"
)

const MaxBodyBytes int64 = 2 << 20

var ErrBodyTooLarge = errors.New("request body exceeds inspection limit")

func readBounded(reader io.Reader) ([]byte, error) {
	body, err := io.ReadAll(io.LimitReader(reader, MaxBodyBytes+1))
	if err != nil {
		return nil, err
	}
	if int64(len(body)) > MaxBodyBytes {
		return nil, ErrBodyTooLarge
	}
	return body, nil
}

func NormalizeBody(r *http.Request) ([]byte, error) {
	var body []byte
	if r.Body != nil {
		var err error
		body, err = readBounded(r.Body)
		if err != nil {
			return nil, err
		}
		r.Body = io.NopCloser(bytes.NewReader(body))
	}

	if r.Header.Get("Content-Encoding") == "gzip" {
		reader, err := gzip.NewReader(bytes.NewReader(body))
		if err != nil {
			return nil, err
		}
		decompressed, readErr := readBounded(reader)
		closeErr := reader.Close()
		if readErr != nil {
			return nil, readErr
		}
		if closeErr != nil {
			return nil, closeErr
		}
		body = decompressed
		r.Header.Del("Content-Encoding")
		r.ContentLength = int64(len(body))
		r.Body = io.NopCloser(bytes.NewReader(body))
	}

	return body, nil
}
