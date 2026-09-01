"""create_revival_teams_and_members_tables

Revision ID: 2a94f1c7e802
Revises: 1812c1061204
Create Date: 2026-09-01 19:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2a94f1c7e802'
down_revision: Union[str, Sequence[str], None] = '1812c1061204'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'revival_teams',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('repository_id', sa.Integer(), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_revival_teams_owner_id'), 'revival_teams', ['owner_id'], unique=False)
    op.create_index(op.f('ix_revival_teams_repository_id'), 'revival_teams', ['repository_id'], unique=True)

    op.create_table(
        'revival_team_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['team_id'], ['revival_teams.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('team_id', 'user_id', name='uq_revival_team_members_team_user'),
    )
    op.create_index(op.f('ix_revival_team_members_team_id'), 'revival_team_members', ['team_id'], unique=False)
    op.create_index(op.f('ix_revival_team_members_user_id'), 'revival_team_members', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_revival_team_members_user_id'), table_name='revival_team_members')
    op.drop_index(op.f('ix_revival_team_members_team_id'), table_name='revival_team_members')
    op.drop_table('revival_team_members')
    op.drop_index(op.f('ix_revival_teams_repository_id'), table_name='revival_teams')
    op.drop_index(op.f('ix_revival_teams_owner_id'), table_name='revival_teams')
    op.drop_table('revival_teams')
