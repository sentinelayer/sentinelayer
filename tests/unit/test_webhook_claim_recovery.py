from datetime import UTC, datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from control_plane.app.infrastructure.db.models import Base, Tenant, WebhookRegistration, WebhookDelivery
from control_plane.app.workers import webhook_delivery as worker


def test_atomic_claim_crash_recovery_and_budget(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'claims.db'}")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)
    now = datetime.now(UTC)
    with sessions() as db:
        db.add(Tenant(id="claim-test", name="claim-test"))
        db.flush()
        db.add(WebhookRegistration(id="hook-test", tenant_id="claim-test", url="https://example.test/hook", secret_ciphertext="test", secret_hash="test-only-hash"))
        db.flush()
        db.add(WebhookDelivery(id="delivery-test", tenant_id="claim-test", webhook_id="hook-test", event_type="test", status="queued", attempt_count=0))
        db.commit()
    monkeypatch.setattr(worker, "MAX_ATTEMPTS", 2)
    with sessions() as first, sessions() as second:
        row1 = first.get(WebhookDelivery, "delivery-test")
        row2 = second.get(WebhookDelivery, "delivery-test")
        assert worker._claim(first, row1, now) == "claimed"
        assert worker._claim(second, row2, now) == "skipped"
        assert row1.attempt_count == 1
        # Simulate process death by leaving the claimed row without completion.
        assert worker._claim(second, row2, now + timedelta(seconds=61)) == "claimed"
        assert row2.attempt_count == 2
        assert worker._claim(first, row1, now + timedelta(seconds=122)) == "dead_letter"
    with sessions() as db:
        row = db.get(WebhookDelivery, "delivery-test")
        assert row.status == "dead_letter"
        assert row.attempt_count == 2
        assert row.next_attempt_at is None
    engine.dispose()
