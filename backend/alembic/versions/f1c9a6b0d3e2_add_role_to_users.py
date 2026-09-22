"""add role to users

Revision ID: f1c9a6b0d3e2
Revises: 480b577e84bd
Create Date: 2026-09-28 00:00:00.000000

"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "f1c9a6b0d3e2"
down_revision: Union[str, None] = "480b577e84bd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "role",
            sa.String(length=20),
            nullable=False,
            server_default="specialist",
        ),
    )
    op.create_check_constraint(
        "ck_users_role", "users", "role IN ('admin', 'specialist')"
    )


def downgrade() -> None:
    op.drop_constraint("ck_users_role", "users", type_="check")
    op.drop_column("users", "role")
