"""Add verification tables for real government data verification.

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-12 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade():
    """Create three new tables for verification audit trail and results."""
    
    # Create VerificationAttempt table
    op.create_table(
        'verification_attempt',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('extracted_fact_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('verification_provider', sa.String(50), nullable=False),
        sa.Column('extracted_value', sa.Text(), nullable=False),
        sa.Column('request_timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['extracted_fact_id'], ['extracted_facts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_extracted_fact_id', 'verification_attempt', ['extracted_fact_id'])
    op.create_index('idx_source_document_id', 'verification_attempt', ['source_document_id'])
    op.create_index('idx_verification_provider', 'verification_attempt', ['verification_provider'])
    op.create_index('idx_request_timestamp', 'verification_attempt', ['request_timestamp'])
    
    # Create VerificationResult table
    op.create_table(
        'verification_result',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('verification_attempt_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('api_response_code', sa.Integer()),
        sa.Column('api_reference_id', sa.String(255)),
        sa.Column('authority_value', sa.Text()),
        sa.Column('authority_normalized_value', sa.Text()),
        sa.Column('response_timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('verification_status', sa.String(20), nullable=False),
        sa.Column('fallback_used', sa.Boolean(), default=False),
        sa.Column('http_error_message', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "verification_status IN ('VERIFIED', 'MISMATCH', 'UNAVAILABLE', 'ERROR', 'INCONCLUSIVE', 'PENDING')",
            name='check_verification_status'
        ),
        sa.ForeignKeyConstraint(['verification_attempt_id'], ['verification_attempt.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('verification_attempt_id', name='uq_verification_attempt_id')
    )
    op.create_index('idx_verification_status', 'verification_result', ['verification_status'])
    op.create_index('idx_response_timestamp', 'verification_result', ['response_timestamp'])
    
    # Create VerificationNameMatch table
    op.create_table(
        'verification_name_match',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('verification_attempt_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_name', sa.Text(), nullable=False),
        sa.Column('normalized_document_name', sa.Text(), nullable=False),
        sa.Column('authority_name', sa.Text(), nullable=False),
        sa.Column('normalized_authority_name', sa.Text(), nullable=False),
        sa.Column('match_result', sa.String(20), nullable=False),
        sa.Column('match_score', sa.Numeric(5, 3), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("match_result IN ('exact_match', 'fuzzy_match', 'no_match')", name='check_match_result'),
        sa.CheckConstraint("match_score BETWEEN 0.0 AND 1.0", name='check_match_score'),
        sa.ForeignKeyConstraint(['verification_attempt_id'], ['verification_attempt.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_name_match_attempt_id', 'verification_name_match', ['verification_attempt_id'])
    op.create_index('idx_match_result', 'verification_name_match', ['match_result'])


def downgrade():
    """Remove verification tables."""
    op.drop_table('verification_name_match')
    op.drop_table('verification_result')
    op.drop_table('verification_attempt')
