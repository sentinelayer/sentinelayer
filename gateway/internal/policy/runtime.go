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
	"log"
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
type policyRefresh struct {
	done chan struct{}
	err  error
}

type Client struct {
	floor                           int
	statePath                       string
	mu                              sync.Mutex
	URL, APIKey, PolicyID, TenantID string
	AckURL, GatewayID               string
	ackRunning                      bool
	Keys                            map[string]ed25519.PublicKey
	HTTP                            *http.Client
	Now                             func() time.Time
	current                         *Snapshot
	checkedAt                       time.Time
	inFlight                        *policyRefresh
}

func FromEnvironment() (*Client, error) {
	endpoint := os.Getenv("GATEWAY_POLICY_URL")
	if endpoint == "" {
		if os.Getenv("GATEWAY_POLICY_API_KEY") != "" || os.Getenv("GATEWAY_POLICY_ID") != "" || os.Getenv("GATEWAY_POLICY_TENANT_ID") != "" {
			return nil, errors.New("GATEWAY_POLICY_URL is required for policy bindings")
		}
		return nil, nil
	}
	return newClient(endpoint, os.Getenv("GATEWAY_POLICY_API_KEY"), os.Getenv("GATEWAY_POLICY_ID"), os.Getenv("GATEWAY_POLICY_TENANT_ID"))
}

func validateEndpoint(endpoint string) error {
	parsed, err := url.Parse(endpoint)
	if err != nil || parsed.Hostname() == "" || parsed.User != nil || parsed.RawQuery != "" || parsed.Fragment != "" {
		return errors.New("invalid policy URL")
	}
	if parsed.Scheme != "https" {
		ip := net.ParseIP(parsed.Hostname())
		if parsed.Scheme != "http" || ip == nil || !ip.IsLoopback() {
			return errors.New("policy URL must use HTTPS or numeric loopback HTTP")
		}
	}
	return nil
}

func newClient(endpoint, apiKey, policyID, tenantID string) (*Client, error) {
	if err := validateEndpoint(endpoint); err != nil {
		return nil, err
	}
	c := &Client{URL: endpoint, APIKey: apiKey, PolicyID: policyID, TenantID: tenantID, Keys: map[string]ed25519.PublicKey{}, Now: time.Now}
	c.AckURL = os.Getenv("GATEWAY_POLICY_ACK_URL")
	c.GatewayID = os.Getenv("GATEWAY_INSTANCE_ID")
	if (c.AckURL == "") != (c.GatewayID == "") {
		return nil, errors.New("policy acknowledgement requires both URL and gateway instance ID")
	}
	if c.AckURL != "" {
		if err := validateEndpoint(c.AckURL); err != nil {
			return nil, err
		}
		if len(c.GatewayID) > 64 {
			return nil, errors.New("gateway instance ID exceeds 64 bytes")
		}
	}
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
	if err := c.initState(os.Getenv("GATEWAY_POLICY_STATE_DIR")); err != nil {
		return nil, err
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
	if snapshot.Version < c.floor || (c.current != nil && snapshot.Version < c.current.Version) {
		return nil, errors.New("policy version rollback rejected")
	}
	return &snapshot, nil
}

// Current shares one refresh without holding the cache lock during network I/O.
// Only unexpired verified snapshots may serve while a refresh is in flight.
func (c *Client) Current(ctx context.Context) (*Snapshot, error) {
	c.mu.Lock()
	now := c.Now()
	valid := c.current != nil && c.current.ExpiresAt > now.Unix()
	if valid && (now.Sub(c.checkedAt) < 10*time.Second || c.inFlight != nil) {
		snapshot := clone(c.current)
		c.mu.Unlock()
		return snapshot, nil
	}
	if refresh := c.inFlight; refresh != nil {
		c.mu.Unlock()
		select {
		case <-ctx.Done():
			return nil, ctx.Err()
		case <-refresh.done:
			c.mu.Lock()
			defer c.mu.Unlock()
			if c.current != nil && c.current.ExpiresAt > c.Now().Unix() {
				return clone(c.current), nil
			}
			if refresh.err != nil {
				return nil, refresh.err
			}
			return nil, errors.New("verified policy expired while waiting for refresh")
		}
	}
	refresh := &policyRefresh{done: make(chan struct{})}
	c.inFlight = refresh
	c.checkedAt = now
	c.mu.Unlock()

	raw, err := c.fetch(ctx)
	c.mu.Lock()
	defer c.mu.Unlock()
	if err == nil {
		var snapshot *Snapshot
		snapshot, err = c.verify(raw, c.Now())
		if err == nil {
			err = c.persistFloor(snapshot.Version)
		}
		if err == nil {
			c.current = snapshot
			c.report(raw)
		}
	}
	refresh.err = err
	c.inFlight = nil
	close(refresh.done)
	if c.current != nil && c.current.ExpiresAt > c.Now().Unix() {
		return clone(c.current), nil
	}
	if err == nil {
		err = errors.New("verified policy expired during refresh")
	}
	return nil, err
}

func (c *Client) fetch(ctx context.Context) ([]byte, error) {
	request, err := http.NewRequestWithContext(ctx, http.MethodGet, c.URL, nil)
	if err != nil {
		return nil, err
	}
	request.Header.Set("X-API-Key", c.APIKey)
	response, err := c.HTTP.Do(request)
	if err != nil {
		return nil, err
	}
	defer response.Body.Close()
	if response.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("policy service status %d", response.StatusCode)
	}
	raw, err := io.ReadAll(io.LimitReader(response.Body, 65537))
	if err != nil || len(raw) > 65536 {
		return nil, errors.New("policy response limit exceeded")
	}
	return raw, nil
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

// report is bounded to one asynchronous HTTP call per client. Receipt failure
// never changes verified enforcement; the control plane exposes stale status.
func (c *Client) report(raw []byte) {
	if c.AckURL == "" || c.ackRunning {
		return
	}
	c.ackRunning = true
	bundle := append([]byte(nil), raw...)
	go func() {
		defer func() { c.mu.Lock(); c.ackRunning = false; c.mu.Unlock() }()
		body, err := json.Marshal(struct {
			GatewayID string          `json:"gateway_id"`
			Bundle    json.RawMessage `json:"bundle"`
		}{c.GatewayID, json.RawMessage(bundle)})
		if err != nil {
			return
		}
		ctx, cancel := context.WithTimeout(context.Background(), 800*time.Millisecond)
		defer cancel()
		request, err := http.NewRequestWithContext(ctx, http.MethodPost, c.AckURL, bytes.NewReader(body))
		if err != nil {
			return
		}
		request.Header.Set("Content-Type", "application/json")
		request.Header.Set("X-API-Key", c.APIKey)
		response, err := c.HTTP.Do(request)
		if err != nil {
			log.Print("policy receipt delivery failed")
			return
		}
		defer response.Body.Close()
		if response.StatusCode != http.StatusOK {
			log.Printf("policy receipt rejected: status=%d", response.StatusCode)
		}
	}()
}
