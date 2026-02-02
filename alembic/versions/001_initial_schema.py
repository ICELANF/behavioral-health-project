"""Initial schema - create all tables from models.py

Revision ID: 001
Revises: None
Create Date: 2026-02-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import os
import sys

# Ensure the project root is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core.models import Base

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables defined in core.models using Base.metadata."""
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    """Drop all tables defined in core.models using Base.metadata."""
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
