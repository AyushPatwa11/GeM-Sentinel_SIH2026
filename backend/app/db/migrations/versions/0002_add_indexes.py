"""Add indexes for Phase 0.

Revision ID: 0002
Revises: 0001
Create Date: 2026-01-01 00:01:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create indexes for query performance
    op.create_index('idx_bids_status', 'bids', ['status'])
    op.create_index('idx_bids_tender_version', 'bids', ['tender_version_id'])
    op.create_index('idx_bids_bidder_org', 'bids', ['bidder_org_id'])
    op.create_index('idx_audit_entity', 'audit_events', ['entity_id', 'created_at'])
    op.create_index('idx_compliance_bid', 'compliance_results', ['bid_id'])
    op.create_index('idx_risk_signals_bid', 'risk_signals', ['bid_id'])
    op.create_index('idx_extracted_facts_document', 'extracted_facts', ['document_id'])
    op.create_index('idx_documents_bid', 'documents', ['bid_id'])
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_tender_versions_published', 'tender_versions', ['published_at'])


def downgrade() -> None:
    # Drop all indexes
    op.drop_index('idx_bids_status')
    op.drop_index('idx_bids_tender_version')
    op.drop_index('idx_bids_bidder_org')
    op.drop_index('idx_audit_entity')
    op.drop_index('idx_compliance_bid')
    op.drop_index('idx_risk_signals_bid')
    op.drop_index('idx_extracted_facts_document')
    op.drop_index('idx_documents_bid')
    op.drop_index('idx_users_email')
    op.drop_index('idx_tender_versions_published')
