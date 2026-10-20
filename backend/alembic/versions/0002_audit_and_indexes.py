"""audit log and date indexes

Revision ID: 0002
Revises: 0001
"""
from alembic import op
import sqlalchemy as sa

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None

DATES = [('orders', 'ix_orders_date'), ('invoices', 'ix_invoices_date'), ('receipts', 'ix_receipts_date'),
         ('production_docs', 'ix_production_docs_date'), ('fin_docs', 'ix_fin_docs_date')]


def upgrade() -> None:
    op.create_table('audit_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('username', sa.String(length=64), nullable=False),
        sa.Column('action', sa.String(length=12), nullable=False),
        sa.Column('entity', sa.String(length=32), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('label', sa.String(length=160), nullable=False),
        sa.Column('changes', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_audit_log')))
    op.create_index('ix_audit_log_at', 'audit_log', ['at'])
    op.create_index('ix_audit_log_user_id', 'audit_log', ['user_id'])
    op.create_index('ix_audit_log_entity', 'audit_log', ['entity', 'entity_id'])
    for table, name in DATES:
        op.create_index(name, table, ['date'])


def downgrade() -> None:
    for table, name in DATES:
        op.drop_index(name, table_name=table)
    op.drop_index('ix_audit_log_entity', table_name='audit_log')
    op.drop_index('ix_audit_log_user_id', table_name='audit_log')
    op.drop_index('ix_audit_log_at', table_name='audit_log')
    op.drop_table('audit_log')
