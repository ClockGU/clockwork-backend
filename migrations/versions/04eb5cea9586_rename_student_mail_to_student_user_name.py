"""rename_student_mail_to_student_user_name

Revision ID: 04eb5cea9586
Revises: 92d7693e8b03
Create Date: 2025-11-30 19:47:37.746818

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import sqlmodel
# revision identifiers, used by Alembic.
revision: str = '04eb5cea9586'
down_revision: Union[str, None] = '92d7693e8b03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename column from student_mail to student_user_name
    op.alter_column('petition', 'student_mail', new_column_name='student_user_name')


def downgrade() -> None:
    # Rename column back from student_user_name to student_mail
    op.alter_column('petition', 'student_user_name', new_column_name='student_mail')
