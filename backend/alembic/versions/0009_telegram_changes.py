"""telegram: edit and delete messages are on for everybody who already linked a chat

Revision ID: 0009
Revises: 0008
"""
from alembic import op


revision = '0009'
down_revision = '0008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE telegram_links SET topics = CASE WHEN topics = '' THEN 'edits,dels' ELSE topics || ',edits,dels' END WHERE topics NOT LIKE '%edits%' AND topics != ''")


def downgrade() -> None:
    pass
