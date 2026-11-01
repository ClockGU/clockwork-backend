"""add budget approved variable in the model of petition

Revision ID: 5154cba6ce5b
Revises: 4d00be87e03e
Create Date: 2025-05-22 21:07:37.020878

"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '5154cba6ce5b'
down_revision: Union[str, None] = '4d00be87e03e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add the column with a default value for existing rows
    op.add_column('petition', sa.Column('budget_approved', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    # Remove the default value after the column is added
    op.alter_column('petition', 'budget_approved', server_default=None)


def downgrade() -> None:
    # Drop the column
    op.drop_column('petition', 'budget_approved')
