package policy

import (
	"errors"
	"net"
	"os"
	"strings"
)

// Routing binds operator-configured hosts to trusted tenant/policy clients.
// It never uses X-Tenant-ID or X-Forwarded-Host to select policy identity.
type Routing struct {
	Default *Client
	Hosts   map[string]*Client
}
type Binding struct {
	Host     string `json:"host"`
	URL      string `json:"url"`
	APIKey   string `json:"api_key"`
	PolicyID string `json:"policy_id"`
	TenantID string `json:"tenant_id"`
}

func RoutingFromEnvironment() (*Routing, error) {
	raw := os.Getenv("GATEWAY_POLICY_BINDINGS_JSON")
	if raw == "" {
		client, err := FromEnvironment()
		if err != nil {
			return nil, err
		}
		if client == nil {
			if os.Getenv("GATEWAY_POLICY_ACK_URL") != "" || os.Getenv("GATEWAY_INSTANCE_ID") != "" {
				return nil, errors.New("receipt configuration requires a policy binding")
			}
			return nil, nil
		}
		return &Routing{Default: client}, nil
	}
	for _, name := range []string{"GATEWAY_POLICY_URL", "GATEWAY_POLICY_API_KEY", "GATEWAY_POLICY_ID", "GATEWAY_POLICY_TENANT_ID"} {
		if os.Getenv(name) != "" {
			return nil, errors.New("host policy bindings cannot be mixed with the default binding")
		}
	}
	var bindings []Binding
	if err := strictDecode([]byte(raw), &bindings); err != nil || len(bindings) == 0 || len(bindings) > 100 {
		return nil, errors.New("host policy bindings must contain 1 to 100 entries")
	}
	routing := &Routing{Hosts: map[string]*Client{}}
	identities := map[string]*Client{}
	for _, binding := range bindings {
		host := strings.ToLower(binding.Host)
		if host == "" || len(host) > 253 || host != strings.TrimSpace(host) || strings.HasSuffix(host, ".") {
			return nil, errors.New("invalid policy host")
		}
		for _, ch := range host {
			if !((ch >= 'a' && ch <= 'z') || (ch >= '0' && ch <= '9') || ch == '.' || ch == '-') {
				return nil, errors.New("policy hosts must be DNS host names without ports")
			}
		}
		for _, label := range strings.Split(host, ".") {
			if len(label) == 0 || len(label) > 63 || strings.HasPrefix(label, "-") || strings.HasSuffix(label, "-") {
				return nil, errors.New("invalid policy DNS label")
			}
		}
		if _, exists := routing.Hosts[host]; exists {
			return nil, errors.New("duplicate policy host")
		}
		client, err := newClient(binding.URL, binding.APIKey, binding.PolicyID, binding.TenantID)
		if err != nil {
			return nil, err
		}
		identity := binding.TenantID + "\x00" + binding.PolicyID
		if existing, ok := identities[identity]; ok {
			if existing.URL != client.URL || existing.APIKey != client.APIKey {
				return nil, errors.New("one tenant/policy identity must use one endpoint and service credential")
			}
			client = existing
		} else {
			identities[identity] = client
		}
		routing.Hosts[host] = client
	}
	return routing, nil
}

func (r *Routing) Select(requestHost string) (*Client, error) {
	if r.Default != nil {
		return r.Default, nil
	}
	host := strings.ToLower(requestHost)
	if hostname, _, err := net.SplitHostPort(host); err == nil {
		host = hostname
	}
	client, ok := r.Hosts[host]
	if !ok {
		return nil, errors.New("unconfigured policy host")
	}
	return client, nil
}
