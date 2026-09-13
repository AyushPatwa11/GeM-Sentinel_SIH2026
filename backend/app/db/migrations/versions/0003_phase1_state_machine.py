"""Phase 1: Add state machine, document versioning, and clarification tracking.

Revision ID: 0003
Revises: 0002
Create Date: 2025-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers
revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade():
    """Add Phase 1 tables and columns."""
    
    # Add BidState table for state machine transitions
    op.create_table(
        'bid_states',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('bid_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('bids.id'), nullable=False),
        sa.Column('state', sa.String, nullable=False),
        sa.Column('entered_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('exited_at', sa.DateTime(timezone=True)),
        sa.Column('transition_metadata', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_bid_states_bid_id', 'bid_states', ['bid_id'])
    op.create_index('ix_bid_states_state', 'bid_states', ['state'])
    
    # Add ClarificationRequest table for Phase 7
    op.create_table(
        'clarification_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('bid_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('bids.id'), nullable=False),
        sa.Column('officer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('question_text', sa.Text, nullable=False),
        sa.Column('related_clause_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('clauses.id')),
        sa.Column('related_fact_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('extracted_facts.id')),
        sa.Column('status', sa.String, nullable=False, server_default='PENDING'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('resolved_at', sa.DateTime(timezone=True)),
        sa.CheckConstraint("status IN ('PENDING','RESOLVED','WITHDRAWN')"),
    )
    op.create_index('ix_clarification_requests_bid_id', 'clarification_requests', ['bid_id'])
    op.create_index('ix_clarification_requests_status', 'clarification_requests', ['status'])
    
    # Add ClarificationResponse table
    op.create_table(
        'clarification_responses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('clarification_request_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('clarification_requests.id'), nullable=False),
        sa.Column('bidder_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('response_text', sa.Text, nullable=False),
        sa.Column('supporting_documents', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_clarification_responses_request_id', 'clarification_responses', ['clarification_request_id'])
    
    # Add DocumentVersion table for versioning
    op.create_table(
        'document_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id'), nullable=False),
        sa.Column('version_number', sa.Integer, nullable=False),
        sa.Column('file_path', sa.Text, nullable=False),
        sa.Column('file_hash', sa.Text, nullable=False),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('upload_reason', sa.String, nullable=True),
        sa.Column('supersedes_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('document_versions.id')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('document_id', 'version_number'),
    )
    op.create_index('ix_document_versions_document_id', 'document_versions', ['document_id'])
    
    # Add OCR processing status table for Phase 3
    op.create_table(
        'ocr_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id'), nullable=False),
        sa.Column('status', sa.String, nullable=False, server_default='PENDING'),
        sa.Column('ocr_engine', sa.String, nullable=True),
        sa.Column('text_content', sa.Text),
        sa.Column('confidence_score', sa.Numeric(4, 3)),
        sa.Column('raw_response', postgresql.JSONB),
        sa.Column('error_message', sa.Text),
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('PENDING','PROCESSING','COMPLETED','FAILED')"),
    )
    op.create_index('ix_ocr_jobs_document_id', 'ocr_jobs', ['document_id'])
    op.create_index('ix_ocr_jobs_status', 'ocr_jobs', ['status'])
    
    # Add RiskSignal v2 with decomposition for Phase 6
    op.create_table(
        'risk_signal_decompositions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('risk_signal_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('risk_signals.id'), nullable=False),
        sa.Column('component_name', sa.String, nullable=False),
        sa.Column('component_weight', sa.Numeric(5, 3), nullable=False),
        sa.Column('component_evidence', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_risk_signal_decompositions_signal_id', 'risk_signal_decompositions', ['risk_signal_id'])
    
    # Add OfficerDecision v2 with override tracking for Phase 8
    op.create_table(
        'officer_decision_overrides',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('officer_decision_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('officer_decisions.id'), nullable=False),
        sa.Column('compliance_result_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('compliance_results.id')),
        sa.Column('original_compliance_status', sa.String, nullable=False),
        sa.Column('override_status', sa.String, nullable=False),
        sa.Column('override_evidence', postgresql.JSONB, nullable=True),
        sa.Column('override_rule_version', sa.String),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_officer_decision_overrides_decision_id', 'officer_decision_overrides', ['officer_decision_id'])
    
    # Add Notification table for Phase 13
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('notification_type', sa.String, nullable=False),
        sa.Column('subject', sa.String, nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('related_bid_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('bids.id')),
        sa.Column('is_read', sa.Boolean, server_default='false'),
        sa.Column('email_sent', sa.Boolean, server_default='false'),
        sa.Column('email_sent_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("notification_type IN ('STATUS_CHANGE','CLARIFICATION_REQUEST','CLARIFICATION_RESPONSE','DECISION_MADE','VERIFICATION_COMPLETE','RISK_FLAGGED')"),
    )
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('ix_notifications_is_read', 'notifications', ['is_read'])
    
    # Update Bid table with enhanced state tracking
    op.add_column('bids', sa.Column('current_state', sa.String, server_default='DRAFT'))
    op.add_column('bids', sa.Column('state_entered_at', sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.add_column('bids', sa.Column('state_metadata', postgresql.JSONB))
    
    # Update Document table with version tracking
    op.add_column('documents', sa.Column('current_version', sa.Integer, server_default='1'))
    op.add_column('documents', sa.Column('superseded_by_document_id', postgresql.UUID(as_uuid=True)))
    
    # Update ComplianceResult with immutability marker
    op.add_column('compliance_results', sa.Column('is_immutable', sa.Boolean, server_default='false'))
    op.add_column('compliance_results', sa.Column('original_status_before_override', sa.String))
    
    # Add constraints
    op.create_check_constraint(
        'check_bid_states',
        'bids',
        "current_state IN ('DRAFT','SUBMITTED','VERIFYING','REVIEW','CLARIFICATION','RESUBMITTED','DECIDED')"
    )
    op.create_index('ix_bids_current_state', 'bids', ['current_state'])


def downgrade():
    """Revert Phase 1 changes."""
    op.drop_table('bid_states')
    op.drop_table('clarification_requests')
    op.drop_table('clarification_responses')
    op.drop_table('document_versions')
    op.drop_table('ocr_jobs')
    op.drop_table('risk_signal_decompositions')
    op.drop_table('officer_decision_overrides')
    op.drop_table('notifications')
    
    op.drop_column('bids', 'current_state')
    op.drop_column('bids', 'state_entered_at')
    op.drop_column('bids', 'state_metadata')
    op.drop_column('documents', 'current_version')
    op.drop_column('documents', 'superseded_by_document_id')
    op.drop_column('compliance_results', 'is_immutable')
    op.drop_column('compliance_results', 'original_status_before_override')
