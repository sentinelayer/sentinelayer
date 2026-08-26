package observability

import (
"github.com/prometheus/client_golang/prometheus"
"github.com/prometheus/client_golang/prometheus/promauto"
)

var (
RequestCount = promauto.NewCounterVec(
prometheus.CounterOpts{
Name: "gateway_requests_total",
Help: "Total number of requests",
},
[]string{"method", "path", "status"},
)
RequestLatency = promauto.NewHistogramVec(
prometheus.HistogramOpts{
Name:    "gateway_request_duration_seconds",
Help:    "Request latency in seconds",
Buckets: prometheus.DefBuckets,
},
[]string{"method", "path"},
)
BlockedTotal = promauto.NewCounterVec(
prometheus.CounterOpts{
Name: "gateway_blocked_total",
Help: "Total blocked requests by reason",
},
[]string{"reason"},
)
AllowedTotal = promauto.NewCounter(
prometheus.CounterOpts{
Name: "gateway_allowed_total",
Help: "Total allowed requests",
},
)
)

func IncBlocked(reason string) {
BlockedTotal.WithLabelValues(reason).Inc()
}

func IncAllowed() {
AllowedTotal.Inc()
}
