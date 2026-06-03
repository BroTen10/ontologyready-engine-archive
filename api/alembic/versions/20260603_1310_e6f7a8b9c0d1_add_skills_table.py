"""add_skills_table

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-06-03 13:10:00.000000+00:00

Add skills table for AI-generated skill management.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'e6f7a8b9c0d1'
down_revision: Union[str, Sequence[str], None] = 'd5e6f7a8b9c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE skills (
            id              SERIAL PRIMARY KEY,
            name            VARCHAR(300) NOT NULL,
            description     TEXT DEFAULT '',
            skill_config    JSONB NOT NULL DEFAULT '{}',
            status          VARCHAR(20) DEFAULT 'active'
                            CHECK (status IN ('active', 'inactive', 'draft')),
            is_preset       BOOLEAN DEFAULT FALSE,
            category        VARCHAR(100) DEFAULT 'custom',
            created_by      VARCHAR(200) DEFAULT '',
            created_at      TIMESTAMPTZ DEFAULT now(),
            updated_at      TIMESTAMPTZ DEFAULT now()
        )
    """)
    op.create_index("idx_skills_status", "skills", ["status"])
    op.create_index("idx_skills_category", "skills", ["category"])


def downgrade() -> None:
    op.drop_table("skills")
