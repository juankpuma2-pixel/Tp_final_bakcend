"""agregar_imagen_url_a_productos

Revision ID: 82428b69861b
Revises: 3b404fc31878
Create Date: 2026-11-02 08:58:01.414720

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '82428b69861b'
down_revision: Union[str, Sequence[str], None] = '3b404fc31878'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [col['name'] for col in inspector.get_columns('productos')]
    if 'imagen_url' not in columns:
        with op.batch_alter_table('productos', schema=None) as batch_op:
            batch_op.add_column(sa.Column('imagen_url', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('productos', schema=None) as batch_op:
        batch_op.drop_column('imagen_url')

