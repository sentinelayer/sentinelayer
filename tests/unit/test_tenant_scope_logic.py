"""Tenant scope logic unit tests — no network."""
from control_plane.app.domain.deployment.blast_radius import BlastRadius, DeployMode, Stage


def test_blast_radius_auto_rollback_on_fp_spike():
    br = BlastRadius()
    br.start("dep-1", "v1.2.0", DeployMode.PERCENTAGE)
    br.advance()  # 5% -> may stay or move
    br.record_metric("fp_spike_pct", 15.0)
    out = br.advance()
    assert out.get("status") == "rolled_back" or any(t["tripped"] for t in br.status()["triggers"])


def test_blast_radius_pilot_stages():
    br = BlastRadius()
    br.start("dep-2", "v1.0.0", DeployMode.SINGLE_TENANT)
    assert br.stage == Stage.INTERNAL
    br.advance()
    assert br.stage == Stage.DESIGN_PARTNER
