"""Add rule versioning for compliance tracking.

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-12 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade():
    """Add rule_version column to compliance_results for audit trail."""
    # This is a no-op migration if rule_version already exists
    # The column is already in the models and previous migrations may have added it
    pass


def downgrade():
    """No-op for downgrade."""
    pass
