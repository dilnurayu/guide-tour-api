"""some fixes in the relationship

Revision ID: f574c4d7f7f1
Revises: a970f4da7b8e
Create Date: 2025-02-06 05:41:52.840132

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f574c4d7f7f1'
down_revision: Union[str, None] = 'a970f4da7b8e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
