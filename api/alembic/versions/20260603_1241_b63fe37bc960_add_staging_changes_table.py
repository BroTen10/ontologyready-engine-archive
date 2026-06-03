"""add_staging_changes_table

Revision ID: b63fe37bc960
Revises: 45bfb6be7812
Create Date: 2026-06-03 12:41:40.367026+00:00

Add staging_changes table for the staging workflow:
store / commit / discard / revert changes to ontology entities.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'b63fe37bc960'
down_revision: Union[str, Sequence[str], None] = '45bfb6be7812'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE staging_changes (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id         VARCHAR(200) NOT NULL DEFAULT 'system',
            target_type     VARCHAR(20) NOT NULL CHECK (target_type IN ('object', 'link', 'type')),
            target_id       UUID,
            target_api_name VARCHAR(100),
            change_type     VARCHAR(20) NOT NULL CHECK (change_type IN ('create', 'update', 'delete')),
            payload         JSONB NOT NULL DEFAULT '{}',
            previous_state  JSONB,
            status          VARCHAR(20) NOT NULL DEFAULT 'staged'
                            CHECK (status IN ('staged', 'committed', 'discarded')),
            created_at      TIMESTAMPTZ DEFAULT now(),
            updated_at      TIMESTAMPTZ DEFAULT now()
        )
    """)
    op.create_index("idx_staging_status", "staging_changes", ["status"])
    op.create_index("idx_staging_user", "staging_changes", ["user_id", "status"])
    op.create_index("idx_staging_target", "staging_changes", ["target_type", "target_id"])
    op.create_index("idx_staging_payload", "staging_changes", ["payload"], postgresql_using="gin")


def downgrade() -> None:
    op.drop_table("staging_changes")
