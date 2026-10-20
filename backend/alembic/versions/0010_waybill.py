"""waybill: driver and vehicle on delivery notes, company details

Revision ID: 0010
Revises: 0009
"""
from alembic import op
import sqlalchemy as sa


revision = '0010'
down_revision = '0009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('invoices', schema=None) as batch_op:
        batch_op.add_column(sa.Column('driver', sa.String(length=120), server_default='', nullable=False))
        batch_op.add_column(sa.Column('vehicle', sa.String(length=30), server_default='', nullable=False))
    op.create_table('company',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=160), server_default='', nullable=False),
    sa.Column('address', sa.String(length=240), server_default='', nullable=False),
    sa.Column('postcode', sa.String(length=20), server_default='', nullable=False),
    sa.Column('okonh', sa.String(length=30), server_default='', nullable=False),
    sa.Column('account', sa.String(length=40), server_default='', nullable=False),
    sa.Column('bank', sa.String(length=200), server_default='', nullable=False),
    sa.Column('mfo', sa.String(length=20), server_default='', nullable=False),
    sa.Column('inn', sa.String(length=20), server_default='', nullable=False),
    sa.Column('phone', sa.String(length=60), server_default='', nullable=False),
    sa.Column('receive_note', sa.Text(), server_default='', nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_company'))
    )


def downgrade() -> None:
    op.drop_table('company')
    with op.batch_alter_table('invoices', schema=None) as batch_op:
        batch_op.drop_column('vehicle')
        batch_op.drop_column('driver')
