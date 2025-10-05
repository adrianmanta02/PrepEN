"""increased description length

Revision ID: 18e4fda7be11
Revises: 1f72b041118c
Create Date: 2025-10-05 12:52:43.901194

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '18e4fda7be11'
down_revision: Union[str, Sequence[str], None] = '1f72b041118c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('materials', 'description', type = sa.String(length=6000),
                    existing_type=sa.String(length = 700))

def downgrade() -> None:
    """Downgrade schema."""
    pass
