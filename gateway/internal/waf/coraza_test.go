package waf

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestProcessRequestBlocksSQLInjection(t *testing.T) {
	engine, err := NewEngine("")
	if err != nil {
		t.Fatalf("create WAF: %v", err)
	}

	req := httptest.NewRequest(http.MethodGet, "http://example.test/?input=%27%3B%20DROP%20TABLE%20users%3B%20--", nil)
	blocked, ruleID, _ := engine.ProcessRequest(req)
	if !blocked || (ruleID != 1001 && ruleID != 1005) {
		t.Fatalf("expected SQL injection block with rule 1001 or 1005, blocked=%v rule=%d", blocked, ruleID)
	}
}

func TestProcessRequestBlocksXSS(t *testing.T) {
	engine, err := NewEngine("")
	if err != nil {
		t.Fatalf("create WAF: %v", err)
	}

	req := httptest.NewRequest(http.MethodGet, "http://example.test/?input=%3Cscript%3Ealert%281%29%3C%2Fscript%3E", nil)
	blocked, ruleID, _ := engine.ProcessRequest(req)
	if !blocked || (ruleID != 1002 && ruleID != 1006) {
		t.Fatalf("expected XSS block with rule 1002 or 1006, blocked=%v rule=%d", blocked, ruleID)
	}
}

func TestProcessRequestBlocksPathTraversal(t *testing.T) {
	engine, err := NewEngine("")
	if err != nil {
		t.Fatalf("create WAF: %v", err)
	}

	req := httptest.NewRequest(http.MethodGet, "http://example.test/api/%2e%2e/%2e%2e/etc/passwd", nil)
	blocked, ruleID, _ := engine.ProcessRequest(req)
	if !blocked || ruleID != 1003 {
		t.Fatalf("expected path traversal block with rule 1003, blocked=%v rule=%d", blocked, ruleID)
	}
}
