"""change the schema of petition

Revision ID: 4cdfda446ff0
Revises: 0101eb42e716
Create Date: 2025-04-02 00:31:47.744151

"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '4cdfda446ff0'
down_revision: Union[str, None] = '0101eb42e716'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Alter the column with explicit casting
    op.execute(
        """
        ALTER TABLE petition
        ALTER COLUMN ba_degree TYPE BOOLEAN
        USING ba_degree::BOOLEAN
        """
    )


def downgrade() -> None:
    # Revert the column back to VARCHAR
    op.execute(
        """
        ALTER TABLE petition
        ALTER COLUMN ba_degree TYPE VARCHAR
        USING ba_degree::TEXT
        """
    )