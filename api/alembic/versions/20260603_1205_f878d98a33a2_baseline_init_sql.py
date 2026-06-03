"""baseline_init_sql

Revision ID: f878d98a33a2
Revises:
Create Date: 2026-06-03 12:05:14.354717+00:00

Initial baseline: 4 core tables from init.sql
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'f878d98a33a2'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.execute("""
        CREATE TABLE ontology_types (
            api_name      VARCHAR(100) PRIMARY KEY,
            type          VARCHAR(20) NOT NULL CHECK (type IN ('OBJECT', 'LINK', 'ACTION')),
            display_name  VARCHAR(200) NOT NULL,
            description   TEXT NOT NULL,
            config        JSONB NOT NULL DEFAULT '{}',
            maturity      VARCHAR(20) DEFAULT 'DRAFT' CHECK (maturity IN ('DRAFT', 'ACTIVE', 'DEPRECATED')),
            created_at    TIMESTAMPTZ DEFAULT now(),
            updated_at    TIMESTAMPTZ DEFAULT now()
        )
    """)
    op.create_index("idx_types_type", "ontology_types", ["type"])
    op.create_index("idx_types_config", "ontology_types", ["config"], postgresql_using="gin")
    op.create_index("idx_types_maturity", "ontology_types", ["maturity"])

    op.execute("""
        CREATE TABLE ontology_objects (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            object_type     VARCHAR(100) NOT NULL REFERENCES ontology_types(api_name),
            external_id     VARCHAR(500),
            dataset_id      VARCHAR(100) NOT NULL DEFAULT 'default',
            display_name    TEXT GENERATED ALWAYS AS (properties ->> 'name') STORED,
            properties      JSONB NOT NULL DEFAULT '{}',
            embedding       VECTOR(384),
            created_at      TIMESTAMPTZ DEFAULT now(),
            updated_at      TIMESTAMPTZ DEFAULT now()
        )
    """)
    op.create_index("idx_objects_type", "ontology_objects", ["object_type"])
    op.create_index("idx_objects_eid", "ontology_objects", ["object_type", "external_id"])
    op.create_index("idx_objects_props", "ontology_objects", ["properties"], postgresql_using="gin")
    op.create_index("idx_objects_display", "ontology_objects", ["display_name"])
    op.create_index("idx_objects_dataset", "ontology_objects", ["dataset_id", "object_type"])

    op.execute("""
        CREATE TABLE ontology_links (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            link_type       VARCHAR(100) NOT NULL REFERENCES ontology_types(api_name),
            source_id       UUID NOT NULL REFERENCES ontology_objects(id) ON DELETE CASCADE,
            target_id       UUID NOT NULL REFERENCES ontology_objects(id) ON DELETE CASCADE,
            dataset_id      VARCHAR(100) NOT NULL DEFAULT 'default',
            properties      JSONB DEFAULT '{}',
            confidence      REAL DEFAULT 1.0 CHECK (confidence >= 0 AND confidence <= 1),
            created_at      TIMESTAMPTZ DEFAULT now()
        )
    """)
    op.create_index("idx_links_source", "ontology_links", ["source_id"])
    op.create_index("idx_links_target", "ontology_links", ["target_id"])
    op.create_index("idx_links_type", "ontology_links", ["link_type"])
    op.create_index("idx_links_props", "ontology_links", ["properties"], postgresql_using="gin")
    op.create_index("idx_links_source_type", "ontology_links", ["source_id", "link_type"])
    op.create_index("idx_links_target_type", "ontology_links", ["target_id", "link_type"])
    op.create_index("idx_links_dataset", "ontology_links", ["dataset_id", "link_type"])

    op.execute("""
        CREATE TABLE ontology_actions_log (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            action_type     VARCHAR(100) NOT NULL,
            parameters      JSONB NOT NULL,
            status          VARCHAR(20) NOT NULL CHECK (status IN ('SUCCESS', 'FAILED', 'PENDING')),
            error_message   TEXT,
            executed_by     VARCHAR(200) NOT NULL,
            before_snapshot JSONB,
            after_snapshot  JSONB,
            executed_at     TIMESTAMPTZ DEFAULT now()
        )
    """)
    op.create_index("idx_actions_log_type", "ontology_actions_log", ["action_type"])
    op.create_index("idx_actions_log_time", "ontology_actions_log", ["executed_at"])
    op.create_index("idx_actions_log_executor", "ontology_actions_log", ["executed_by"])
    op.create_index("idx_actions_log_params", "ontology_actions_log", ["parameters"], postgresql_using="gin")
    op.create_index("idx_actions_log_before", "ontology_actions_log", ["before_snapshot"], postgresql_using="gin")
    op.create_index("idx_actions_log_after", "ontology_actions_log", ["after_snapshot"], postgresql_using="gin")


def downgrade() -> None:
    op.drop_table("ontology_actions_log")
    op.drop_table("ontology_links")
    op.drop_table("ontology_objects")
    op.drop_table("ontology_types")
