"""add status in petition table

Revision ID: 5f9eb82de8ba
Revises: b0025a329005
Create Date: 2025-04-05 19:09:32.889050

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import sqlmodel
# revision identifiers, used by Alembic.
revision: str = '5f9eb82de8ba'
down_revision: Union[str, None] = 'b0025a329005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add the column with a default value for existing rows
    op.add_column('petition', sa.Column('status', sa.String(), nullable=False, server_default='pending'))
    # Remove the default for future inserts
    op.alter_column('petition', 'status', server_default=None)


def downgrade() -> None:
    # Drop the column
    op.drop_column('petition', 'status')
