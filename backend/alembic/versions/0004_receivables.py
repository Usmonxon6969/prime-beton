"""payment terms, pay-by dates and advances against orders

Revision ID: 0004
Revises: 0003
"""
from alembic import op
import sqlalchemy as sa

revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('customers') as b:
        b.add_column(sa.Column('pay_days', sa.Integer(), server_default='0', nullable=False))
    with op.batch_alter_table('invoices') as b:
        b.add_column(sa.Column('pay_due', sa.DateTime(), nullable=True))
        b.create_index('ix_invoices_pay_due', ['pay_due'])
    with op.batch_alter_table('fin_docs') as b:
        b.add_column(sa.Column('order_id', sa.Integer(), nullable=True))
        b.create_foreign_key('fk_fin_docs_order_id_orders', 'orders', ['order_id'], ['id'])
        b.create_index('ix_fin_docs_order_id', ['order_id'])


def downgrade() -> None:
    with op.batch_alter_table('fin_docs') as b:
        b.drop_index('ix_fin_docs_order_id')
        b.drop_constraint('fk_fin_docs_order_id_orders', type_='foreignkey')
        b.drop_column('order_id')
    with op.batch_alter_table('invoices') as b:
        b.drop_index('ix_invoices_pay_due')
        b.drop_column('pay_due')
    with op.batch_alter_table('customers') as b:
        b.drop_column('pay_days')
