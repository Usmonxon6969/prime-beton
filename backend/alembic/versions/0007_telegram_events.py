"""telegram event messages and daily summary

Revision ID: 0007
Revises: 0006
"""
from alembic import op
import sqlalchemy as sa


revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('telegram_cursors',
    sa.Column('kind', sa.String(length=20), nullable=False),
    sa.Column('last_id', sa.BigInteger(), nullable=False),
    sa.PrimaryKeyConstraint('kind', name=op.f('pk_telegram_cursors'))
    )
    with op.batch_alter_table('telegram_links', schema=None) as batch_op:
        batch_op.add_column(sa.Column('topics', sa.String(length=120), server_default='orders,ship,pay,prod,digest', nullable=False))


def downgrade() -> None:
    with op.batch_alter_table('telegram_links', schema=None) as batch_op:
        batch_op.drop_column('topics')
    op.drop_table('telegram_cursors')
