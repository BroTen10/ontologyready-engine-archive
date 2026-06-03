"""add_doc_engine_and_oss_configs

Revision ID: f8a9b0c1d2e3
Revises: f7a8b9c0d1e2
Create Date: 2026-06-03 13:22:00.000000+00:00

Add doc_engine_config and oss_config tables.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'f8a9b0c1d2e3'
down_revision: Union[str, Sequence[str], None] = 'f7a8b9c0d1e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE doc_engine_config (
            id              SERIAL PRIMARY KEY,
            engine_type     VARCHAR(50) NOT NULL DEFAULT 'pgvector'
                            CHECK (engine_type IN ('pgvector', 'opensearch')),
            config          JSONB NOT NULL DEFAULT '{}',
            is_active       BOOLEAN DEFAULT TRUE,
            created_at      TIMESTAMPTZ DEFAULT now(),
            updated_at      TIMESTAMPTZ DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE oss_config (
            id              SERIAL PRIMARY KEY,
            provider        VARCHAR(50) NOT NULL DEFAULT 's3',
            endpoint        TEXT NOT NULL DEFAULT '',
            access_key      TEXT NOT NULL DEFAULT '',
            secret_key      TEXT NOT NULL DEFAULT '',
            bucket          VARCHAR(300) NOT NULL DEFAULT '',
            region          VARCHAR(100) DEFAULT 'us-east-1',
            is_active       BOOLEAN DEFAULT TRUE,
            created_at      TIMESTAMPTZ DEFAULT now(),
            updated_at      TIMESTAMPTZ DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE evaluation_datasets (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name            VARCHAR(300) NOT NULL,
            description     TEXT DEFAULT '',
            file_path       TEXT DEFAULT '',
            item_count      INTEGER DEFAULT 0,
            created_by      VARCHAR(200) DEFAULT '',
            created_at      TIMESTAMPTZ DEFAULT now(),
            updated_at      TIMESTAMPTZ DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE evaluation_runs (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            dataset_id      UUID REFERENCES evaluation_datasets(id) ON DELETE CASCADE,
            config          JSONB DEFAULT '{}',
            status          VARCHAR(20) DEFAULT 'PENDING'
                            CHECK (status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED')),
            metrics         JSONB DEFAULT '{}',
            created_by      VARCHAR(200) DEFAULT '',
            created_at      TIMESTAMPTZ DEFAULT now(),
            completed_at    TIMESTAMPTZ DEFAULT NULL
        )
    """)
    op.create_index("idx_eval_runs_dataset", "evaluation_runs", ["dataset_id"])
    op.create_index("idx_eval_runs_status", "evaluation_runs", ["status"])


def downgrade() -> None:
    op.drop_table("evaluation_runs")
    op.drop_table("evaluation_datasets")
    op.drop_table("oss_config")
    op.drop_table("doc_engine_config")
