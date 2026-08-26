# ADR 0001: Data Plane Language

## Context
Gateway needs low latency, high concurrency, and WAF embedding.

## Decision
Use Go for Data Plane (gateway).

## Alternatives
- Python (FastAPI) - slower, harder to embed Coraza
- Rust - too early for team skills

## Consequences
- Go has Coraza integration
- Good performance
- Simple deployment (single binary)
