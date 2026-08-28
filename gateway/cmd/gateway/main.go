package main

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"log"
	"net"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/sentinelayer/gateway/internal/authctx"
	"github.com/sentinelayer/gateway/internal/decision"
	"github.com/sentinelayer/gateway/internal/desync"
	"github.com/sentinelayer/gateway/internal/engine"
	"github.com/sentinelayer/gateway/internal/normalize"
	"github.com/sentinelayer/gateway/internal/observability"
	"github.com/sentinelayer/gateway/internal/ratelimit"
	"github.com/sentinelayer/gateway/internal/ssrf"
	"github.com/sentinelayer/gateway/internal/waf"
)

type RequestContext struct {
	TenantID          string `json:"tenant_id"`
	ApplicationID     string `json:"application_id"`
	Environment       string `json:"environment"`
	Endpoint          string `json:"endpoint"`
	UserID            string `json:"user_id"`
	SessionID         string `json:"session_id"`
	ResourceType      string `json:"resource_type"`
	ResourceID        string `json:"resource_id"`
	BusinessOperation string `json:"business_operation"`
	Sensitivity       string `json:"sensitivity"`
	Criticality       string `json:"criticality"`
}

type DecisionOutput struct {
	Action     string         `json:"action"`
	Score      float64        `json:"score"`
	Confidence float64        `json:"confidence"`
	Signals    []string       `json:"signals"`
	Reason     string         `json:"reason"`
	PolicyVer  string         `json:"policy_version"`
	Context    RequestContext `json:"context"`
	Timestamp  time.Time      `json:"timestamp"`
}

func classifyEndpoint(r *http.Request) string {
	path := r.URL.Path
	if strings.HasPrefix(path, "/health") || strings.HasPrefix(path, "/ready") || path == "/" {
		return "public"
	}

	// Login and registration must be reachable before a JWT exists. Keep
	// every other auth endpoint critical so logout, token changes, and
	// account mutations remain protected by the gateway.
	if path == "/api/v1/auth/login" || path == "/api/v1/auth/register" {
		return "public"
	}

	for _, p := range []string{"/api/v1/payments", "/api/v1/checkout", "/api/v1/admin", "/api/v1/keys", "/api/v1/auth"} {
		if strings.HasPrefix(path, p) {
			return "critical"
		}
	}
	return "normal"
}

func extractContext(r *http.Request, claims *authctx.Claims) RequestContext {
	ctx := RequestContext{
		Environment: os.Getenv("SL_ENV"),
		Endpoint:    r.URL.Path,
		Sensitivity: "internal",
		Criticality: "normal",
	}
	if ctx.Environment == "" {
		ctx.Environment = "production"
	}
	if claims != nil {
		ctx.TenantID = claims.TenantID
		ctx.UserID = claims.Sub
	} else {
		ctx.TenantID = r.Header.Get("X-Tenant-ID")
		ctx.UserID = r.Header.Get("X-User-ID")
	}
	ctx.ApplicationID = r.Header.Get("X-Application-ID")
	ctx.SessionID = r.Header.Get("X-Session-ID")
	ctx.ResourceType = r.Header.Get("X-Resource-Type")
	ctx.ResourceID = r.Header.Get("X-Resource-ID")
	ctx.BusinessOperation = r.Header.Get("X-Business-Op")
	if ctx.ApplicationID == "" {
		ctx.ApplicationID = "default"
	}
	if classifyEndpoint(r) == "critical" {
		ctx.Criticality = "critical"
		ctx.Sensitivity = "high"
	}
	return ctx
}

func jsonFloat(f float64) string {
	b, _ := json.Marshal(f)
	return string(b)
}

func clientAddress(r *http.Request) string {
	if host, _, err := net.SplitHostPort(r.RemoteAddr); err == nil {
		return host
	}
	return strings.TrimSpace(r.RemoteAddr)
}

func rateLimitKey(r *http.Request, ctx RequestContext) string {
	hash := sha256.New()
	for _, part := range []string{
		ctx.TenantID, ctx.UserID, ctx.SessionID, r.Header.Get("X-API-Key"),
		clientAddress(r), r.Method, r.URL.Path,
	} {
		_, _ = hash.Write([]byte(part))
		_, _ = hash.Write([]byte{0})
	}
	return "sl:gateway:rate:" + hex.EncodeToString(hash.Sum(nil))
}

func listenAddress() (string, error) {
	port := strings.TrimSpace(os.Getenv("PORT"))
	if port == "" {
		port = "8080"
	}
	value, err := strconv.Atoi(port)
	if err != nil || value < 1 || value > 65535 {
		return "", fmt.Errorf("PORT must be an integer between 1 and 65535")
	}
	return ":" + strconv.Itoa(value), nil
}

func main() {
	if os.Getenv("SL_ENFORCE_PROVENANCE") == "1" {
		expected := os.Getenv("SL_APPROVED_ARTIFACT_HASH")
		running := os.Getenv("SL_RUNNING_ARTIFACT_HASH")
		if expected == "" || running == "" || expected != running {
			log.Fatalf("RUNTIME PROVENANCE FAILED: expected=%s running=%s", expected, running)
		}
		log.Printf("Runtime provenance verified: %s", running)
	}

	crsDir := os.Getenv("CRS_RULES_DIR")
	if crsDir == "" {
		crsDir = "/app/waf/rules"
	}
	wafEngine, err := waf.NewEngine(crsDir)
	if err != nil {
		log.Fatalf("WAF init failed: %v", err)
	}
	log.Println("Coraza WAF initialized")

	redisAddr := os.Getenv("REDIS_ADDR")
	if redisAddr == "" {
		redisAddr = os.Getenv("REDIS_URL")
	}
	rateLimiter := ratelimit.NewRedisRateLimiter(redisAddr, 60)
	failMatrix := decision.NewFailMatrix()
	lkg := decision.NewLastKnownGood()
	riskClient := engine.NewClient(os.Getenv("RISK_ENGINE_URL"))
	behaviorClient := engine.NewBehaviorClient(os.Getenv("BEHAVIOR_ENGINE_URL"))

	jwtSecret := []byte(os.Getenv("JWT_SECRET"))
	if len(jwtSecret) < 32 {
		log.Fatal("JWT_SECRET must be configured with at least 32 bytes")
	}

	upstreamURL := os.Getenv("UPSTREAM_URL")
	if upstreamURL == "" {
		upstreamURL = "http://127.0.0.1:8005"
	}
	upstream, err := url.Parse(upstreamURL)
	if err != nil {
		log.Fatalf("invalid UPSTREAM_URL: %v", err)
	}
	proxy := httputil.NewSingleHostReverseProxy(upstream)

	mux := http.NewServeMux()
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		endpointClass := classifyEndpoint(r)
		signals := []string{}

		if desync.GuardDesync(r) {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusBadRequest)
			_ = json.NewEncoder(w).Encode(map[string]string{"error": "HTTP desync detected", "code": "DESYNC"})
			observability.IncBlocked("desync")
			return
		}

		host := r.Header.Get("X-Forwarded-Host")
		if host == "" {
			host = r.Host
		}
		if ssrf.IsBlockedHost(host) || ssrf.IsPrivateIP(host) {
			if failMatrix.ShouldFailClosed("ssrf", endpointClass) {
				w.Header().Set("Content-Type", "application/json")
				w.WriteHeader(http.StatusForbidden)
				_ = json.NewEncoder(w).Encode(map[string]string{"error": "SSRF blocked", "code": "SSRF"})
				observability.IncBlocked("ssrf")
				return
			}
		}

		var claims *authctx.Claims
		authHeader := r.Header.Get("Authorization")
		if authHeader != "" {
			c, aerr := authctx.ValidateJWT(authHeader, jwtSecret)
			if aerr != nil {
				if failMatrix.ShouldFailClosed("auth", endpointClass) {
					w.Header().Set("Content-Type", "application/json")
					w.WriteHeader(http.StatusUnauthorized)
					_ = json.NewEncoder(w).Encode(map[string]string{"error": "invalid token", "code": "AUTH"})
					observability.IncBlocked("auth")
					return
				}
				signals = append(signals, "auth_failure")

			} else {
				claims = c
			}
		} else if endpointClass == "critical" {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusUnauthorized)
			_ = json.NewEncoder(w).Encode(map[string]string{"error": "auth required", "code": "AUTH_REQUIRED"})
			observability.IncBlocked("auth")
			return
		}

		reqCtx := extractContext(r, claims)
		normalize.NormalizeRequest(r)
		if _, err := normalize.NormalizeBody(r); err != nil {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusBadRequest)
			_ = json.NewEncoder(w).Encode(map[string]string{"error": "request body normalization failed", "code": "BODY"})
			observability.IncBlocked("body")
			return
		}

		blocked, ruleID, msg := wafEngine.ProcessRequest(r)
		wafBlocked := blocked
		if blocked {
			// Keep the request in the decision path for risk/audit telemetry,
			// but never let a matched WAF violation become an ALLOW.
			signals = append(signals, "waf_block")
		}

		if rateLimiter != nil {
			allowed, rateErr := rateLimiter.Allow(rateLimitKey(r, reqCtx))
			if rateErr != nil {
				if failMatrix.ShouldFailClosed("redis", endpointClass) {
					w.Header().Set("Content-Type", "application/json")
					w.WriteHeader(http.StatusServiceUnavailable)
					_ = json.NewEncoder(w).Encode(map[string]string{"error": "rate limiter unavailable", "code": "RATE_DEPENDENCY"})
					observability.IncBlocked("rate_dependency")
					return
				}
				signals = append(signals, "rate_limiter_unavailable")
			} else if !allowed {
				w.Header().Set("Retry-After", "60")
				w.Header().Set("Content-Type", "application/json")
				w.WriteHeader(http.StatusTooManyRequests)
				_ = json.NewEncoder(w).Encode(map[string]string{"error": "Rate limit exceeded", "code": "RATE"})
				observability.IncBlocked("rate")
				return
			}
		}

		behaviorCtx, behaviorCancel := context.WithTimeout(r.Context(), 80*time.Millisecond)
		behaviorResp, behaviorErr := behaviorClient.Analyze(behaviorCtx, engine.BehaviorRequest{
			TenantID: reqCtx.TenantID, ApplicationID: reqCtx.ApplicationID, Environment: reqCtx.Environment,
			Endpoint: reqCtx.Endpoint, UserID: reqCtx.UserID, SessionID: reqCtx.SessionID,
			ClientID: clientAddress(r), ResourceType: reqCtx.ResourceType, ResourceID: reqCtx.ResourceID,
			BusinessOp: reqCtx.BusinessOperation, Sensitivity: reqCtx.Sensitivity, Criticality: reqCtx.Criticality,
		})
		behaviorCancel()
		behaviorBlocked := false
		if behaviorErr != nil {
			signals = append(signals, "behavior_engine_unavailable")
			behaviorBlocked = failMatrix.ShouldFailClosed("behavior_engine", endpointClass)
		} else {
			signals = append(signals, behaviorResp.Signals...)
		}

		score := 0.0
		confidence := 0.85
		var action string
		var reason string

		riskReq := engine.RiskRequest{
			TenantID:      reqCtx.TenantID,
			ApplicationID: reqCtx.ApplicationID,
			Endpoint:      reqCtx.Endpoint,
			UserID:        reqCtx.UserID,
			Signals:       signals,
			Context: map[string]interface{}{
				"criticality": reqCtx.Criticality,
				"sensitivity": reqCtx.Sensitivity,
			},
		}
		rctx, cancel := context.WithTimeout(r.Context(), 120*time.Millisecond)
		riskResp, riskErr := riskClient.Score(rctx, riskReq)
		cancel()

		if riskErr != nil {
			if failMatrix.ShouldFailClosed("risk_engine", endpointClass) {
				action = "BLOCK"
				score = 100
				confidence = 0.5
				reason = "risk_engine_unavailable_fail_closed"
			} else if v, ok := lkg.Get(reqCtx.TenantID + ":" + reqCtx.Endpoint); ok {
				if prev, ok2 := v.(DecisionOutput); ok2 {
					action = prev.Action
					score = prev.Score
					confidence = prev.Confidence
					reason = "last_known_good"
				} else {
					action = "MONITOR"
					reason = "risk_engine_unavailable_monitor"
				}
			} else {
				action = "MONITOR"
				reason = "risk_engine_unavailable_monitor"
			}
			signals = append(signals, "risk_engine_error")
		} else {
			score = riskResp.Score
			confidence = riskResp.Confidence
			action = riskResp.Action
			reason = riskResp.Explanation
			if reason == "" {
				reason = "risk_engine"
			}
		}

		if behaviorBlocked {
			action = "BLOCK"
			score = 100
			confidence = 0
			reason = "behavior_engine_unavailable_fail_closed"
		}
		if wafBlocked {
			action = "BLOCK"
			reason = fmt.Sprintf("waf_block rule=%d: %s", ruleID, msg)
		}
		if action == "BLOCK" && endpointClass == "public" && !wafBlocked {
			action = "MONITOR"
		}

		out := DecisionOutput{
			Action: action, Score: score, Confidence: confidence,
			Signals: signals, Reason: reason, PolicyVer: "v1.0.0",
			Context: reqCtx, Timestamp: time.Now().UTC(),
		}
		lkg.Save(reqCtx.TenantID+":"+reqCtx.Endpoint, out)

		if action == "BLOCK" {
			w.Header().Set("Content-Type", "application/json")
			w.Header().Set("X-SL-Decision", "BLOCK")
			w.Header().Set("X-SL-Score", jsonFloat(score))
			w.WriteHeader(http.StatusForbidden)
			_ = json.NewEncoder(w).Encode(out)
			observability.IncBlocked("risk")
			return
		}

		r.Header.Set("X-SL-Decision", action)
		r.Header.Set("X-SL-Score", jsonFloat(score))
		r.Header.Set("X-SL-Tenant", reqCtx.TenantID)
		r.Header.Set("X-SL-Latency-Ms", jsonFloat(float64(time.Since(start).Milliseconds())))
		proxy.ServeHTTP(w, r)
		observability.IncAllowed()
	})

	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(map[string]interface{}{
			"status": "healthy", "waf": "coraza",
			"pipeline":   "waf->auth->rate->risk_http->decision->upstream",
			"provenance": os.Getenv("SL_RUNNING_ARTIFACT_HASH"),
		})
	})
	mux.HandleFunc("/ready", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(map[string]string{"status": "ready"})
	})

	addr, err := listenAddress()
	if err != nil {
		log.Fatal(err)
	}
	server := &http.Server{
		Addr:         addr,
		Handler:      mux,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}
	log.Printf("Gateway %s — full pipeline + risk HTTP client", addr)
	log.Fatal(server.ListenAndServe())
}
