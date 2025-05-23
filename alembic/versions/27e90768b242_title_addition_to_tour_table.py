"""title addition to Tour table

Revision ID: 27e90768b242
Revises: db797dbf2bf3
Create Date: 2025-02-11 20:10:14.801993

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '27e90768b242'
down_revision: Union[str, None] = 'db797dbf2bf3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tours', sa.Column('title', sa.String(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('tours', 'title')
    # ### end Alembic commands ###
