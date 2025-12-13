"""add_bic_and_bank_name_to_employee

Revision ID: 76b6eb43b5c0
Revises: 3d2e4d2bf81b
Create Date: 2025-12-01 14:40:22.702951

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import sqlmodel
# revision identifiers, used by Alembic.
revision: str = '76b6eb43b5c0'
down_revision: Union[str, None] = '3d2e4d2bf81b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add bic and bank_name columns to employee table
    op.add_column('employee', sa.Column('bic', sa.String(), nullable=True))
    op.add_column('employee', sa.Column('bank_name', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove bic and bank_name columns from employee table
    op.drop_column('employee', 'bank_name')
    op.drop_column('employee', 'bic')
