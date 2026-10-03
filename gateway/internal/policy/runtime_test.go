package policy

import (
	"context"
	"crypto/ed25519"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"net/http/httptest"
	"sync/atomic"
	"testing"
	"time"
)

func signed(t *testing.T, key ed25519.PrivateKey, s Snapshot) []byte {
	t.Helper()
	payload, err := json.Marshal(s)
	if err != nil {
		t.Fatal(err)
	}
	raw, err := json.Marshal(Envelope{base64.StdEncoding.EncodeToString(payload), base64.StdEncoding.EncodeToString(ed25519.Sign(key, payload)), "pinned"})
	if err != nil {
		t.Fatal(err)
	}
	return raw
}

func fixture() (*Client, ed25519.PrivateKey, Snapshot) {
	key := ed25519.NewKeyFromSeed(make([]byte, 32))
	now := time.Unix(2000000000, 0)
	c := &Client{PolicyID: "policy-a", TenantID: "tenant-a", Keys: map[string]ed25519.PublicKey{"pinned": key.Public().(ed25519.PublicKey)}, Now: func() time.Time { return now }}
	s := Snapshot{PolicyID: "policy-a", TenantID: "tenant-a", Version: 2, IssuedAt: now.Unix(), ExpiresAt: now.Unix() + 60, Rules: Rules{Mode: "enforce", BlockScore: 80, DenyPathPrefixes: []string{"/private"}}}
	return c, key, s
}

func TestSignatureBindingValidityAndRollback(t *testing.T) {
	c, key, s := fixture()
	if _, err := c.verify(signed(t, key, s), c.Now()); err != nil {
		t.Fatal(err)
	}
	tests := map[string]func(*Snapshot){
		"tenant":            func(s *Snapshot) { s.TenantID = "other" },
		"policy":            func(s *Snapshot) { s.PolicyID = "other" },
		"expired":           func(s *Snapshot) { s.ExpiresAt = s.IssuedAt },
		"future":            func(s *Snapshot) { s.IssuedAt += 31; s.ExpiresAt += 31 },
		"long validity":     func(s *Snapshot) { s.ExpiresAt++ },
		"mode":              func(s *Snapshot) { s.Rules.Mode = "disable" },
		"score":             func(s *Snapshot) { s.Rules.BlockScore = 101 },
		"noncanonical path": func(s *Snapshot) { s.Rules.DenyPathPrefixes = []string{"/a/../private"} },
		"encoded path":      func(s *Snapshot) { s.Rules.DenyPathPrefixes = []string{"/%70rivate"} },
	}
	for name, mutate := range tests {
		t.Run(name, func(t *testing.T) {
			bad := s
			mutate(&bad)
			if _, err := c.verify(signed(t, key, bad), c.Now()); err == nil {
				t.Fatal("accepted invalid bundle")
			}
		})
	}
	wrong := ed25519.NewKeyFromSeed([]byte("different-test-seed-32-characters")[:32])
	if _, err := c.verify(signed(t, wrong, s), c.Now()); err == nil {
		t.Fatal("accepted forged signature")
	}
	c.current = &s
	older := s
	older.Version--
	if _, err := c.verify(signed(t, key, older), c.Now()); err == nil {
		t.Fatal("accepted rollback")
	}
}

func TestVerifiedFallbackEndsAtExpiry(t *testing.T) {
	c, key, s := fixture()
	now := c.Now()
	c.Now = func() time.Time { return now }
	var good atomic.Bool
	good.Store(true)
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Header.Get("X-API-Key") != "test-service-key" {
			t.Error("missing service authentication")
		}
		if good.Load() {
			w.Write(signed(t, key, s))
		} else {
			w.WriteHeader(503)
		}
	}))
	defer server.Close()
	c.URL = server.URL
	c.APIKey = "test-service-key"
	c.HTTP = server.Client()
	got, err := c.Current(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	got.Rules.DenyPathPrefixes[0] = "/mutated" // cache must not expose mutable slices
	good.Store(false)
	now = now.Add(11 * time.Second)
	got, err = c.Current(context.Background())
	if err != nil || got.Rules.DenyPathPrefixes[0] != "/private" {
		t.Fatal("verified fallback unavailable or mutable")
	}
	now = now.Add(49 * time.Second)
	if _, err = c.Current(context.Background()); err == nil {
		t.Fatal("accepted expired fallback")
	}
}

func TestExpiryWhileFetching(t *testing.T) {
	c, key, s := fixture()
	var clock atomic.Int64
	clock.Store(c.Now().Unix())
	c.Now = func() time.Time { return time.Unix(clock.Load(), 0) }
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { clock.Add(60); w.Write(signed(t, key, s)) }))
	defer server.Close()
	c.URL = server.URL
	c.HTTP = server.Client()
	if _, err := c.Current(context.Background()); err == nil {
		t.Fatal("accepted bundle expired during fetch")
	}
}

func TestRulesRespectPathBoundariesAndMonitor(t *testing.T) {
	_, _, s := fixture()
	if !s.Blocked("/private/a", 0) || !s.Blocked("/private", 0) || s.Blocked("/private-ish", 0) || !s.Blocked("/safe", 80) {
		t.Fatal("incorrect rule boundaries")
	}
	s.Rules.Mode = "monitor"
	if s.Blocked("/private", 100) {
		t.Fatal("monitor applied additional blocking")
	}
}

func TestEnvironmentRejectsUnsafeEndpointAndMissingTrust(t *testing.T) {
	for _, endpoint := range []string{"http://example.com/runtime", "https://user:pass@example.com/runtime", "https://example.com/runtime?key=secret"} {
		t.Setenv("GATEWAY_POLICY_URL", endpoint)
		if _, err := FromEnvironment(); err == nil {
			t.Fatal("accepted unsafe endpoint")
		}
	}
	t.Setenv("GATEWAY_POLICY_URL", "https://example.com/runtime")
	t.Setenv("GATEWAY_POLICY_API_KEY", "test-service-key-at-least-24")
	t.Setenv("GATEWAY_POLICY_ID", "p")
	t.Setenv("GATEWAY_POLICY_TENANT_ID", "t")
	t.Setenv("POLICY_SIGNING_PUBLIC_KEYS_JSON", "{}")
	if _, err := FromEnvironment(); err == nil {
		t.Fatal("accepted empty trust store")
	}
}

func TestWarmPolicyDoesNotWaitForInFlightRefresh(t *testing.T) {
	c, key, snapshot := fixture()
	c.current = &snapshot
	c.checkedAt = c.Now().Add(-11 * time.Second)
	entered := make(chan struct{})
	release := make(chan struct{})
	var calls atomic.Int64
	updated := snapshot
	updated.Version++
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		calls.Add(1)
		close(entered)
		<-release
		_, _ = w.Write(signed(t, key, updated))
	}))
	defer server.Close()
	c.URL, c.HTTP = server.URL, server.Client()
	refreshed := make(chan error, 1)
	go func() { _, err := c.Current(context.Background()); refreshed <- err }()
	<-entered
	warm := make(chan error, 1)
	go func() {
		got, err := c.Current(context.Background())
		if err == nil && got.Version != snapshot.Version {
			err = fmt.Errorf("unexpected warm version %d", got.Version)
		}
		warm <- err
	}()
	var fast bool
	select {
	case err := <-warm:
		fast = true
		if err != nil {
			t.Error(err)
		}
	case <-time.After(100 * time.Millisecond):
	}
	close(release)
	if err := <-refreshed; err != nil {
		t.Fatal(err)
	}
	if !fast {
		<-warm
		t.Fatal("verified unexpired policy waited behind control-plane network I/O")
	}
	got, err := c.Current(context.Background())
	if err != nil || got.Version != updated.Version {
		t.Fatalf("refresh not installed: got=%v err=%v", got, err)
	}
	if calls.Load() != 1 {
		t.Fatalf("duplicate refreshes: %d", calls.Load())
	}
}

func TestExpiredPolicyWaitRespectsCancellationAndNeverAllows(t *testing.T) {
	c, _, snapshot := fixture()
	snapshot.ExpiresAt = c.Now().Unix()
	c.current = &snapshot
	entered, release := make(chan struct{}), make(chan struct{})
	var requests atomic.Int64
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if requests.Add(1) == 1 {
			close(entered)
		}
		<-release
		w.WriteHeader(http.StatusServiceUnavailable)
	}))
	defer server.Close()
	c.URL, c.HTTP = server.URL, server.Client()
	refreshed := make(chan error, 1)
	go func() {
		got, err := c.Current(context.Background())
		if got != nil {
			err = fmt.Errorf("expired policy returned")
		}
		refreshed <- err
	}()
	<-entered
	ctx, cancel := context.WithTimeout(context.Background(), 25*time.Millisecond)
	defer cancel()
	waiting := make(chan error, 1)
	go func() {
		got, err := c.Current(ctx)
		if got != nil {
			err = fmt.Errorf("expired policy returned to waiter")
		}
		waiting <- err
	}()
	var waitErr error
	var bounded bool
	select {
	case waitErr = <-waiting:
		bounded = true
	case <-time.After(100 * time.Millisecond):
	}
	close(release)
	if err := <-refreshed; err == nil {
		t.Fatal("refresh failure accepted expired policy")
	}
	if !bounded {
		<-waiting
		t.Fatal("expired policy wait ignored context deadline")
	}
	if !errors.Is(waitErr, context.DeadlineExceeded) {
		t.Fatalf("wait error=%v; want deadline", waitErr)
	}
	if requests.Load() != 1 {
		t.Fatalf("cold/expired wait started duplicate refreshes: %d", requests.Load())
	}
}
