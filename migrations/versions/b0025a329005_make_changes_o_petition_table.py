"""make changes o petition table

Revision ID: b0025a329005
Revises: 4cdfda446ff0
Create Date: 2025-04-02 00:43:37.349291

"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b0025a329005'
down_revision: Union[str, None] = '4cdfda446ff0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns
    op.add_column('petition', sa.Column('time_exce_course', sa.Boolean(), nullable=True))
    op.add_column('petition', sa.Column('duration_exce_course', sa.Boolean(), nullable=True))

    # Alter the column with explicit casting
    op.execute(
        """
        ALTER TABLE petition
        ALTER COLUMN time_exce_student TYPE BOOLEAN
        USING time_exce_student::BOOLEAN
        """
    )

    # Drop the old column
    op.drop_column('petition', 'duration_exce_student')


def downgrade() -> None:
    # Revert the changes
    op.add_column('petition', sa.Column('duration_exce_student', sa.VARCHAR(), autoincrement=False, nullable=True))

    op.execute(
        """
        ALTER TABLE petition
        ALTER COLUMN time_exce_student TYPE VARCHAR
        USING time_exce_student::TEXT
        """
    )

    op.drop_column('petition', 'duration_exce_course')
    op.drop_column('petition', 'time_exce_course')
