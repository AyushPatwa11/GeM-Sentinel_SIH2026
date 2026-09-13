"""Initial schema from ORM models.

Revision ID: 0001
Revises: 
Create Date: 2026-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create organizations table
    op.create_table(
        'organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('legal_name', sa.Text(), nullable=False),
        sa.Column('cin', sa.Text(), nullable=True),
        sa.Column('gstin', sa.Text(), nullable=True),
        sa.Column('pan', sa.Text(), nullable=True),
        sa.Column('udyam_number', sa.Text(), nullable=True),
        sa.Column('nsic_number', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.Text(), nullable=False),
        sa.Column('password_hash', sa.Text(), nullable=False),
        sa.Column('role', sa.Text(), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("role IN ('bidder','officer','admin')", name='users_role_check'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='users_email_key')
    )

    # Create tenders table
    op.create_table(
        'tenders',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.Text(), nullable=False, server_default='draft'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('draft','published','closed')", name='tenders_status_check'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create tender_versions table
    op.create_table(
        'tender_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tender_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version_number', sa.Text(), nullable=False),
        sa.Column('is_corrigendum', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('supersedes_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('source_document_path', sa.Text(), nullable=False),
        sa.Column('precedence_policy_version', sa.Text(), nullable=False, server_default='default_v1'),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['supersedes_version_id'], ['tender_versions.id'], ),
        sa.ForeignKeyConstraint(['tender_id'], ['tenders.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tender_id', 'version_number', name='tender_versions_tender_id_version_number_key')
    )

    # Create clauses table
    op.create_table(
        'clauses',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tender_version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('raw_text', sa.Text(), nullable=False),
        sa.Column('source_page', sa.Integer(), nullable=True),
        sa.Column('source_span', sa.Text(), nullable=True),
        sa.Column('category', sa.Text(), nullable=True),
        sa.Column('mandatory', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('logic_tree', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('ambiguity_flag', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('ambiguity_reason', sa.Text(), nullable=True),
        sa.Column('extraction_confidence', sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column('grounding_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('superseded_by_clause_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("category IN ('FINANCIAL','STATUTORY','TECHNICAL','EXPERIENCE','OTHER')", name='clauses_category_check'),
        sa.ForeignKeyConstraint(['superseded_by_clause_id'], ['clauses.id'], ),
        sa.ForeignKeyConstraint(['tender_version_id'], ['tender_versions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create clause_diffs table
    op.create_table(
        'clause_diffs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('old_clause_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('new_clause_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('diff_type', sa.Text(), nullable=True),
        sa.Column('field_changed', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("diff_type IN ('ADDED','REMOVED','MODIFIED','UNCHANGED')", name='clause_diffs_diff_type_check'),
        sa.ForeignKeyConstraint(['new_clause_id'], ['clauses.id'], ),
        sa.ForeignKeyConstraint(['old_clause_id'], ['clauses.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create bids table
    op.create_table(
        'bids',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tender_version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('bidder_org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.Text(), nullable=False, server_default='draft'),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('draft','submitted','under_review','decided')", name='bids_status_check'),
        sa.ForeignKeyConstraint(['bidder_org_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['tender_version_id'], ['tender_versions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('bid_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_path', sa.Text(), nullable=False),
        sa.Column('file_hash', sa.Text(), nullable=False),
        sa.Column('doc_type', sa.Text(), nullable=True),
        sa.Column('classification_confidence', sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column('ocr_status', sa.Text(), nullable=False, server_default='PENDING'),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("ocr_status IN ('PENDING','DONE','FAILED','UNSUPPORTED')", name='documents_ocr_status_check'),
        sa.ForeignKeyConstraint(['bid_id'], ['bids.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create extracted_facts table
    op.create_table(
        'extracted_facts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('field_name', sa.Text(), nullable=False),
        sa.Column('field_value', sa.Text(), nullable=False),
        sa.Column('source_page', sa.Integer(), nullable=True),
        sa.Column('evidence_span', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Numeric(precision=4, scale=3), nullable=False),
        sa.Column('meets_threshold', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create entity_resolution_results table
    op.create_table(
        'entity_resolution_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('bid_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('claimed_org_name', sa.Text(), nullable=False),
        sa.Column('resolved_organization_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('match_method', sa.Text(), nullable=True),
        sa.Column('identifier_conflicts', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("match_method IN ('IDENTIFIER_EXACT','NAME_FUZZY','CONFLICT')", name='entity_resolution_results_match_method_check'),
        sa.CheckConstraint("status IN ('RESOLVED','CONFLICT','UNRESOLVED')", name='entity_resolution_results_status_check'),
        sa.ForeignKeyConstraint(['bid_id'], ['bids.id'], ),
        sa.ForeignKeyConstraint(['resolved_organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create verification_results table
    op.create_table(
        'verification_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('extracted_fact_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('adapter_source', sa.Text(), nullable=False),
        sa.Column('status', sa.Text(), nullable=False),
        sa.Column('checked_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['extracted_fact_id'], ['extracted_facts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create compliance_results table
    op.create_table(
        'compliance_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('bid_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('clause_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.Text(), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['bid_id'], ['bids.id'], ),
        sa.ForeignKeyConstraint(['clause_id'], ['clauses.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create risk_signals table
    op.create_table(
        'risk_signals',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('bid_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('signal_type', sa.Text(), nullable=False),
        sa.Column('severity', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['bid_id'], ['bids.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create risk_assessments table
    op.create_table(
        'risk_assessments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('bid_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('overall_risk_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('assessed_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['bid_id'], ['bids.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create officer_decisions table
    op.create_table(
        'officer_decisions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('bid_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('officer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('decision', sa.Text(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['bid_id'], ['bids.id'], ),
        sa.ForeignKeyConstraint(['officer_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create audit_events table
    op.create_table(
        'audit_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.Text(), nullable=False),
        sa.Column('entity_type', sa.Text(), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('prev_hash', sa.Text(), nullable=True),
        sa.Column('event_hash', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    # Drop tables in reverse order of creation
    op.drop_table('audit_events')
    op.drop_table('officer_decisions')
    op.drop_table('risk_assessments')
    op.drop_table('risk_signals')
    op.drop_table('compliance_results')
    op.drop_table('verification_results')
    op.drop_table('entity_resolution_results')
    op.drop_table('extracted_facts')
    op.drop_table('documents')
    op.drop_table('bids')
    op.drop_table('clause_diffs')
    op.drop_table('clauses')
    op.drop_table('tender_versions')
    op.drop_table('tenders')
    op.drop_table('users')
    op.drop_table('organizations')
