"""Add guest user support

Revision ID: 4b2c3e0e9a0b
Revises: 882b12d6159d
Create Date: 2025-11-19
"""

from alembic import op
import sqlalchemy as sa

revision = "4b2c3e0e9a0b"
down_revision = "882b12d6159d"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing_cols = {c["name"] for c in insp.get_columns("users")}

    if "is_guest" not in existing_cols:
        op.add_column(
            "users", sa.Column("is_guest", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        # Drop default only on dialects that support it (not SQLite)
        if bind.dialect.name != "sqlite":
            op.alter_column("users", "is_guest", server_default=None)
    else:
        # If column exists and we're on non-sqlite, attempt to drop default
        if bind.dialect.name != "sqlite":
            try:
                op.alter_column("users", "is_guest", server_default=None)
            except Exception:
                # Ignore if not supported or already dropped
                pass

    if "guest_expires_at" not in existing_cols:
        op.add_column("users", sa.Column("guest_expires_at", sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column("users", "guest_expires_at")
    op.drop_column("users", "is_guest")
