"""premium_grants: make sure the table exists (an earlier draft of revision 0014 created a column on users instead)

Revision ID: 0015
Revises: 0014
"""
from alembic import op
import sqlalchemy as sa


revision = '0015'
down_revision = '0014'
branch_labels = None
depends_on = None


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())
    if insp.has_table('premium_grants'):
        return
    op.create_table(
        'premium_grants',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('feature', sa.String(length=32), nullable=False),
        sa.Column('granted_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('uses_limit', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('used', sa.String(length=400), nullable=False, server_default=''),
        sa.UniqueConstraint('user_id', 'feature'),
    )
    op.create_index('ix_premium_grants_user_id', 'premium_grants', ['user_id'])


def downgrade() -> None:
    pass
