"""Add compliance result details columns (reasoning_chain, evidence_refs, rule_version).

Revision ID: 0004
Revises: 0003
Create Date: 2025-01-15 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers
revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade():
    """Add missing columns to compliance_results table."""
    
    # Add reasoning_chain, evidence_refs, and rule_version columns to compliance_results
    op.add_column('compliance_results', sa.Column('reasoning_chain', postgresql.JSONB, nullable=True))
    op.add_column('compliance_results', sa.Column('evidence_refs', postgresql.JSONB, nullable=True))
    op.add_column('compliance_results', sa.Column('rule_version', sa.String, nullable=True, server_default='1.0'))


def downgrade():
    """Remove added columns from compliance_results table."""
    
    op.drop_column('compliance_results', 'reasoning_chain')
    op.drop_column('compliance_results', 'evidence_refs')
    op.drop_column('compliance_results', 'rule_version')

