package waf

import "fmt"

type WAFEngine struct {
Rules []string
}

func NewWAFEngine() *WAFEngine {
return &WAFEngine{
Rules: []string{
"SQL Injection",
"XSS Attack",
"Path Traversal",
"Command Injection",
},
}
}

func (w *WAFEngine) Process(input string) bool {
for _, rule := range w.Rules {
if input == rule {
return true
}
}
return false
}

func (w *WAFEngine) GetRules() []string {
return w.Rules
}
