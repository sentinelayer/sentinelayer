package waf

import (
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"testing"
)

func TestNewEngineLoadsOfficialCRS(t *testing.T) {
	if _, err := os.Stat("../../../waf/rules/REQUEST-942-APPLICATION-ATTACK-SQLI.conf"); err != nil {
		t.Fatalf("official CRS rules are not present: %v", err)
	}
	if _, err := NewEngine("../../../waf/rules"); err != nil {
		t.Fatalf("load official CRS rules: %v", err)
	}
}

func TestOfficialCRSBlocksSQLInjection(t *testing.T) {
	engine, err := NewEngine("../../../waf/rules")
	if err != nil {
		t.Fatalf("create WAF with official CRS: %v", err)
	}

	req := httptest.NewRequest(http.MethodGet, "http://example.test/?input=%27%20union%20select%20password%20from%20users", nil)
	blocked, _, _ := engine.ProcessRequest(req)
	if !blocked {
		t.Fatal("expected official CRS to block SQL injection")
	}
}

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

func TestProcessRequestBlocksJSONBodySQLInjection(t *testing.T) {
	engine, err := NewEngine("")
	if err != nil {
		t.Fatalf("create WAF: %v", err)
	}

	req := httptest.NewRequest(http.MethodPost, "http://example.test/login", strings.NewReader(`{"username":"admin' OR 1=1 --"}`))
	req.Header.Set("Content-Type", "application/json")
	blocked, ruleID, _ := engine.ProcessRequest(req)
	if !blocked || (ruleID != 1001 && ruleID != 1005) {
		t.Fatalf("expected JSON body SQL injection block with rule 1001 or 1005, blocked=%v rule=%d", blocked, ruleID)
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

func TestProcessRequestPreservesHostForCRS(t *testing.T) {
	engine, err := NewEngine("../../../waf/rules")
	if err != nil {
		t.Fatalf("create WAF with official CRS: %v", err)
	}
	req := httptest.NewRequest(http.MethodGet, "http://example.test/safe", nil)
	req.Header.Set("Accept", "application/json")
	req.Header.Set("User-Agent", "SentinelLayer-test/1.0")
	blocked, ruleID, msg := engine.ProcessRequest(req)
	if blocked {
		t.Fatalf("safe request blocked by rule %d (%s)", ruleID, msg)
	}
}


// Coraza 3.8.1 signals argument truncation instead of silently inspecting a
// subset. Both query-string and JSON body limits must fail closed.
func TestProcessRequestRejectsExcessiveQueryArguments(t *testing.T) {
    engine, err := NewEngine("")
    if err != nil {
        t.Fatalf("create WAF: %v", err)
    }
    req := httptest.NewRequest(http.MethodGet,
        "http://example.test/?"+strings.Repeat("item=1&", 1001), nil)
    blocked, ruleID, _ := engine.ProcessRequest(req)
    if !blocked || ruleID != 200004 {
        t.Fatalf("expected argument-limit query block (200004); blocked=%v rule=%d", blocked, ruleID)
    }
}

func TestProcessRequestRejectsExcessiveJSONArguments(t *testing.T) {
    engine, err := NewEngine("")
    if err != nil {
        t.Fatalf("create WAF: %v", err)
    }
    req := httptest.NewRequest(http.MethodPost, "http://example.test/data",
        strings.NewReader(`{"entries":[`+strings.TrimSuffix(strings.Repeat("1,", 1001), ",")+`]}`))
    req.Header.Set("Content-Type", "application/json")
    blocked, ruleID, _ := engine.ProcessRequest(req)
    if !blocked || ruleID != 200005 {
        t.Fatalf("expected argument-limit JSON block (200005); blocked=%v rule=%d", blocked, ruleID)
    }
}
