"""Remove bank fields and make previously_employed default False.

Revision ID: 391a0c89e5c7
Revises: f3bf786cf92e
Create Date: 2026-08-03 15:39:54.482832

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import sqlmodel
# revision identifiers, used by Alembic.
revision: str = '391a0c89e5c7'
down_revision: Union[str, None] = 'f3bf786cf92e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
