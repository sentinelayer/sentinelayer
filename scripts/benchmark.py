"""Bounded synthetic benchmark with explicit errors and upstream baseline."""
from __future__ import annotations
import argparse
import concurrent.futures
import json
import math
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit
import requests


def percentile(values, fraction):
    return sorted(values)[max(0, math.ceil(len(values) * fraction) - 1)] if values else None


def _timing(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and number >= 0 else None


def run_benchmark(origin, iterations=200, concurrency=1, timeout=3, prefix="/benchmark", extra_headers=None):
    if not 1 <= iterations <= 100000 or not 1 <= concurrency <= 64 or timeout <= 0:
        raise ValueError("invalid bounded benchmark settings")
    def sample(index):
        start = time.perf_counter()
        try:
            with requests.Session() as session:
                session.trust_env = False
                response = session.get(f"{origin.rstrip('/')}{prefix}/{index}",
                    headers={"User-Agent": "SentinelLayer-Benchmark/1.0", "Accept": "application/json", **(extra_headers or {})},
                    timeout=timeout, allow_redirects=False)
                status = str(response.status_code)
                try:
                    payload = response.json() if response.status_code == 200 else {}
                    processing = response.headers.get("X-SL-Gateway-Processing-Ms", payload.get("gateway_processing_ms"))
                    degraded = response.headers.get("X-SL-Gateway-Degraded", payload.get("gateway_degraded")) == "true"
                except (ValueError, AttributeError):
                    payload = {}
                    processing = None
                    degraded = False
                if processing is None:
                    processing = response.headers.get("X-SL-Gateway-Processing-Ms")
                degraded = degraded or response.headers.get("X-SL-Gateway-Degraded") == "true"
                stages = payload.get("gateway_stages_ms", {}) if isinstance(payload, dict) else {}
                stages = {stage: response.headers.get(f"X-SL-Gateway-{stage}-Ms", stages.get(stage)) for stage in ("WAF", "Behavior", "Risk")} if isinstance(stages, dict) else {}
                stages = {k: value for k, raw in stages.items() if (value := _timing(raw)) is not None} if isinstance(stages, dict) else {}
                processing = _timing(processing)
        except requests.RequestException as exc:
            status = type(exc).__name__
            processing = None
            degraded = False
            stages = {}
        return (time.perf_counter() - start) * 1000, status, processing, degraded, stages
    start = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        results = list(executor.map(sample, range(iterations)))
    elapsed = time.perf_counter() - start
    timings = [value for value, _, _, _, _ in results]
    statuses = Counter(status for _, status, _, _, _ in results)
    return {"attempts": iterations, "concurrency": concurrency, "elapsed_seconds": elapsed,
        "completed_requests_per_second": iterations / elapsed,
        "failures": sum(count for status, count in statuses.items() if status != "200"),
        "status_counts": dict(statuses),
        "degraded_responses": sum(degraded for _, _, _, degraded, _ in results),
        "gateway_processing_samples": sum(value is not None for _, _, value, _, _ in results),
        "gateway_processing_p95_ms": percentile([value for _, _, value, _, _ in results if value is not None], .95), "p50_ms": percentile(timings, .5),
        "p95_ms": percentile(timings, .95), "p99_ms": percentile(timings, .99), "max_ms": max(timings),
        "gateway_stage_samples": {stage: sum(stage in stages for _, _, _, _, stages in results) for stage in ("WAF", "Behavior", "Risk")},
        "gateway_stage_p95_ms": {stage: percentile([stages[stage] for _, _, _, _, stages in results if stage in stages], .95) for stage in ("WAF", "Behavior", "Risk")},
        "connection_mode": "new connection per request",
        "rate_limit_scope": "distinct paths; not one-path capacity"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gateway", required=True)
    parser.add_argument("--upstream", required=True)
    parser.add_argument("--iterations", type=int, default=200)
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--allow-remote", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    for target in (args.gateway, args.upstream):
        parsed = urlsplit(target)
        if parsed.scheme not in {"http", "https"} or parsed.username or parsed.password or not parsed.hostname:
            parser.error("HTTP origins without credentials required")
        if not args.allow_remote and parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
            parser.error("remote load requires explicit --allow-remote")
    common = {"iterations": args.iterations, "concurrency": args.concurrency}
    baseline = run_benchmark(args.upstream, prefix="/benchmark-baseline", **common)
    gateway = run_benchmark(args.gateway, prefix="/benchmark-gateway", **common)
    delta = gateway["p95_ms"] - baseline["p95_ms"]
    result = {"timestamp": datetime.now(UTC).isoformat(), "baseline": baseline, "gateway": gateway,
        "p95_distribution_difference_ms": delta, "latency_target_ms": 20,
        "local_latency_gate_pass": gateway["gateway_processing_samples"] == args.iterations and gateway["gateway_processing_p95_ms"] < 20 and not gateway["failures"] and not baseline["failures"] and not gateway["degraded_responses"],
        "limitations": "Difference of percentiles, not paired request overhead; synthetic workload, no production capacity or SLA claim."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["local_latency_gate_pass"] else 1)

if __name__ == "__main__":
    main()
