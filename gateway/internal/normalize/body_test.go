package normalize

import (
	"bytes"
	"compress/gzip"
	"io"
	"net/http/httptest"
	"testing"
)

func gzipPayload(t *testing.T, payload []byte) []byte {
	t.Helper()
	var buffer bytes.Buffer
	writer := gzip.NewWriter(&buffer)
	if _, err := writer.Write(payload); err != nil {
		t.Fatal(err)
	}
	if err := writer.Close(); err != nil {
		t.Fatal(err)
	}
	return buffer.Bytes()
}

func TestNormalizeBodyRestoresPlainBody(t *testing.T) {
	req := httptest.NewRequest("POST", "http://example.test", bytes.NewReader([]byte(`{"safe":true}`)))
	body, err := NormalizeBody(req)
	if err != nil {
		t.Fatal(err)
	}
	if string(body) != `{"safe":true}` {
		t.Fatalf("body = %q", body)
	}
	restored, _ := io.ReadAll(req.Body)
	if string(restored) != string(body) {
		t.Fatalf("restored body = %q", restored)
	}
}

func TestNormalizeBodyDecompressesAndRestoresGzip(t *testing.T) {
	payload := []byte(`{"sql":"select 1"}`)
	req := httptest.NewRequest("POST", "http://example.test", bytes.NewReader(gzipPayload(t, payload)))
	req.Header.Set("Content-Encoding", "gzip")
	body, err := NormalizeBody(req)
	if err != nil {
		t.Fatal(err)
	}
	if string(body) != string(payload) || req.Header.Get("Content-Encoding") != "" {
		t.Fatalf("body/header not normalized: %q %q", body, req.Header.Get("Content-Encoding"))
	}
}

func TestNormalizeBodyRejectsGzipBomb(t *testing.T) {
	payload := bytes.Repeat([]byte("A"), int(MaxBodyBytes)+1)
	req := httptest.NewRequest("POST", "http://example.test", bytes.NewReader(gzipPayload(t, payload)))
	req.Header.Set("Content-Encoding", "gzip")
	if _, err := NormalizeBody(req); err != ErrBodyTooLarge {
		t.Fatalf("err = %v; want ErrBodyTooLarge", err)
	}
}

func TestNormalizeBodyRejectsCompressedOversize(t *testing.T) {
	payload := bytes.Repeat([]byte("A"), int(MaxBodyBytes)+1)
	req := httptest.NewRequest("POST", "http://example.test", bytes.NewReader(payload))
	if _, err := NormalizeBody(req); err != ErrBodyTooLarge {
		t.Fatalf("err = %v; want ErrBodyTooLarge", err)
	}
}

func TestNormalizeBodyRejectsInvalidGzip(t *testing.T) {
	req := httptest.NewRequest("POST", "http://example.test", bytes.NewReader([]byte("not gzip")))
	req.Header.Set("Content-Encoding", "gzip")
	if _, err := NormalizeBody(req); err == nil {
		t.Fatal("invalid gzip was accepted")
	}
}
