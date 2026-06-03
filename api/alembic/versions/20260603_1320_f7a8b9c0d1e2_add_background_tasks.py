"""add_background_tasks

Revision ID: f7a8b9c0d1e2
Revises: e6f7a8b9c0d1
Create Date: 2026-06-03 13:20:00.000000+00:00

Add background_tasks table for async task management with status tracking.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'f7a8b9c0d1e2'
down_revision: Union[str, Sequence[str], None] = 'e6f7a8b9c0d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE background_tasks (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            task_type       VARCHAR(100) NOT NULL,
            status          VARCHAR(20) DEFAULT 'PENDING'
                            CHECK (status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELED')),
            progress        INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
            params          JSONB DEFAULT '{}',
            result          JSONB DEFAULT NULL,
            error           TEXT DEFAULT NULL,
            logs            TEXT DEFAULT '',
            created_by      VARCHAR(200) DEFAULT '',
            created_at      TIMESTAMPTZ DEFAULT now(),
            updated_at      TIMESTAMPTZ DEFAULT now(),
            completed_at    TIMESTAMPTZ DEFAULT NULL,
            cancelled_at    TIMESTAMPTZ DEFAULT NULL
        )
    """)
    op.create_index("idx_bg_tasks_status", "background_tasks", ["status"])
    op.create_index("idx_bg_tasks_type", "background_tasks", ["task_type"])
    op.create_index("idx_bg_tasks_created_at", "background_tasks", ["created_at"])


def downgrade() -> None:
    op.drop_table("background_tasks")
