"""add_documents_table

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-06-03 13:05:00.000000+00:00

Add documents table for reference document upload and text extraction.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'd5e6f7a8b9c0'
down_revision: Union[str, Sequence[str], None] = 'c4d5e6f7a8b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE documents (
            id              SERIAL PRIMARY KEY,
            filename        VARCHAR(500) NOT NULL,
            original_name   VARCHAR(500) NOT NULL,
            content_type    VARCHAR(100) NOT NULL DEFAULT 'text/plain',
            file_size       BIGINT DEFAULT 0,
            file_path       TEXT NOT NULL,
            extracted_text  TEXT DEFAULT '',
            status          VARCHAR(20) DEFAULT 'UPLOADED'
                            CHECK (status IN ('UPLOADED', 'EXTRACTING', 'EXTRACTED', 'FAILED')),
            uploaded_by     VARCHAR(200) DEFAULT '',
            created_at      TIMESTAMPTZ DEFAULT now(),
            updated_at      TIMESTAMPTZ DEFAULT now()
        )
    """)
    op.create_index("idx_documents_status", "documents", ["status"])
    op.create_index("idx_documents_uploaded_by", "documents", ["uploaded_by"])


def downgrade() -> None:
    op.drop_table("documents")
