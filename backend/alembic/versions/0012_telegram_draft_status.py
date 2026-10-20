"""telegram: production lists can wait for the manager's approval

Revision ID: 0012
Revises: 0011
"""
from alembic import op
import sqlalchemy as sa


revision = '0012'
down_revision = '0011'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('telegram_drafts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', sa.String(length=10), server_default='draft', nullable=False))


def downgrade() -> None:
    with op.batch_alter_table('telegram_drafts', schema=None) as batch_op:
        batch_op.drop_column('status')
