import json
import statistics
import time
from typing import Any

import requests

BASE_URL = "http://localhost:8000"

def run_benchmark(endpoint: str, method: str = "GET", body: dict = None, iterations: int = 10) -> dict[str, Any]:
    times = []
    status_codes = []

    for _ in range(iterations):
        start = time.time()
        try:
            if method == "GET":
                resp = requests.get(f"{BASE_URL}{endpoint}")
            elif method == "POST":
                resp = requests.post(f"{BASE_URL}{endpoint}", json=body)
            else:
                continue
        except Exception:
            continue

        elapsed = time.time() - start
        times.append(elapsed)
        status_codes.append(resp.status_code)

    if not times:
        return {"error": "No successful requests"}

    return {
        "endpoint": endpoint,
        "method": method,
        "iterations": len(times),
        "p50": statistics.median(times) * 1000,
        "p95": statistics.quantiles(times, n=20)[18] * 1000 if len(times) >= 20 else times[-1] * 1000,
        "p99": statistics.quantiles(times, n=100)[98] * 1000 if len(times) >= 100 else times[-1] * 1000,
        "min": min(times) * 1000,
        "max": max(times) * 1000,
        "avg": statistics.mean(times) * 1000,
        "status_codes": status_codes
    }

def main():
    results = []

    results.append(run_benchmark("/health", "GET", iterations=50))
    results.append(run_benchmark("/", "GET", iterations=50))

    if results:
        with open("benchmark_results.json", "w") as f:
            json.dump(results, f, indent=2)
        print("Benchmark results saved to benchmark_results.json")
    else:
        print("Benchmark failed")

if __name__ == "__main__":
    main()
