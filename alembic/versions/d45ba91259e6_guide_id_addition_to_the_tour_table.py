"""guide_id addition to the tour table

Revision ID: d45ba91259e6
Revises: ad0847b96f32
Create Date: 2025-01-29 11:03:54.840612

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd45ba91259e6'
down_revision: Union[str, None] = 'ad0847b96f32'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tours', sa.Column('guide_id', sa.Integer(), nullable=False))
    op.create_foreign_key(None, 'tours', 'users', ['guide_id'], ['user_id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'tours', type_='foreignkey')
    op.drop_column('tours', 'guide_id')
    # ### end Alembic commands ###
