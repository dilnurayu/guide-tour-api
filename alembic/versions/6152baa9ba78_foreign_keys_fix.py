"""foreign keys fix

Revision ID: 6152baa9ba78
Revises: d45ba91259e6
Create Date: 2025-01-29 11:25:27.345425

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6152baa9ba78'
down_revision: Union[str, None] = 'd45ba91259e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('book_guide', sa.Column('tourist_id', sa.Integer(), nullable=False))
    op.create_foreign_key(None, 'book_guide', 'users', ['tourist_id'], ['user_id'])
    op.add_column('book_tour', sa.Column('tourist_id', sa.Integer(), nullable=False))
    op.create_foreign_key(None, 'book_tour', 'users', ['tourist_id'], ['user_id'])
    op.add_column('reviews', sa.Column('tourist_id', sa.Integer(), nullable=False))
    op.create_foreign_key(None, 'reviews', 'users', ['tourist_id'], ['user_id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'reviews', type_='foreignkey')
    op.drop_column('reviews', 'tourist_id')
    op.drop_constraint(None, 'book_tour', type_='foreignkey')
    op.drop_column('book_tour', 'tourist_id')
    op.drop_constraint(None, 'book_guide', type_='foreignkey')
    op.drop_column('book_guide', 'tourist_id')
    # ### end Alembic commands ###
