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


def test_series_preserves_failed_round(monkeypatch):
    from scripts import verify_pilot
    monkeypatch.setenv('PILOT_CAPACITY_ROUNDS', '2')
    monkeypatch.setenv('PILOT_CAPACITY_REQUESTS', '100')
    reports = iter([
        dict(attempts=100, failures=0, degraded_responses=1, policy_mismatches=0,
             processing_p95_ms=5, processing_gate_pass=False),
        dict(attempts=100, failures=0, degraded_responses=0, policy_mismatches=0,
             processing_p95_ms=4, processing_gate_pass=True),
    ])
    monkeypatch.setattr(verify_pilot, 'capacity_probe', lambda *_: next(reports))
    evidence = verify_pilot.capacity_series(None, 3)
    assert evidence['attempts'] == 200
    assert evidence['degraded_responses'] == 1
    assert evidence['round_processing_p95_ms'] == [5, 4]
    assert not evidence['series_gate_pass']


@pytest.mark.parametrize('rounds', ['0', '21'])
def test_series_rejects_unbounded_budget(monkeypatch, rounds):
    from scripts.verify_pilot import capacity_series
    monkeypatch.setenv('PILOT_CAPACITY_ROUNDS', rounds)
    with pytest.raises(ValueError):
        capacity_series(None, 3)


def test_owner_session_revoked_when_alert_inspection_fails(monkeypatch):
    from scripts import verify_pilot
    monkeypatch.setenv('SL_PILOT_VERIFY', '1')
    monkeypatch.setenv('PILOT_BASE_URL', 'https://sentinelayer-production-b882.up.railway.app')
    monkeypatch.setenv('PILOT_ADMIN_EMAIL', 'test@example.test')
    monkeypatch.setenv('PILOT_ADMIN_PASSWORD', 'test-password')
    monkeypatch.setenv('PILOT_ADMIN_MFA_SECRET', 'JBSWY3DPEHPK3PXP')
    calls = []
    def receive(request):
        calls.append(request.url.path)
        if request.url.path.endswith('/login'):
            data = __import__('json').loads(request.content)
            return httpx.Response(200, json={'access_token': 'test-token'} if 'mfa_code' in data else {'mfa_required': True})
        if request.url.path.endswith('/me'):
            return httpx.Response(200, json=dict(is_admin=True, mfa_enabled=True, tenant_id='sentinel-pilot'))
        if request.url.path.endswith('/logout'):
            return httpx.Response(200, json={'logged_out': True})
        return httpx.Response(503, json={'error': 'unavailable'})
    real_client = httpx.Client
    monkeypatch.setattr(verify_pilot.httpx, 'Client', lambda **kwargs: real_client(**kwargs, transport=httpx.MockTransport(receive)))
    with pytest.raises(RuntimeError):
        verify_pilot.main()
    assert calls[-1] == '/api/v1/auth/logout'
