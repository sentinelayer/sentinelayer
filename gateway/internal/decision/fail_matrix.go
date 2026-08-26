package decision

type FailMatrix struct {
    Capabilities map[string]string
}

func NewFailMatrix() *FailMatrix {
    return &FailMatrix{
        Capabilities: map[string]string{
            "waf":        "fail-open",
            "ratelimit":  "fail-open",
            "auth":       "fail-closed",
            "risk":       "fail-open",
            "decision":   "fail-closed",
        },
    }
}

func (f *FailMatrix) GetPolicy(capability string) string {
    if policy, ok := f.Capabilities[capability]; ok {
        return policy
    }
    return "fail-closed"
}
