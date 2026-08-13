"""Alembic migration template."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = None  # type: ignore  # set by `alembic revision`
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass