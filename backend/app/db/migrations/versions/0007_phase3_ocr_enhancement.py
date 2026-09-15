"""Add Phase 3 OCR enhancement fields.

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-12 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to ocr_jobs table for Phase 3 enhancement
    op.add_column('ocr_jobs', sa.Column('version_number', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('ocr_jobs', sa.Column('requested_by', sa.UUID(as_uuid=True), nullable=False, server_default=sa.text("'00000000-0000-0000-0000-000000000000'")))
    op.add_column('ocr_jobs', sa.Column('extracted_text', sa.Text(), nullable=True))
    op.add_column('ocr_jobs', sa.Column('extracted_entities', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    
    # Add foreign key for requested_by
    op.create_foreign_key('fk_ocr_jobs_requested_by', 'ocr_jobs', 'users', ['requested_by'], ['id'])


def downgrade() -> None:
    op.drop_constraint('fk_ocr_jobs_requested_by', 'ocr_jobs', type_='foreignkey')
    op.drop_column('ocr_jobs', 'extracted_entities')
    op.drop_column('ocr_jobs', 'extracted_text')
    op.drop_column('ocr_jobs', 'requested_by')
    op.drop_column('ocr_jobs', 'version_number')
