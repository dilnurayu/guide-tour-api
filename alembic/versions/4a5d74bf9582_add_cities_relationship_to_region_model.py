"""Add cities relationship to Region model

Revision ID: 4a5d74bf9582
Revises: b64daf8f25f1
Create Date: 2025-01-24 12:28:09.595730

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4a5d74bf9582'
down_revision: Union[str, None] = 'b64daf8f25f1'
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
