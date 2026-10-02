// Package policy verifies short-lived, tenant-bound control-plane policy bundles.
package policy

import (
	"bytes"
	"context"
	"crypto/ed25519"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/url"
	"os"
	"path"
	"strings"
	"sync"
	"time"
)

type Rules struct {
	Mode             string   `json:"mode"`
	BlockScore       int      `json:"block_score"`
	DenyPathPrefixes []string `json:"deny_path_prefixes"`
}
type Snapshot struct {
	PolicyID      string `json:"policy_id"`
	TenantID      string `json:"tenant_id"`
	ApplicationID string `json:"application_id"`
	Version       int    `json:"version"`
	IssuedAt      int64  `json:"issued_at"`
	ExpiresAt     int64  `json:"expires_at"`
	Rules         Rules  `json:"rules"`
}
type Envelope struct {
	Payload   string `json:"payload"`
	Signature string `json:"signature"`
	KeyID     string `json:"key_id"`
}
type Client struct {
	mu                              sync.Mutex
	URL, APIKey, PolicyID, TenantID string
	Keys                            map[string]ed25519.PublicKey
	HTTP                            *http.Client
	Now                             func() time.Time
	current                         *Snapshot
	checkedAt                       time.Time
}

func FromEnvironment() (*Client, error) {
	endpoint := os.Getenv("GATEWAY_POLICY_URL")
	if endpoint == "" {
		if os.Getenv("GATEWAY_POLICY_API_KEY") != "" || os.Getenv("GATEWAY_POLICY_ID") != "" || os.Getenv("GATEWAY_POLICY_TENANT_ID") != "" {
			return nil, errors.New("GATEWAY_POLICY_URL is required for policy bindings")
		}
		return nil, nil
	}
	parsed, err := url.Parse(endpoint)
	if err != nil || parsed.Hostname() == "" || parsed.User != nil || parsed.RawQuery != "" || parsed.Fragment != "" {
		return nil, errors.New("invalid policy URL")
	}
	if parsed.Scheme != "https" {
		ip := net.ParseIP(parsed.Hostname())
		if parsed.Scheme != "http" || ip == nil || !ip.IsLoopback() {
			return nil, errors.New("policy URL must use HTTPS or numeric loopback HTTP")
		}
	}
	c := &Client{URL: endpoint, APIKey: os.Getenv("GATEWAY_POLICY_API_KEY"), PolicyID: os.Getenv("GATEWAY_POLICY_ID"), TenantID: os.Getenv("GATEWAY_POLICY_TENANT_ID"), Keys: map[string]ed25519.PublicKey{}, Now: time.Now}
	if len(c.APIKey) < 24 || c.PolicyID == "" || c.TenantID == "" {
		return nil, errors.New("policy URL requires API key, policy ID and tenant ID")
	}
	var keys map[string]string
	if err := json.Unmarshal([]byte(os.Getenv("POLICY_SIGNING_PUBLIC_KEYS_JSON")), &keys); err != nil {
		return nil, errors.New("configured policy public keys are required")
	}
	for id, encoded := range keys {
		decoded, err := base64.StdEncoding.DecodeString(encoded)
		if err != nil || id == "" || len(decoded) != ed25519.PublicKeySize {
			return nil, errors.New("invalid policy public key")
		}
		c.Keys[id] = ed25519.PublicKey(decoded)
	}
	if len(c.Keys) == 0 {
		return nil, errors.New("at least one trusted policy public key is required")
	}
	c.HTTP = &http.Client{Timeout: 800 * time.Millisecond, Transport: &http.Transport{Proxy: nil}, CheckRedirect: func(_ *http.Request, _ []*http.Request) error { return errors.New("policy redirects are forbidden") }}
	return c, nil
}

func strictDecode(raw []byte, target any) error {
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(target); err != nil {
		return err
	}
	if err := decoder.Decode(new(any)); err != io.EOF {
		return errors.New("policy JSON has trailing data")
	}
	return nil
}
func (c *Client) verify(raw []byte, now time.Time) (*Snapshot, error) {
	var envelope Envelope
	if err := strictDecode(raw, &envelope); err != nil {
		return nil, errors.New("invalid policy envelope")
	}
	public, ok := c.Keys[envelope.KeyID]
	if !ok {
		return nil, errors.New("untrusted policy signing key")
	}
	payload, err := base64.StdEncoding.DecodeString(envelope.Payload)
	if err != nil {
		return nil, errors.New("invalid policy payload encoding")
	}
	signature, err := base64.StdEncoding.DecodeString(envelope.Signature)
	if err != nil || !ed25519.Verify(public, payload, signature) {
		return nil, errors.New("policy signature verification failed")
	}
	var snapshot Snapshot
	if err := strictDecode(payload, &snapshot); err != nil {
		return nil, errors.New("invalid signed policy payload")
	}
	if snapshot.PolicyID != c.PolicyID || snapshot.TenantID != c.TenantID || snapshot.Version < 1 {
		return nil, errors.New("policy binding mismatch")
	}
	if snapshot.IssuedAt > now.Unix()+30 || snapshot.ExpiresAt <= now.Unix() || snapshot.ExpiresAt <= snapshot.IssuedAt || snapshot.ExpiresAt-snapshot.IssuedAt > 60 {
		return nil, errors.New("policy validity window rejected")
	}
	if snapshot.Rules.Mode != "enforce" && snapshot.Rules.Mode != "monitor" {
		return nil, errors.New("unsupported policy mode")
	}
	if snapshot.Rules.BlockScore < 0 || snapshot.Rules.BlockScore > 100 || len(snapshot.Rules.DenyPathPrefixes) > 100 {
		return nil, errors.New("invalid policy limits")
	}
	for _, prefix := range snapshot.Rules.DenyPathPrefixes {
		if len(prefix) > 256 || !strings.HasPrefix(prefix, "/") || strings.ContainsAny(prefix, "?#\\%") || strings.TrimSuffix(prefix, "/") != strings.TrimSuffix(path.Clean(prefix), "/") {
			return nil, errors.New("invalid policy path prefix")
		}
		for _, ch := range prefix {
			if ch < 32 || ch > 126 {
				return nil, errors.New("invalid policy path character")
			}
		}
	}
	if c.current != nil && snapshot.Version < c.current.Version {
		return nil, errors.New("policy version rollback rejected")
	}
	return &snapshot, nil
}

// Current refreshes at most every ten seconds; an unexpired verified bundle is
// the only fallback. Expiry and signature errors never substitute an ALLOW.
func (c *Client) Current(ctx context.Context) (*Snapshot, error) {
	c.mu.Lock()
	defer c.mu.Unlock()
	now := c.Now()
	if c.current != nil && now.Sub(c.checkedAt) < 10*time.Second && c.current.ExpiresAt > now.Unix() {
		return clone(c.current), nil
	}
	c.checkedAt = now
	request, err := http.NewRequestWithContext(ctx, http.MethodGet, c.URL, nil)
	if err != nil {
		return nil, err
	}
	request.Header.Set("X-API-Key", c.APIKey)
	response, err := c.HTTP.Do(request)
	if err == nil {
		defer response.Body.Close()
		if response.StatusCode != http.StatusOK {
			err = fmt.Errorf("policy service status %d", response.StatusCode)
		} else {
			raw, readErr := io.ReadAll(io.LimitReader(response.Body, 65537))
			if readErr != nil || len(raw) > 65536 {
				err = errors.New("policy response limit exceeded")
			} else {
				var snapshot *Snapshot
				snapshot, err = c.verify(raw, c.Now())
				if err == nil {
					c.current = snapshot
					return clone(snapshot), nil
				}
			}
		}
	}
	if c.current != nil && c.current.ExpiresAt > c.Now().Unix() {
		return clone(c.current), nil
	}
	return nil, err
}
func clone(s *Snapshot) *Snapshot {
	copy := *s
	copy.Rules.DenyPathPrefixes = append([]string(nil), s.Rules.DenyPathPrefixes...)
	return &copy
}
func (s *Snapshot) Blocked(requestPath string, score float64) bool {
	if s.Rules.Mode != "enforce" {
		return false
	}
	if score >= float64(s.Rules.BlockScore) {
		return true
	}
	cleaned := path.Clean(requestPath)
	for _, prefix := range s.Rules.DenyPathPrefixes {
		base := strings.TrimSuffix(prefix, "/")
		if base == "" || cleaned == base || strings.HasPrefix(cleaned, base+"/") {
			return true
		}
	}
	return false
}
