"""add_llm_configs

Revision ID: c4d5e6f7a8b9
Revises: b2e199992827
Create Date: 2026-06-03 13:00:00.000000+00:00

Add llm_configs table for multi-provider LLM integration management.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'c4d5e6f7a8b9'
down_revision: Union[str, Sequence[str], None] = 'b2e199992827'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE llm_configs (
            id              SERIAL PRIMARY KEY,
            provider        VARCHAR(50) NOT NULL,
            api_key         TEXT NOT NULL DEFAULT '',
            endpoint        TEXT DEFAULT '',
            model           VARCHAR(200) NOT NULL DEFAULT '',
            settings        JSONB NOT NULL DEFAULT '{}',
            is_default      BOOLEAN DEFAULT FALSE,
            is_active       BOOLEAN DEFAULT TRUE,
            created_at      TIMESTAMPTZ DEFAULT now(),
            updated_at      TIMESTAMPTZ DEFAULT now()
        )
    """)
    op.create_index("idx_llm_configs_provider", "llm_configs", ["provider"])


def downgrade() -> None:
    op.drop_table("llm_configs")
