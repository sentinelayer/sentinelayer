import httpx
import pytest
from scripts.verify_pilot import capacity_probe, POLICY_ID


@pytest.mark.parametrize('fault', [None, 'missing', 'nonfinite', 'degraded', 'policy', 'http'])
def test_deployed_measurement_requires_trusted_complete_success(monkeypatch, fault):
    monkeypatch.setenv('PILOT_CAPACITY_REQUESTS', '100')
    monkeypatch.setenv('PILOT_CAPACITY_CONCURRENCY', '4')
    def receive(request):
        assert request.url.path.startswith('/__sentinel_capacity_probe__/')
        headers = {'X-SL-Gateway-Processing-Ms': '1.25', 'X-SL-Gateway-Degraded': 'false',
                   'X-SL-Policy-Version': f'{POLICY_ID}:3'}
        if fault == 'missing': headers.pop('X-SL-Gateway-Processing-Ms')
        if fault == 'nonfinite': headers['X-SL-Gateway-Processing-Ms'] = 'nan'
        if fault == 'degraded': headers['X-SL-Gateway-Degraded'] = 'true'
        if fault == 'policy': headers['X-SL-Policy-Version'] = 'wrong:3'
        return httpx.Response(503 if fault == 'http' else 200, headers=headers, text='<html>test</html>')
    with httpx.Client(base_url='https://pilot.example.test', transport=httpx.MockTransport(receive)) as client:
        evidence = capacity_probe(client, 3)
    assert evidence['attempts'] == 100
    assert evidence['processing_gate_pass'] is (fault is None)
    if fault in {'missing', 'nonfinite'}:
        assert evidence['processing_samples'] == 0
        assert evidence['processing_p95_ms'] is None
