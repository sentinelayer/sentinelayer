package policy

import (
	"context"
	"crypto/ed25519"
	"encoding/base64"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestConfiguredHostRoutingRejectsUnknownAndSpoofedTenants(t *testing.T) {
	_, key, s := fixture()
	public := base64.StdEncoding.EncodeToString(key.Public().(ed25519.PublicKey))
	keys, _ := json.Marshal(map[string]string{"pinned": public})
	t.Setenv("POLICY_SIGNING_PUBLIC_KEYS_JSON", string(keys))
	for _, name := range []string{"GATEWAY_POLICY_URL", "GATEWAY_POLICY_API_KEY", "GATEWAY_POLICY_ID", "GATEWAY_POLICY_TENANT_ID", "GATEWAY_POLICY_ACK_URL", "GATEWAY_INSTANCE_ID"} {
		t.Setenv(name, "")
	}
	bindings := []Binding{{"a.example", "https://cp.example/runtime", "test-service-key-at-least-24", "policy-a", "tenant-a"}, {"b.example", "https://cp.example/runtime", "test-service-key-at-least-24", "policy-b", "tenant-b"}}
	raw, _ := json.Marshal(bindings)
	t.Setenv("GATEWAY_POLICY_BINDINGS_JSON", string(raw))
	routing, err := RoutingFromEnvironment()
	if err != nil {
		t.Fatal(err)
	}
	a, err := routing.Select("A.EXAMPLE:443")
	if err != nil || a.TenantID != "tenant-a" {
		t.Fatal("incorrect A routing")
	}
	b, err := routing.Select("b.example")
	if err != nil || b.TenantID != "tenant-b" {
		t.Fatal("incorrect B routing")
	}
	if _, err := routing.Select("unknown.example"); err == nil {
		t.Fatal("unknown host bypassed policy")
	}
	if _, err := b.verify(signed(t, key, s), time.Unix(s.IssuedAt, 0)); err == nil {
		t.Fatal("accepted another tenant's bundle")
	}
	bindings[1].Host = "A.EXAMPLE"
	raw, _ = json.Marshal(bindings)
	t.Setenv("GATEWAY_POLICY_BINDINGS_JSON", string(raw))
	if _, err := RoutingFromEnvironment(); err == nil {
		t.Fatal("accepted duplicate host")
	}
	t.Setenv("GATEWAY_POLICY_URL", "https://cp.example/runtime")
	if _, err := RoutingFromEnvironment(); err == nil {
		t.Fatal("accepted ambiguous routing modes")
	}
}

func TestGatewayReportsExactVerifiedBundleAsynchronously(t *testing.T) {
	c, key, s := fixture()
	bundle := signed(t, key, s)
	received := make(chan []byte, 1)
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/runtime" {
			w.Write(bundle)
			return
		}
		if r.Method != "POST" || r.Header.Get("X-API-Key") != "test-service-key" {
			t.Error("receipt authentication missing")
		}
		var body struct {
			GatewayID string          `json:"gateway_id"`
			Bundle    json.RawMessage `json:"bundle"`
		}
		if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
			t.Error(err)
		}
		if body.GatewayID != "gateway-1" {
			t.Error("wrong gateway identity")
		}
		received <- body.Bundle
	}))
	defer server.Close()
	c.URL = server.URL + "/runtime"
	c.AckURL = server.URL + "/ack"
	c.GatewayID = "gateway-1"
	c.APIKey = "test-service-key"
	c.HTTP = server.Client()
	if _, err := c.Current(context.Background()); err != nil {
		t.Fatal(err)
	}
	select {
	case raw := <-received:
		var want, got Envelope
		json.Unmarshal(bundle, &want)
		json.Unmarshal(raw, &got)
		if got != want {
			t.Fatal("receipt changed the verified envelope")
		}
	case <-time.After(time.Second):
		t.Fatal("receipt was not delivered")
	}
}
