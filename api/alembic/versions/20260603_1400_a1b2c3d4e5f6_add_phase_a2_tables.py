"""add_phase_a2_tables

Revision ID: a1b2c3d4e5f6
Revises: f8a9b0c1d2e3
Create Date: 2026-06-03 14:00:00.000000+00:00

Phase A2 tables:
- datasets: real dataset registry
- roles: role definitions with permissions
- role_assignments: user-to-role mapping
- groups_table: user groups
- group_members: group membership
- api_keys: hashed API keys with permissions
- personal_access_tokens: user PAT management
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f8a9b0c1d2e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Datasets ──────────────────────────────────────────────
    op.execute("""
        CREATE TABLE datasets (
            id              VARCHAR(100) PRIMARY KEY,
            name            VARCHAR(300) NOT NULL,
            description     TEXT DEFAULT '',
            is_default      BOOLEAN DEFAULT FALSE,
            created_at      TIMESTAMPTZ DEFAULT now(),
            updated_at      TIMESTAMPTZ DEFAULT now()
        )
    """)

    # ── Roles ─────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE roles (
            id              SERIAL PRIMARY KEY,
            name            VARCHAR(200) NOT NULL UNIQUE,
            description     TEXT DEFAULT '',
            permissions     JSONB NOT NULL DEFAULT '[]',
            created_at      TIMESTAMPTZ DEFAULT now(),
            updated_at      TIMESTAMPTZ DEFAULT now()
        )
    """)

    # ── Role assignments ──────────────────────────────────────
    op.execute("""
        CREATE TABLE role_assignments (
            id              SERIAL PRIMARY KEY,
            user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            role_id         INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
            created_at      TIMESTAMPTZ DEFAULT now(),
            UNIQUE(user_id, role_id)
        )
    """)
    op.create_index("idx_role_assignments_user", "role_assignments", ["user_id"])

    # ── Groups ────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE groups_table (
            id              SERIAL PRIMARY KEY,
            name            VARCHAR(200) NOT NULL UNIQUE,
            description     TEXT DEFAULT '',
            created_at      TIMESTAMPTZ DEFAULT now(),
            updated_at      TIMESTAMPTZ DEFAULT now()
        )
    """)

    # ── Group members ─────────────────────────────────────────
    op.execute("""
        CREATE TABLE group_members (
            id              SERIAL PRIMARY KEY,
            group_id        INTEGER NOT NULL REFERENCES groups_table(id) ON DELETE CASCADE,
            user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at      TIMESTAMPTZ DEFAULT now(),
            UNIQUE(group_id, user_id)
        )
    """)
    op.create_index("idx_group_members_user", "group_members", ["user_id"])

    # ── API Keys ──────────────────────────────────────────────
    op.execute("""
        CREATE TABLE api_keys (
            id              SERIAL PRIMARY KEY,
            key_hash        VARCHAR(128) NOT NULL UNIQUE,
            key_prefix      VARCHAR(12) NOT NULL,
            name            VARCHAR(200) NOT NULL,
            user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
            permissions     JSONB DEFAULT '["api"]',
            expires_at      TIMESTAMPTZ DEFAULT NULL,
            is_active       BOOLEAN DEFAULT TRUE,
            last_used_at    TIMESTAMPTZ DEFAULT NULL,
            created_at      TIMESTAMPTZ DEFAULT now()
        )
    """)
    op.create_index("idx_api_keys_user", "api_keys", ["user_id"])

    # ── Personal Access Tokens ────────────────────────────────
    op.execute("""
        CREATE TABLE personal_access_tokens (
            id              SERIAL PRIMARY KEY,
            token_hash      VARCHAR(128) NOT NULL UNIQUE,
            token_prefix    VARCHAR(12) NOT NULL,
            name            VARCHAR(200) NOT NULL,
            user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            scopes          JSONB DEFAULT '["api"]',
            expires_at      TIMESTAMPTZ DEFAULT NULL,
            is_active       BOOLEAN DEFAULT TRUE,
            last_used_at    TIMESTAMPTZ DEFAULT NULL,
            created_at      TIMESTAMPTZ DEFAULT now()
        )
    """)
    op.create_index("idx_pat_user", "personal_access_tokens", ["user_id"])

    # Seed default admin role
    op.execute("""
        INSERT INTO roles (name, description, permissions)
        VALUES ('admin', 'Super administrator with full access', '["*"]')
        ON CONFLICT (name) DO NOTHING
    """)
    op.execute("""
        INSERT INTO roles (name, description, permissions)
        VALUES ('editor', 'Can create and edit ontology data', '["types:read","types:write","objects:read","objects:write","links:read","links:write"]')
        ON CONFLICT (name) DO NOTHING
    """)
    op.execute("""
        INSERT INTO roles (name, description, permissions)
        VALUES ('viewer', 'Read-only access to ontology data', '["types:read","objects:read","links:read","graph:read"]')
        ON CONFLICT (name) DO NOTHING
    """)


def downgrade() -> None:
    op.drop_table("personal_access_tokens")
    op.drop_table("api_keys")
    op.drop_table("group_members")
    op.drop_table("groups_table")
    op.drop_table("role_assignments")
    op.drop_table("roles")
    op.drop_table("datasets")
