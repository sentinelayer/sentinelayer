package waf

import (
"fmt"
"net/http"

"github.com/corazawaf/coraza/v3"
"github.com/corazawaf/coraza/v3/types"
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
SecDefaultAction "phase:1,log,auditlog,pass"
SecDefaultAction "phase:2,log,auditlog,pass"
`
if crsRulesDir != "" {
directives += fmt.Sprintf("\nInclude %s/*.conf\n", crsRulesDir)
}

// Baseline rules always on (SQLi / XSS via libinjection when available)
directives += `
SecRule ARGS "@detectSQLi" "id:1001,phase:2,block,msg:'SQL Injection',logdata:'%{MATCHED_VAR}'"
SecRule ARGS "@detectXSS" "id:1002,phase:2,block,msg:'XSS',logdata:'%{MATCHED_VAR}'"
SecRule REQUEST_URI "@contains ../" "id:1003,phase:1,block,msg:'Path Traversal'"
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
tx.Close()
}()

tx.ProcessConnection(r.RemoteAddr, 0, "", 0)
tx.ProcessURI(r.URL.String(), r.Method, r.Proto)
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

// Body: caller may have already read; we process URI/headers/args primarily here.
tx.ProcessRequestBody()
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
