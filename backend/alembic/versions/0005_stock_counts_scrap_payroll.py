"""stock counts, scrap, payroll

Revision ID: 0005
Revises: 0004
"""
from alembic import op
import sqlalchemy as sa


revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('workers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('position', sa.String(length=80), nullable=False),
    sa.Column('phone', sa.String(length=40), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_workers')),
    sa.UniqueConstraint('name', name=op.f('uq_workers_name'))
    )
    op.create_table('pay_adjusts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('worker_id', sa.Integer(), nullable=False),
    sa.Column('date', sa.DateTime(), nullable=False),
    sa.Column('amount', sa.Numeric(precision=18, scale=2), nullable=False),
    sa.Column('note', sa.Text(), nullable=False),
    sa.Column('status', sa.String(length=10), nullable=False),
    sa.ForeignKeyConstraint(['worker_id'], ['workers.id'], name=op.f('fk_pay_adjusts_worker_id_workers')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_pay_adjusts'))
    )
    with op.batch_alter_table('pay_adjusts', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_pay_adjusts_date'), ['date'], unique=False)
        batch_op.create_index(batch_op.f('ix_pay_adjusts_worker_id'), ['worker_id'], unique=False)

    op.create_table('stock_adjusts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('number', sa.String(length=24), nullable=False),
    sa.Column('date', sa.DateTime(), nullable=False),
    sa.Column('kind', sa.String(length=8), nullable=False),
    sa.Column('warehouse_id', sa.Integer(), nullable=False),
    sa.Column('reason', sa.String(length=12), nullable=False),
    sa.Column('comment', sa.Text(), nullable=False),
    sa.Column('status', sa.String(length=10), nullable=False),
    sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id'], name=op.f('fk_stock_adjusts_warehouse_id_warehouses')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_stock_adjusts')),
    sa.UniqueConstraint('number', name=op.f('uq_stock_adjusts_number'))
    )
    with op.batch_alter_table('stock_adjusts', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_stock_adjusts_date'), ['date'], unique=False)
        batch_op.create_index(batch_op.f('ix_stock_adjusts_warehouse_id'), ['warehouse_id'], unique=False)

    op.create_table('product_rates',
    sa.Column('item_id', sa.Integer(), nullable=False),
    sa.Column('rate', sa.Numeric(precision=18, scale=2), nullable=False),
    sa.ForeignKeyConstraint(['item_id'], ['items.id'], name=op.f('fk_product_rates_item_id_items')),
    sa.PrimaryKeyConstraint('item_id', name=op.f('pk_product_rates'))
    )
    op.create_table('production_crew',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('doc_id', sa.Integer(), nullable=False),
    sa.Column('worker_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['doc_id'], ['production_docs.id'], name=op.f('fk_production_crew_doc_id_production_docs')),
    sa.ForeignKeyConstraint(['worker_id'], ['workers.id'], name=op.f('fk_production_crew_worker_id_workers')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_production_crew'))
    )
    with op.batch_alter_table('production_crew', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_production_crew_doc_id'), ['doc_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_production_crew_worker_id'), ['worker_id'], unique=False)

    op.create_table('stock_adjust_rows',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('adjust_id', sa.Integer(), nullable=False),
    sa.Column('item_id', sa.Integer(), nullable=False),
    sa.Column('system_qty', sa.Numeric(precision=18, scale=3), nullable=False),
    sa.Column('qty', sa.Numeric(precision=18, scale=3), nullable=False),
    sa.Column('delta', sa.Numeric(precision=18, scale=3), nullable=False),
    sa.ForeignKeyConstraint(['adjust_id'], ['stock_adjusts.id'], name=op.f('fk_stock_adjust_rows_adjust_id_stock_adjusts')),
    sa.ForeignKeyConstraint(['item_id'], ['items.id'], name=op.f('fk_stock_adjust_rows_item_id_items')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_stock_adjust_rows'))
    )
    with op.batch_alter_table('stock_adjust_rows', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_stock_adjust_rows_adjust_id'), ['adjust_id'], unique=False)

    with op.batch_alter_table('fin_docs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('worker_id', sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f('ix_fin_docs_worker_id'), ['worker_id'], unique=False)
        batch_op.create_foreign_key(batch_op.f('fk_fin_docs_worker_id_workers'), 'workers', ['worker_id'], ['id'])

    with op.batch_alter_table('production_docs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('labour', sa.Numeric(precision=18, scale=2), server_default='0', nullable=False))

    with op.batch_alter_table('production_rows', schema=None) as batch_op:
        batch_op.add_column(sa.Column('scrap', sa.Numeric(precision=18, scale=3), server_default='0', nullable=False))



def downgrade() -> None:
    with op.batch_alter_table('production_rows', schema=None) as batch_op:
        batch_op.drop_column('scrap')

    with op.batch_alter_table('production_docs', schema=None) as batch_op:
        batch_op.drop_column('labour')

    with op.batch_alter_table('fin_docs', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('fk_fin_docs_worker_id_workers'), type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_fin_docs_worker_id'))
        batch_op.drop_column('worker_id')

    with op.batch_alter_table('stock_adjust_rows', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_stock_adjust_rows_adjust_id'))

    op.drop_table('stock_adjust_rows')
    with op.batch_alter_table('production_crew', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_production_crew_worker_id'))
        batch_op.drop_index(batch_op.f('ix_production_crew_doc_id'))

    op.drop_table('production_crew')
    op.drop_table('product_rates')
    with op.batch_alter_table('stock_adjusts', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_stock_adjusts_warehouse_id'))
        batch_op.drop_index(batch_op.f('ix_stock_adjusts_date'))

    op.drop_table('stock_adjusts')
    with op.batch_alter_table('pay_adjusts', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_pay_adjusts_worker_id'))
        batch_op.drop_index(batch_op.f('ix_pay_adjusts_date'))

    op.drop_table('pay_adjusts')
    op.drop_table('workers')
