"""users: the main administrator account (hidden from, and untouchable by, the other users)

Revision ID: 0013
Revises: 0012
"""
from alembic import op
import sqlalchemy as sa


revision = '0013'
down_revision = '0012'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_owner', sa.Boolean(), server_default='0', nullable=False))
    # the first administrator ever created is the main one
    # a bound boolean works on SQLite and on PostgreSQL (PostgreSQL refuses «is_owner = 1» for a boolean column)
    op.get_bind().execute(sa.text("UPDATE users SET is_owner = :yes WHERE id = (SELECT MIN(id) FROM users WHERE role = 'admin')"), {"yes": True})


def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('is_owner')
