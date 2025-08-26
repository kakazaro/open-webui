"""add_chat_id_to_feedback

Revision ID: 790ecce592df
Revises: 3781e22d8b01
Create Date: 2025-01-08 15:13:16.063379

"""
from typing import Sequence, Union

from sqlalchemy.engine.reflection import Inspector
from alembic import op
import sqlalchemy as sa
import open_webui.internal.db

revision: str = '790ecce592df'
down_revision: Union[str, None] = '3781e22d8b01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    # Get list of columns in the 'feedback' table
    columns = [col['name'] for col in inspector.get_columns('feedback')]

    # Add chat_id column to feedback
    if 'chat_id' not in columns:
        op.add_column(
            "feedback",
            sa.Column("chat_id", sa.Text(), nullable=True),
        )


def downgrade():
    op.drop_column("feedback", "chat_id")