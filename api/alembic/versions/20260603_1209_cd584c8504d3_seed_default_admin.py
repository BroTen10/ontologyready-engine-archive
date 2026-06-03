"""seed_default_admin

Revision ID: cd584c8504d3
Revises: b316b7088674
Create Date: 2026-06-03 12:09:13.140535+00:00

Seed a default admin user (admin / admin123) for initial JWT login.
"""
from typing import Sequence, Union

from alembic import op
from passlib.context import CryptContext


revision: str = 'cd584c8504d3'
down_revision: Union[str, Sequence[str], None] = 'b316b7088674'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ADMIN_ID = "00000000-0000-0000-0000-000000000001"


def upgrade() -> None:
    pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed = pwd.hash("admin123")
    op.execute(
        f"""
        INSERT INTO users (id, username, email, hashed_password, full_name, is_active, is_superuser)
        VALUES ('{ADMIN_ID}', 'admin', 'admin@ontologyready.local', '{hashed}', 'Administrator', TRUE, TRUE)
        ON CONFLICT (username) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute(f"DELETE FROM users WHERE id = '{ADMIN_ID}'")
