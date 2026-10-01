"""create scores table

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-02

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "scores",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("scored_by_id", sa.Uuid(), nullable=False),
        sa.Column("model_version_id", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("probability", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(length=10), nullable=False),
        sa.Column("cache_hit", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["model_version_id"], ["model_versions.id"]),
        sa.ForeignKeyConstraint(["scored_by_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scores_scored_by_created", "scores", ["scored_by_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_scores_scored_by_created", table_name="scores")
    op.drop_table("scores")
