"""telegram bot

Revision ID: 0006
Revises: 0005
"""
from alembic import op
import sqlalchemy as sa


revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('telegram_codes',
    sa.Column('code_hash', sa.String(length=64), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('expires_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_telegram_codes_user_id_users')),
    sa.PrimaryKeyConstraint('code_hash', name=op.f('pk_telegram_codes'))
    )
    with op.batch_alter_table('telegram_codes', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_telegram_codes_user_id'), ['user_id'], unique=False)

    op.create_table('telegram_links',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('chat_id', sa.BigInteger(), nullable=False),
    sa.Column('lang', sa.String(length=2), nullable=False),
    sa.Column('notify', sa.Boolean(), nullable=False),
    sa.Column('linked_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_telegram_links_user_id_users')),
    sa.PrimaryKeyConstraint('user_id', name=op.f('pk_telegram_links')),
    sa.UniqueConstraint('chat_id', name=op.f('uq_telegram_links_chat_id'))
    )
    op.create_table('telegram_sent',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('key', sa.String(length=100), nullable=False),
    sa.Column('sent_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_telegram_sent_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_telegram_sent')),
    sa.UniqueConstraint('user_id', 'key', name='uq_telegram_sent_user_key')
    )
    with op.batch_alter_table('telegram_sent', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_telegram_sent_sent_at'), ['sent_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_telegram_sent_user_id'), ['user_id'], unique=False)



def downgrade() -> None:
    with op.batch_alter_table('telegram_sent', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_telegram_sent_user_id'))
        batch_op.drop_index(batch_op.f('ix_telegram_sent_sent_at'))

    op.drop_table('telegram_sent')
    op.drop_table('telegram_links')
    with op.batch_alter_table('telegram_codes', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_telegram_codes_user_id'))

    op.drop_table('telegram_codes')
