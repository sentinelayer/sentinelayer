package decision

// FailMatrix implements Section 10.23 Fail-Open / Fail-Closed Decision Matrix.
// Capability-level, not component-level. Matches blueprint mandatory matrix.
type FailMatrix struct {
policies map[string]map[string]string
}

func NewFailMatrix() *FailMatrix {
return &FailMatrix{
policies: map[string]map[string]string{
"waf": {
"critical": "fail-closed",
"normal":   "fail-open",
"public":   "fail-open",
},
"risk_engine": {
"critical": "fail-closed",
"normal":   "monitor",
"public":   "monitor",
},
"redis": {
"critical": "fail-open",
"normal":   "fail-open",
"public":   "fail-open",
},
"threat_intel": {
"critical": "ignore",
"normal":   "ignore",
"public":   "ignore",
},
"control_plane": {
"critical": "last-known-good",
"normal":   "last-known-good",
"public":   "last-known-good",
},
"ai": {
"critical": "ignore",
"normal":   "ignore",
"public":   "ignore",
},
"auth": {
"critical": "fail-closed",
"normal":   "fail-closed",
"public":   "fail-open",
},
"ssrf": {
"critical": "fail-closed",
"normal":   "fail-closed",
"public":   "fail-closed",
},
},
}
}

func (f *FailMatrix) Policy(capability, endpointClass string) string {
if m, ok := f.policies[capability]; ok {
if p, ok := m[endpointClass]; ok {
return p
}
}
return "fail-closed"
}

func (f *FailMatrix) ShouldFailOpen(capability, endpointClass string) bool {
p := f.Policy(capability, endpointClass)
return p == "fail-open" || p == "ignore" || p == "monitor" || p == "last-known-good"
}

func (f *FailMatrix) ShouldFailClosed(capability, endpointClass string) bool {
return f.Policy(capability, endpointClass) == "fail-closed"
}
