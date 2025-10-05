"""added approval column for user

Revision ID: 0173583db351
Revises: 18e4fda7be11
Create Date: 2025-10-05 13:09:07.421042

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0173583db351'
down_revision: Union[str, Sequence[str], None] = '18e4fda7be11'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('is_approved', sa.Boolean(), nullable = False, server_default = sa.false()))


def downgrade() -> None:
    """Downgrade schema."""
    pass
