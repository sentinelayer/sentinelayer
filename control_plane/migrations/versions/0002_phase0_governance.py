"""Phase 0 governance — expand evidence + add requirements table

Revision ID: 0002
Revises: 0001
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    # Expand evidence table
    op.add_column("evidence", sa.Column("artifact_type", sa.String(32), server_default="file"))
    op.add_column("evidence", sa.Column("hash_sha256", sa.String(64), nullable=True))
    op.add_column("evidence", sa.Column("previous_hash", sa.String(64), nullable=True))
    op.add_column("evidence", sa.Column("owner", sa.String(128), nullable=True))
    op.add_column("evidence", sa.Column("reviewer", sa.String(128), nullable=True))
    op.add_column("evidence", sa.Column("implementation_version", sa.String(64), nullable=True))
    op.add_column("evidence", sa.Column("current_system_version", sa.String(64), nullable=True))
    op.add_column("evidence", sa.Column("runtime_artifact_hash", sa.String(64), nullable=True))
    op.add_column("evidence", sa.Column("approved_manifest_hash", sa.String(64), nullable=True))
    op.add_column("evidence", sa.Column("retention_days", sa.String(16), server_default="2555"))
    op.add_column("evidence", sa.Column("valid_from", sa.DateTime(), nullable=True))
    op.add_column("evidence", sa.Column("valid_until", sa.DateTime(), nullable=True))
    op.add_column("evidence", sa.Column("relationship", sa.String(64), nullable=True))
    op.add_column("evidence", sa.Column("related_id", sa.String(64), nullable=True))
    op.add_column("evidence", sa.Column("verified_at", sa.DateTime(), nullable=True))
    op.add_column("evidence", sa.Column("validated_at", sa.DateTime(), nullable=True))
    op.add_column("evidence", sa.Column("expired_at", sa.DateTime(), nullable=True))
    op.add_column("evidence", sa.Column("revoked_at", sa.DateTime(), nullable=True))
    op.add_column("evidence", sa.Column("revoked_reason", sa.Text(), nullable=True))
    op.add_column("evidence", sa.Column("chain_of_custody", sa.Text(), server_default="[]"))

    # Alter artifact to Text
    op.alter_column("evidence", "artifact", type_=sa.Text(), existing_type=sa.String())

    # Create requirements table
    op.create_table(
        "requirements",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("owner", sa.String(128), nullable=False),
        sa.Column("dependency", sa.Text(), server_default="[]"),
        sa.Column("requirement", sa.Text(), nullable=False),
        sa.Column("acceptance_criteria", sa.Text(), server_default="[]"),
        sa.Column("security_impact", sa.Text(), server_default=""),
        sa.Column("test_method", sa.String(256), server_default=""),
        sa.Column("failure_behavior", sa.String(256), server_default=""),
        sa.Column("rollback_strategy", sa.Text(), server_default=""),
        sa.Column("evidence_ids", sa.Text(), server_default="[]"),
        sa.Column("reviewer", sa.String(128), server_default=""),
        sa.Column("criticality", sa.String(8), server_default="P1"),
        sa.Column("gate", sa.String(32), server_default="MVP"),
        sa.Column("status", sa.String(16), server_default="NOT_STARTED"),
        sa.Column("implementation_version", sa.String(64), server_default=""),
        sa.Column("implementation_pass", sa.Boolean(), server_default="false"),
        sa.Column("automated_test_pass", sa.Boolean(), server_default="false"),
        sa.Column("security_test_pass", sa.Boolean(), server_default="false"),
        sa.Column("evidence_valid", sa.Boolean(), server_default="false"),
        sa.Column("independent_reviewer_valid", sa.Boolean(), server_default="false"),
        sa.Column("residual_risk_accepted", sa.Boolean(), server_default="false"),
        sa.Column("dependency_check_pass", sa.Boolean(), server_default="false"),
        sa.Column("rollback_test_pass", sa.Boolean(), server_default="false"),
        sa.Column("drift_detected", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )


def downgrade():
    op.drop_table("requirements")
    # Note: dropping columns is destructive; keep simple for now
