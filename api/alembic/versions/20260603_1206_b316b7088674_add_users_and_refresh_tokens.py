"""add_users_and_refresh_tokens

Revision ID: b316b7088674
Revises: f878d98a33a2
Create Date: 2026-06-03 12:06:43.681755+00:00

Add users and refresh_tokens tables for JWT authentication.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'b316b7088674'
down_revision: Union[str, Sequence[str], None] = 'f878d98a33a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE users (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            username        VARCHAR(100) NOT NULL UNIQUE,
            email           VARCHAR(255) NOT NULL UNIQUE,
            hashed_password VARCHAR(255) NOT NULL,
            full_name       VARCHAR(200) NOT NULL DEFAULT '',
            is_active       BOOLEAN NOT NULL DEFAULT TRUE,
            is_superuser    BOOLEAN NOT NULL DEFAULT FALSE,
            created_at      TIMESTAMPTZ DEFAULT now(),
            updated_at      TIMESTAMPTZ DEFAULT now()
        )
    """)
    op.create_index("idx_users_username", "users", ["username"])
    op.create_index("idx_users_email", "users", ["email"])

    op.execute("""
        CREATE TABLE refresh_tokens (
            id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            token        VARCHAR(512) NOT NULL UNIQUE,
            user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            expires_at   TIMESTAMPTZ NOT NULL,
            created_at   TIMESTAMPTZ DEFAULT now()
        )
    """)
    op.create_index("idx_refresh_tokens_token", "refresh_tokens", ["token"])
    op.create_index("idx_refresh_tokens_user", "refresh_tokens", ["user_id"])


def downgrade() -> None:
    op.drop_table("refresh_tokens")
    op.drop_table("users")
