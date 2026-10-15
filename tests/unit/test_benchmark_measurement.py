import importlib.util
from pathlib import Path
import requests

spec = importlib.util.spec_from_file_location("sentinel_benchmark", Path(__file__).parents[2] / "scripts/benchmark.py")
benchmark = importlib.util.module_from_spec(spec)
spec.loader.exec_module(benchmark)


def test_percentiles_use_sorted_nearest_rank():
    assert benchmark.percentile([30, 10, 20], .95) == 30
    assert benchmark.percentile([30, 10, 20], .5) == 20
    assert benchmark.percentile([], .95) is None


def test_timeouts_remain_in_denominator(monkeypatch):
    def fail(*args, **kwargs):
        raise requests.Timeout("synthetic timeout")
    monkeypatch.setattr(requests.Session, "get", fail)
    result = benchmark.run_benchmark("http://127.0.0.1", iterations=5)
    assert result["attempts"] == 5
    assert result["failures"] == 5
    assert result["status_counts"] == {"Timeout": 5}
    assert result["gateway_processing_samples"] == 0


def test_engine_worker_budget_rejects_unbounded_process_count():
    from scripts.validate_runtime_config import validate
    assert "SL_ENGINE_WORKERS must be 1 or 2" in validate({"SL_ENV": "test", "SL_ENGINE_WORKERS": "100"})
    assert not validate({"SL_ENV": "test", "SL_ENGINE_WORKERS": "2", "REDIS_URL": "redis://127.0.0.1:6379/0"})
    assert "Two engine workers require shared REDIS_URL state" in validate({"SL_ENV": "test", "SL_ENGINE_WORKERS": "2"})


def test_boolean_degradation_and_all_gateway_stages_are_reported(monkeypatch):
    class FakeResponse:
        status_code = 200
        headers = {"X-SL-Gateway-Processing-Ms": "4.5",
                   "X-SL-Gateway-Rate-Ms": "1.2",
                   "X-SL-Gateway-Policy-Ms": "0.7"}
        def json(self):
            return {"gateway_degraded": True, "gateway_stages_ms": {
                "WAF": 0.5, "Behavior": 0.3, "Risk": 0.2,
            }}

    monkeypatch.setattr(requests.Session, "get", lambda *args, **kwargs: FakeResponse())
    result = benchmark.run_benchmark("http://localhost", iterations=3)
    assert result["attempts"] == 3
    assert result["failures"] == 0
    assert result["degraded_responses"] == 3
    assert result["gateway_processing_samples"] == 3
    assert result["gateway_processing_p95_ms"] == 4.5
    assert result["gateway_stage_samples"] == {
        "WAF": 3, "Rate": 3, "Policy": 3, "Behavior": 3, "Risk": 3,
    }
    assert result["gateway_stage_p95_ms"]["Rate"] == 1.2
    assert result["gateway_stage_p95_ms"]["Policy"] == 0.7


def test_benchmark_rejects_nan_negative_and_unreported_stage_timing(monkeypatch):
    class FakeResponse:
        status_code = 200
        headers = {"X-SL-Gateway-Degraded": "false",
                   "X-SL-Gateway-Processing-Ms": "nan",
                   "X-SL-Gateway-Rate-Ms": "-1",
                   "X-SL-Gateway-Policy-Ms": "Infinity"}
        def json(self):
            return {"gateway_degraded": True, "gateway_stages_ms": {
                "Behavior": float("nan"), "Risk": "bad",
            }}

    monkeypatch.setattr(requests.Session, "get", lambda *args, **kwargs: FakeResponse())
    result = benchmark.run_benchmark("http://localhost", iterations=2)
    assert result["degraded_responses"] == 0  # explicit header overrides JSON
    assert result["gateway_processing_samples"] == 0
    assert all(samples == 0 for samples in result["gateway_stage_samples"].values())
    assert all(value is None for value in result["gateway_stage_p95_ms"].values())
