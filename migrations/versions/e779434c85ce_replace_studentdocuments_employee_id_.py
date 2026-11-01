"""replace studentdocuments employee_id with user_account

Revision ID: e779434c85ce
Revises: 06d7685e2d3c
Create Date: 2026-10-29 13:22:35.132448

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import sqlmodel
# revision identifiers, used by Alembic.
revision: str = 'e779434c85ce'
down_revision: Union[str, None] = '06d7685e2d3c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('studentdocuments', sa.Column('user_account', sa.Uuid(), nullable=True))

    # Backfill user_account from the linked employee
    op.execute("""
        UPDATE studentdocuments
        SET user_account = employee.user_account
        FROM employee
        WHERE studentdocuments.employee_id = employee.id;
    """)

    op.alter_column('studentdocuments', 'user_account', nullable=False)
    op.create_unique_constraint('uq_studentdocuments_user_account', 'studentdocuments', ['user_account'])
    op.create_foreign_key(
        'studentdocuments_user_account_fkey',
        'studentdocuments',
        'employee',
        ['user_account'],
        ['user_account'],
        onupdate='CASCADE',
    )

    # Dropping the column also drops its unique constraint and foreign key
    op.drop_column('studentdocuments', 'employee_id')


def downgrade() -> None:
    op.add_column('studentdocuments', sa.Column('employee_id', sa.Uuid(), nullable=True))

    # Backfill employee_id from the linked employee
    op.execute("""
        UPDATE studentdocuments
        SET employee_id = employee.id
        FROM employee
        WHERE studentdocuments.user_account = employee.user_account;
    """)

    op.alter_column('studentdocuments', 'employee_id', nullable=False)
    op.create_unique_constraint('uq_studentdocuments_employee_id', 'studentdocuments', ['employee_id'])
    op.create_foreign_key(
        'studentdocuments_employee_id_fkey',
        'studentdocuments',
        'employee',
        ['employee_id'],
        ['id'],
    )

    # Dropping the column also drops its unique constraint and foreign key
    op.drop_column('studentdocuments', 'user_account')
