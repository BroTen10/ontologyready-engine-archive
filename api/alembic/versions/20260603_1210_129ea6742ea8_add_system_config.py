"""add_system_config

Revision ID: 129ea6742ea8
Revises: cd584c8504d3
Create Date: 2026-06-03 12:10:43.164872+00:00

Add system_config table and seed default configuration values.
"""
from typing import Sequence, Union

from alembic import op


revision: str = '129ea6742ea8'
down_revision: Union[str, Sequence[str], None] = 'cd584c8504d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


DEFAULTS = [
    ("system.name", "OntologyReady", "System display name"),
    ("system.version", "0.2.0", "Current system version"),
    ("system.logo_url", "", "Logo URL shown in console header"),
    ("system.description", "Enterprise Ontology Management Platform", "System description"),
]


def upgrade() -> None:
    op.execute("""
        CREATE TABLE system_config (
            key         VARCHAR(200) PRIMARY KEY,
            value       TEXT NOT NULL DEFAULT '',
            description TEXT NOT NULL DEFAULT '',
            updated_at  TIMESTAMPTZ DEFAULT now()
        )
    """)
    for key, value, desc in DEFAULTS:
        op.execute(
            f"INSERT INTO system_config (key, value, description) "
            f"VALUES ('{key}', '{value}', '{desc}') "
            f"ON CONFLICT (key) DO NOTHING"
        )


def downgrade() -> None:
    op.drop_table("system_config")
