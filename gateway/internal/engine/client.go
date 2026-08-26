package engine

import (
"bytes"
"context"
"encoding/json"
"fmt"
"net/http"
"sync"
"time"
)

type RiskRequest struct {
TenantID        string                 `json:"tenant_id"`
ApplicationID   string                 `json:"application_id"`
Endpoint        string                 `json:"endpoint"`
UserID          string                 `json:"user_id"`
Signals         []string               `json:"signals"`
Context         map[string]interface{} `json:"context"`
FailedAttempts  int                    `json:"failed_attempts"`
SuspiciousIP    bool                   `json:"suspicious_ip"`
UnusualTime     bool                   `json:"unusual_time"`
MultipleTenants bool                   `json:"multiple_tenants"`
}

type RiskResponse struct {
Action        string                 `json:"action"`
Score         float64                `json:"score"`
Confidence    float64                `json:"confidence"`
Signals       []string               `json:"signals"`
Factors       map[string]interface{} `json:"factors"`
Explanation   string                 `json:"explanation"`
EngineVersion string                 `json:"engine_version"`
}

type CircuitBreaker struct {
mu        sync.Mutex
failures  int
threshold int
openUntil time.Time
cooldown  time.Duration
}

func NewCircuitBreaker(threshold int, cooldown time.Duration) *CircuitBreaker {
return &CircuitBreaker{threshold: threshold, cooldown: cooldown}
}

func (c *CircuitBreaker) Allow() bool {
c.mu.Lock()
defer c.mu.Unlock()
if time.Now().Before(c.openUntil) {
return false
}
return true
}

func (c *CircuitBreaker) RecordSuccess() {
c.mu.Lock()
defer c.mu.Unlock()
c.failures = 0
c.openUntil = time.Time{}
}

func (c *CircuitBreaker) RecordFailure() {
c.mu.Lock()
defer c.mu.Unlock()
c.failures++
if c.failures >= c.threshold {
c.openUntil = time.Now().Add(c.cooldown)
}
}

type Client struct {
baseURL    string
httpClient *http.Client
cb         *CircuitBreaker
}

func NewClient(baseURL string) *Client {
if baseURL == "" {
baseURL = "http://127.0.0.1:8090"
}
return &Client{
baseURL:    baseURL,
httpClient: &http.Client{Timeout: 150 * time.Millisecond},
cb:         NewCircuitBreaker(5, 10*time.Second),
}
}

func (c *Client) Score(ctx context.Context, req RiskRequest) (*RiskResponse, error) {
if !c.cb.Allow() {
return nil, fmt.Errorf("circuit open")
}
body, err := json.Marshal(req)
if err != nil {
return nil, err
}
httpReq, err := http.NewRequestWithContext(ctx, http.MethodPost, c.baseURL+"/v1/score", bytes.NewReader(body))
if err != nil {
c.cb.RecordFailure()
return nil, err
}
httpReq.Header.Set("Content-Type", "application/json")
resp, err := c.httpClient.Do(httpReq)
if err != nil {
c.cb.RecordFailure()
return nil, err
}
defer resp.Body.Close()
if resp.StatusCode != http.StatusOK {
c.cb.RecordFailure()
return nil, fmt.Errorf("risk engine status %d", resp.StatusCode)
}
var out RiskResponse
if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
c.cb.RecordFailure()
return nil, err
}
c.cb.RecordSuccess()
return &out, nil
}
