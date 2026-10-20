"""telegram: summary hour per person and quiet night mode

Revision ID: 0008
Revises: 0007
"""
from alembic import op
import sqlalchemy as sa


revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('telegram_links', schema=None) as batch_op:
        batch_op.add_column(sa.Column('digest_hour', sa.Integer(), server_default='18', nullable=False))
        batch_op.add_column(sa.Column('digest_day', sa.Integer(), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('quiet', sa.Boolean(), server_default=sa.false(), nullable=False))


def downgrade() -> None:
    with op.batch_alter_table('telegram_links', schema=None) as batch_op:
        batch_op.drop_column('quiet')
        batch_op.drop_column('digest_day')
        batch_op.drop_column('digest_hour')
