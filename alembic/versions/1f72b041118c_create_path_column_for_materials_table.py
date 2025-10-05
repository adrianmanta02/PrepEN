"""Create path column for materials table

Revision ID: 1f72b041118c
Revises: 
Create Date: 2025-10-02 23:06:02.544617

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1f72b041118c'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('materials', sa.Column("path", sa.String(), nullable = True))


def downgrade() -> None:
    """Downgrade schema."""
    pass
