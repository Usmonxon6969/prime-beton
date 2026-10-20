"""premium features: switched on by the main administrator for a period and a number of uses

Revision ID: 0014
Revises: 0013
"""
from alembic import op
import sqlalchemy as sa


revision = '0014'
down_revision = '0013'
branch_labels = None
depends_on = None


def upgrade() -> None:
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
    op.drop_index('ix_premium_grants_user_id', table_name='premium_grants')
    op.drop_table('premium_grants')
