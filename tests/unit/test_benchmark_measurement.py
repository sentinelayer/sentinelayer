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
