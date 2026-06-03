"""add_property_definitions_table

Revision ID: 45bfb6be7812
Revises: 129ea6742ea8
Create Date: 2026-06-03 12:34:03.992862+00:00

Add property_definitions table to store enhanced property schema definitions
with pg_type, constraints, and index fields.
"""
from typing import Sequence, Union

from alembic import op


revision: str = '45bfb6be7812'
down_revision: Union[str, Sequence[str], None] = '129ea6742ea8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE property_definitions (
            id              SERIAL PRIMARY KEY,
            type_api_name   VARCHAR(100) NOT NULL REFERENCES ontology_types(api_name) ON DELETE CASCADE,
            name            VARCHAR(200) NOT NULL,
            semantic_type   VARCHAR(50) NOT NULL DEFAULT 'string',
            pg_type         VARCHAR(100),
            constraints     JSONB DEFAULT '{}',
            index           BOOLEAN DEFAULT FALSE,
            required        BOOLEAN DEFAULT FALSE,
            description     TEXT DEFAULT '',
            sort_order      INTEGER DEFAULT 0,
            created_at      TIMESTAMPTZ DEFAULT now(),
            updated_at      TIMESTAMPTZ DEFAULT now(),
            UNIQUE (type_api_name, name)
        )
    """)
    op.create_index("idx_propdef_type", "property_definitions", ["type_api_name"])
    op.create_index("idx_propdef_constraints", "property_definitions", ["constraints"], postgresql_using="gin")

    # Data migration: backfill from config JSONB
    op.execute("""
        INSERT INTO property_definitions (type_api_name, name, semantic_type, required, description, sort_order)
        SELECT
            t.api_name,
            prop ->> 'name',
            COALESCE(prop ->> 'type', 'string'),
            COALESCE((prop ->> 'required')::boolean, false),
            COALESCE(prop ->> 'description', ''),
            idx
        FROM ontology_types t
        CROSS JOIN LATERAL jsonb_array_elements(t.config -> 'properties') WITH ORDINALITY AS p(prop, idx)
        WHERE t.config ? 'properties'
          AND jsonb_typeof(t.config -> 'properties') = 'array'
          AND NOT EXISTS (
              SELECT 1 FROM property_definitions pd
              WHERE pd.type_api_name = t.api_name AND pd.name = prop ->> 'name'
          )
    """)


def downgrade() -> None:
    op.drop_table("property_definitions")
