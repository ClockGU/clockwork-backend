"""rename studentdocuments url columns to file

Revision ID: 36c611e225fd
Revises: e779434c85ce
Create Date: 2026-10-29 15:05:44.034797

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import sqlmodel
# revision identifiers, used by Alembic.
revision: str = '36c611e225fd'
down_revision: Union[str, None] = 'e779434c85ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


FIELDS = [
    'elstam',
    'studienbescheinigung',
    'versicherungsbescheinigung',
    'sozialversicherungsbogen',
    'ba_degree',
    'residence_permit',
    'id_photo',
]


def upgrade() -> None:
    for field in FIELDS:
        op.alter_column('studentdocuments', f'{field}_url', new_column_name=f'{field}_file')


def downgrade() -> None:
    for field in FIELDS:
        op.alter_column('studentdocuments', f'{field}_file', new_column_name=f'{field}_url')
