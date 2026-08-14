"""Remove unnecessary time_exce_ date fields.

Revision ID: 916146966fdf
Revises: e65a0adeb339
Create Date: 2026-08-14 10:48:47.675956

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import sqlmodel
# revision identifiers, used by Alembic.
revision: str = '916146966fdf'
down_revision: Union[str, None] = 'e65a0adeb339'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
