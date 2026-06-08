"""add_airlines_and_airports_tables

Revision ID: f3e8b2c19a44
Revises: 9aa2c14988c3
Create Date: 2026-05-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3e8b2c19a44'
down_revision: Union[str, Sequence[str], None] = '9aa2c14988c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'airlines',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('logo_url', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_airlines')),
    )
    op.create_index(op.f('ix_airlines_id'), 'airlines', ['id'], unique=False)
    op.create_index(op.f('ix_airlines_code'), 'airlines', ['code'], unique=True)

    op.create_table(
        'airports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('city_name', sa.String(length=100), nullable=False),
        sa.Column('city_code', sa.String(length=10), nullable=False),
        sa.Column('country_code', sa.String(length=10), nullable=False),
        sa.Column('country_name', sa.String(length=100), nullable=False),
        sa.Column('airport_code', sa.String(length=10), nullable=False),
        sa.Column('airport_name', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_airports')),
    )
    op.create_index(op.f('ix_airports_id'), 'airports', ['id'], unique=False)
    op.create_index(op.f('ix_airports_city_code'), 'airports', ['city_code'], unique=False)
    op.create_index(op.f('ix_airports_airport_code'), 'airports', ['airport_code'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_airports_airport_code'), table_name='airports')
    op.drop_index(op.f('ix_airports_city_code'), table_name='airports')
    op.drop_index(op.f('ix_airports_id'), table_name='airports')
    op.drop_table('airports')
    op.drop_index(op.f('ix_airlines_code'), table_name='airlines')
    op.drop_index(op.f('ix_airlines_id'), table_name='airlines')
    op.drop_table('airlines')
