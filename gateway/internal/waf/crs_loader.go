package waf

import (
    "os"
    "path/filepath"
    "strings"
)

func LoadCRSRules(rulesDir string) ([]string, error) {
    var rules []string
    err := filepath.Walk(rulesDir, func(path string, info os.FileInfo, err error) error {
        if err != nil {
            return err
        }
        if !info.IsDir() && strings.HasSuffix(path, ".conf") {
            data, err := os.ReadFile(path)
            if err != nil {
                return err
            }
            rules = append(rules, string(data))
        }
        return nil
    })
    return rules, err
}
