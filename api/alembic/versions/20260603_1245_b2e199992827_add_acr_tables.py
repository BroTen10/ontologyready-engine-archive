"""add_acr_tables

Revision ID: b2e199992827
Revises: c3a3c8752274
Create Date: 2026-06-03 12:45:18.471427+00:00

Add ACR (Access Control Rules) tables:
acr_rules, acr_groups, acr_bindings for row-level and attribute-level security.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'b2e199992827'
down_revision: Union[str, Sequence[str], None] = 'c3a3c8752274'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE acr_rules (
            id              SERIAL PRIMARY KEY,
            rule_name       VARCHAR(200) NOT NULL UNIQUE,
            description     TEXT DEFAULT '',
            conditions      JSONB NOT NULL DEFAULT '{}',
            permissions     JSONB NOT NULL DEFAULT '{}',
            priority        INTEGER DEFAULT 0,
            is_active       BOOLEAN DEFAULT TRUE,
            created_at      TIMESTAMPTZ DEFAULT now(),
            updated_at      TIMESTAMPTZ DEFAULT now()
        )
    """)
    op.create_index("idx_acr_rules_priority", "acr_rules", ["priority"])

    op.execute("""
        CREATE TABLE acr_groups (
            id              SERIAL PRIMARY KEY,
            group_name      VARCHAR(200) NOT NULL UNIQUE,
            description     TEXT DEFAULT '',
            rules           INTEGER[] DEFAULT '{}',
            is_active       BOOLEAN DEFAULT TRUE,
            created_at      TIMESTAMPTZ DEFAULT now(),
            updated_at      TIMESTAMPTZ DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE acr_bindings (
            id              SERIAL PRIMARY KEY,
            user_id         VARCHAR(200) NOT NULL,
            group_id        INTEGER REFERENCES acr_groups(id) ON DELETE CASCADE,
            target_type     VARCHAR(20) DEFAULT '*',
            target_id       VARCHAR(200) DEFAULT '*',
            created_at      TIMESTAMPTZ DEFAULT now()
        )
    """)
    op.create_index("idx_acr_bindings_user", "acr_bindings", ["user_id", "group_id"])


def downgrade() -> None:
    op.drop_table("acr_bindings")
    op.drop_table("acr_groups")
    op.drop_table("acr_rules")
