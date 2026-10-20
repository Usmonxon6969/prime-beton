"""telegram: production lists waiting for confirmation

Revision ID: 0011
Revises: 0010
"""
from alembic import op
import sqlalchemy as sa


revision = '0011'
down_revision = '0010'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('telegram_drafts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('chat_id', sa.BigInteger(), nullable=False),
    sa.Column('payload', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'))
    op.create_index(op.f('ix_telegram_drafts_user_id'), 'telegram_drafts', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_telegram_drafts_user_id'), table_name='telegram_drafts')
    op.drop_table('telegram_drafts')
