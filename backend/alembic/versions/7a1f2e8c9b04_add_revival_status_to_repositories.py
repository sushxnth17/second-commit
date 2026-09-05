"""add_revival_status_to_repositories

Revision ID: 7a1f2e8c9b04
Revises: 65f873eebc8b
Create Date: 2026-09-05 20:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a1f2e8c9b04'
down_revision: Union[str, Sequence[str], None] = '65f873eebc8b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('repositories') as batch_op:
        batch_op.add_column(
            sa.Column(
                'revival_status',
                sa.String(length=50),
                server_default='seeking_revival',
                nullable=False,
            )
        )
        batch_op.create_check_constraint(
            'ck_repositories_revival_status',
            "revival_status IN ('seeking_revival', 'forming_team', 'revival_in_progress', 'revived', 'paused', 'archived')",
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('repositories') as batch_op:
        batch_op.drop_constraint('ck_repositories_revival_status', type_='check')
        batch_op.drop_column('revival_status')
