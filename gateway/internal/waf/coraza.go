package waf

import (
	"bytes"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"strings"

	"github.com/corazawaf/coraza/v3"
)

// Engine wraps real Coraza WAF (not regex).
type Engine struct {
	waf coraza.WAF
}

// NewEngine creates Coraza with recommended directives.
// CRS rules dir optional; if empty, uses built-in baseline.
func NewEngine(crsRulesDir string) (*Engine, error) {
	directives := `
SecRuleEngine On
SecRequestBodyAccess On
SecResponseBodyAccess Off
SecRule REQUEST_HEADERS:Content-Type "@rx (?i)^application/json" "id:1000,phase:1,pass,nolog,ctl:requestBodyProcessor=JSON"
	`

	if crsRulesDir != "" {
		setupFile := os.Getenv("CRS_SETUP_FILE")
		if setupFile == "" {
			setupFile = filepath.Join(filepath.Dir(crsRulesDir), "crs-setup.conf.example")
		}
		if _, err := os.Stat(setupFile); err != nil {
			return nil, fmt.Errorf("CRS setup file is required: %s: %w", setupFile, err)
		}
		directives += fmt.Sprintf("\nSecDataDir %s\nInclude %s\nInclude %s/*.conf\n", crsRulesDir, setupFile, crsRulesDir)
	}

	// Baseline rules always on. Libinjection handles common SQLi/XSS payloads;
	// explicit signatures cover deployments where the optional operator is unavailable.
	directives += `
SecRule ARGS "@detectSQLi" "id:1001,phase:2,deny,status:403,msg:'SQL Injection',logdata:'%{MATCHED_VAR}'"
SecRule ARGS "@rx (?i)(union\s+select|drop\s+table|or\s+1\s*=\s*1|--[[:space:]]|/\*)" "id:1005,phase:2,deny,status:403,msg:'SQL Injection signature',logdata:'%{MATCHED_VAR}'"
SecRule ARGS "@detectXSS" "id:1002,phase:2,deny,status:403,msg:'XSS',logdata:'%{MATCHED_VAR}'"
SecRule ARGS "@rx (?i)(<script|javascript:|onerror\s*=|onload\s*=)" "id:1006,phase:2,deny,status:403,msg:'XSS signature',logdata:'%{MATCHED_VAR}'"
SecRule REQUEST_URI "@rx (?i)(\.\./|%2e%2e%2f)" "id:1003,phase:1,deny,status:403,msg:'Path Traversal'"
SecRule REQUEST_HEADERS:Content-Type "@contains multipart/form-data" "id:1004,phase:1,pass"
`

	cfg := coraza.NewWAFConfig().WithDirectives(directives)
	waf, err := coraza.NewWAF(cfg)
	if err != nil {
		return nil, fmt.Errorf("coraza new waf: %w", err)
	}
	return &Engine{waf: waf}, nil
}

// ProcessRequest runs Coraza on the incoming request.
// Returns true if request should be BLOCKED.
func (e *Engine) ProcessRequest(r *http.Request) (blocked bool, ruleID int, msg string) {
	tx := e.waf.NewTransaction()
	defer func() {
		tx.ProcessLogging()
		_ = tx.Close()
	}()

	rawURI := r.RequestURI
	if rawURI == "" {
		rawURI = r.URL.RequestURI()
	}
	decodedURI, _ := url.PathUnescape(rawURI)
	if strings.Contains(decodedURI, "../") || strings.Contains(strings.ToLower(rawURI), "%2e%2e") {
		return true, 1003, "Path Traversal"
	}

	tx.ProcessConnection(r.RemoteAddr, 0, "", 0)
	requestURI := r.RequestURI
	if requestURI == "" {
		requestURI = r.URL.RequestURI()
	}
	tx.ProcessURI(requestURI, r.Method, r.Proto)
	if r.Host != "" {
		tx.AddRequestHeader("Host", r.Host)
	}
	for k, vv := range r.Header {
		for _, v := range vv {
			tx.AddRequestHeader(k, v)
		}
	}
	tx.ProcessRequestHeaders()

	it := tx.Interruption()
	if it != nil {
		return true, it.RuleID, it.Data
	}

	// Buffer the body once, feed the exact bytes to Coraza, and restore the
	// body for the upstream proxy. Oversized inspection is rejected rather than
	// silently forwarding an uninspected payload.
	const maxInspectionBody = 2 * 1024 * 1024
	if r.Body != nil && r.Body != http.NoBody {
		body, err := io.ReadAll(io.LimitReader(r.Body, maxInspectionBody+1))
		if err != nil {
			return true, 1007, "Request body could not be inspected"
		}
		r.Body = io.NopCloser(bytes.NewReader(body))
		if len(body) > maxInspectionBody {
			return true, 1007, "Request body exceeds inspection limit"
		}
		if it, _, err := tx.ReadRequestBodyFrom(bytes.NewReader(body)); err != nil {
			return true, 1007, "Request body could not be inspected"
		} else if it != nil {
			return true, it.RuleID, it.Data
		}
	}
	_, _ = tx.ProcessRequestBody()
	it = tx.Interruption()
	if it != nil {
		return true, it.RuleID, it.Data
	}
	return false, 0, ""
}

// Allowed is inverse of blocked for middleware clarity.
func (e *Engine) Allowed(r *http.Request) bool {
	blocked, _, _ := e.ProcessRequest(r)
	return !blocked
}
