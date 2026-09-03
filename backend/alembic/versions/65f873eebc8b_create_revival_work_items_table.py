"""create_revival_work_items_table

Revision ID: 65f873eebc8b
Revises: 2a94f1c7e802
Create Date: 2026-09-03 16:06:47.271680

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '65f873eebc8b'
down_revision: Union[str, Sequence[str], None] = '2a94f1c7e802'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'revival_work_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('assignee_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['assignee_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['team_id'], ['revival_teams.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("status IN ('todo', 'in_progress', 'completed')", name='ck_revival_work_items_status'),
    )
    op.create_index(op.f('ix_revival_work_items_assignee_id'), 'revival_work_items', ['assignee_id'], unique=False)
    op.create_index(op.f('ix_revival_work_items_team_id'), 'revival_work_items', ['team_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_revival_work_items_team_id'), table_name='revival_work_items')
    op.drop_index(op.f('ix_revival_work_items_assignee_id'), table_name='revival_work_items')
    op.drop_table('revival_work_items')
