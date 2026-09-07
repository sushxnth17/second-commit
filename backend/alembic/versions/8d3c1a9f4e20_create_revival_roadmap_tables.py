"""create_revival_roadmap_tables

Revision ID: 8d3c1a9f4e20
Revises: 7a1f2e8c9b04
Create Date: 2026-09-07 17:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8d3c1a9f4e20'
down_revision: Union[str, Sequence[str], None] = '7a1f2e8c9b04'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'revival_roadmap_phases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('position', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['team_id'], ['revival_teams.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_revival_roadmap_phases_team_id'),
        'revival_roadmap_phases',
        ['team_id'],
        unique=False,
    )

    op.create_table(
        'revival_roadmap_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('phase_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('position', sa.Integer(), server_default='0', nullable=False),
        sa.Column('status', sa.String(length=50), server_default='todo', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['phase_id'], ['revival_roadmap_phases.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            "status IN ('todo', 'in_progress', 'completed')",
            name='ck_revival_roadmap_tasks_status',
        ),
    )
    op.create_index(
        op.f('ix_revival_roadmap_tasks_phase_id'),
        'revival_roadmap_tasks',
        ['phase_id'],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_revival_roadmap_tasks_phase_id'), table_name='revival_roadmap_tasks')
    op.drop_table('revival_roadmap_tasks')
    op.drop_index(op.f('ix_revival_roadmap_phases_team_id'), table_name='revival_roadmap_phases')
    op.drop_table('revival_roadmap_phases')
