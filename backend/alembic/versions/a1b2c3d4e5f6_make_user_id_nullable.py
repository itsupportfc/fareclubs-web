"""make user_id nullable for guest checkout

Revision ID: a1b2c3d4e5f6
Revises: 36d167450ae7
Create Date: 2026-03-09 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '36d167450ae7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('payments', 'user_id', nullable=True)
    op.alter_column('bookings', 'user_id', nullable=True)


def downgrade() -> None:
    op.alter_column('bookings', 'user_id', nullable=False)
    op.alter_column('payments', 'user_id', nullable=False)
