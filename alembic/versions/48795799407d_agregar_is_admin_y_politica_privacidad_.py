"""agregar_is_admin_y_politica_privacidad_a_usuarios

Revision ID: 48795799407d
Revises: 82428b69861b
Create Date: 2026-11-24 11:38:01.878647

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '48795799407d'
down_revision: Union[str, Sequence[str], None] = '82428b69861b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    cols_usuarios = [c['name'] for c in inspector.get_columns('usuarios')]
    with op.batch_alter_table('usuarios', schema=None) as batch_op:
        if 'is_admin' not in cols_usuarios:
            batch_op.add_column(sa.Column('is_admin', sa.Boolean(), server_default='0', nullable=False))
        if 'acepta_politica_privacidad' not in cols_usuarios:
            batch_op.add_column(sa.Column('acepta_politica_privacidad', sa.Boolean(), server_default='0', nullable=False))

    cols_productos = [c['name'] for c in inspector.get_columns('productos')]
    with op.batch_alter_table('productos', schema=None) as batch_op:
        if 'descripcion' not in cols_productos:
            batch_op.add_column(sa.Column('descripcion', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('productos', schema=None) as batch_op:
        batch_op.drop_column('descripcion')

    with op.batch_alter_table('usuarios', schema=None) as batch_op:
        batch_op.drop_column('acepta_politica_privacidad')
        batch_op.drop_column('is_admin')
