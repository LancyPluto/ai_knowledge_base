"""email auth

Revision ID: 20260325_04
Revises: 5f9b627bcff8
Create Date: 2026-03-25
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision = "20260325_04"
down_revision = "5f9b627bcff8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("user", sa.Column("email", sa.String(length=255), nullable=True))
    op.create_index("ix_user_email", "user", ["email"], unique=True)

    op.create_table(
        "email_code",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("purpose", sa.String(length=32), nullable=False),
        sa.Column("expires_at", mysql.DATETIME(fsp=6), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_email_code_email", "email_code", ["email"], unique=False)
    op.create_index("ix_email_code_purpose", "email_code", ["purpose"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_email_code_purpose", table_name="email_code")
    op.drop_index("ix_email_code_email", table_name="email_code")
    op.drop_table("email_code")
    op.drop_index("ix_user_email", table_name="user")
    op.drop_column("user", "email")
