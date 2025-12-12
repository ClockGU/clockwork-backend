"""empty message

Revision ID: 3feaeef2828f
Revises: 3d2e4d2bf81b
Create Date: 2025-12-01 14:34:55.146737

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import sqlmodel
# revision identifiers, used by Alembic.
revision: str = '3feaeef2828f'
down_revision: Union[str, None] = '3d2e4d2bf81b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
