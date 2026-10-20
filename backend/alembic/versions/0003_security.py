"""two-factor sign-in and server-side sessions

Revision ID: 0003
Revises: 0002
"""
from alembic import op
import sqlalchemy as sa

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('users') as b:
        b.add_column(sa.Column('totp_secret', sa.String(length=255), nullable=True))
        b.add_column(sa.Column('totp_enabled', sa.Boolean(), server_default=sa.false(), nullable=False))
        b.add_column(sa.Column('totp_last_step', sa.Integer(), server_default='0', nullable=False))
    op.create_table('user_sessions',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('last_seen', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('ip', sa.String(length=64), nullable=False, server_default=''),
        sa.Column('agent', sa.String(length=200), nullable=False, server_default=''),
        sa.Column('revoked', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'))
    op.create_index('ix_user_sessions_user_id', 'user_sessions', ['user_id'])


def downgrade() -> None:
    op.drop_table('user_sessions')
    with op.batch_alter_table('users') as b:
        b.drop_column('totp_last_step')
        b.drop_column('totp_enabled')
        b.drop_column('totp_secret')
