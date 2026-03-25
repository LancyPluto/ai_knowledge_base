"""initial

Revision ID: 20260325_01
Revises:
Create Date: 2026-03-25
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision = "20260325_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("username", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", mysql.DATETIME(fsp=6), nullable=True),
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_user_username", "user", ["username"], unique=True)

    op.create_table(
        "document",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default=sa.text("'PENDING'")),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column("updated_at", mysql.DATETIME(fsp=6), nullable=True),
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_document_filename", "document", ["filename"], unique=False)
    op.create_index("ix_document_user_id", "document", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_document_user_id", table_name="document")
    op.drop_index("ix_document_filename", table_name="document")
    op.drop_table("document")

    op.drop_index("ix_user_username", table_name="user")
    op.drop_table("user")
