# ADR 0001: Data Plane Language = Go

## Status
Accepted

## Context
Data Plane handles every request (proxy, WAF, rate limit, decision). Must be low-latency, memory-safe enough, and easy to embed Coraza.

## Decision
Use Go for Gateway / Data Plane.

## Consequences
- Coraza (Go) integrates natively
- Single binary deploy
- Control Plane remains Python (FastAPI) for GRC, evidence, gates
- Clear process boundary: Go = request path, Python = management path
