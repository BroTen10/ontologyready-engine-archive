"""add_ontology_versions_tables

Revision ID: c3a3c8752274
Revises: b63fe37bc960
Create Date: 2026-06-03 12:43:49.126395+00:00

Add ontology_versions and version_change_log tables for version management.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'c3a3c8752274'
down_revision: Union[str, Sequence[str], None] = 'b63fe37bc960'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE ontology_versions (
            id              SERIAL PRIMARY KEY,
            version_number  INTEGER NOT NULL,
            created_by      VARCHAR(200) NOT NULL DEFAULT 'system',
            snapshot_data   JSONB NOT NULL,
            comment         TEXT DEFAULT '',
            created_at      TIMESTAMPTZ DEFAULT now()
        )
    """)
    op.create_index("idx_versions_number", "ontology_versions", ["version_number"], unique=True)

    op.execute("""
        CREATE TABLE version_change_log (
            id              SERIAL PRIMARY KEY,
            version_id      INTEGER NOT NULL REFERENCES ontology_versions(id) ON DELETE CASCADE,
            entity_type     VARCHAR(20) NOT NULL CHECK (entity_type IN ('type', 'object', 'link')),
            entity_id       VARCHAR(200),
            change_summary  TEXT NOT NULL,
            created_at      TIMESTAMPTZ DEFAULT now()
        )
    """)
    op.create_index("idx_vcl_version", "version_change_log", ["version_id"])


def downgrade() -> None:
    op.drop_table("version_change_log")
    op.drop_table("ontology_versions")
