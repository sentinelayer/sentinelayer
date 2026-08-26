package waf

import (
"bufio"
"os"
"path/filepath"
"strings"
)

type CorazaRule struct {
ID      string
Phase   int
Action  string
Pattern string
}

type CorazaEngine struct {
Rules []CorazaRule
}

func NewCorazaEngine() *CorazaEngine {
return &CorazaEngine{
Rules: []CorazaRule{},
}
}

func (c *CorazaEngine) LoadCRS(rulesDir string) error {
return filepath.Walk(rulesDir, func(path string, info os.FileInfo, err error) error {
if err != nil {
return err
}
if !info.IsDir() && strings.HasSuffix(path, ".conf") {
file, err := os.Open(path)
if err != nil {
return err
}
defer file.Close()
scanner := bufio.NewScanner(file)
for scanner.Scan() {
line := scanner.Text()
if strings.Contains(line, "SecRule") {
rule := c.parseRule(line)
c.Rules = append(c.Rules, rule)
}
}
}
return nil
})
}

func (c *CorazaEngine) parseRule(line string) CorazaRule {
rule := CorazaRule{
ID:    "CRS-001",
Phase: 1,
}
if strings.Contains(line, "phase:1") {
rule.Phase = 1
} else if strings.Contains(line, "phase:2") {
rule.Phase = 2
}
if strings.Contains(line, "block") {
rule.Action = "block"
} else {
rule.Action = "allow"
}
// Extract pattern from @rx
if strings.Contains(line, "@rx") {
parts := strings.Split(line, "@rx")
if len(parts) > 1 {
pattern := strings.TrimSpace(parts[1])
pattern = strings.Split(pattern, "\"")[0]
rule.Pattern = pattern
}
}
return rule
}

func (c *CorazaEngine) Match(input string) bool {
for _, rule := range c.Rules {
if rule.Pattern != "" && strings.Contains(input, rule.Pattern) {
return true
}
}
return false
}
