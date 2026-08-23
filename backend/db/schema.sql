-- GeM Sentinel schema (PostgreSQL)
-- Matches the locked schema design stage exactly.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============ Identity & Access ============

CREATE TABLE organizations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  legal_name TEXT NOT NULL,
  cin TEXT,
  gstin TEXT,
  pan TEXT,
  udyam_number TEXT,
  nsic_number TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('bidder','officer','admin')),
  organization_id UUID REFERENCES organizations(id),
  created_at TIMESTAMPTZ DEFAULT now()
);

-- ============ Tender & Versioning ============

CREATE TABLE tenders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  organization_id UUID REFERENCES organizations(id),
  created_by UUID REFERENCES users(id),
  status TEXT NOT NULL CHECK (status IN ('draft','published','closed')) DEFAULT 'draft',
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE tender_versions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tender_id UUID REFERENCES tenders(id) NOT NULL,
  version_number TEXT NOT NULL,
  is_corrigendum BOOLEAN DEFAULT FALSE,
  supersedes_version_id UUID REFERENCES tender_versions(id),
  source_document_path TEXT NOT NULL,
  precedence_policy_version TEXT NOT NULL DEFAULT 'default_v1',
  published_at TIMESTAMPTZ,
  UNIQUE(tender_id, version_number)
);

CREATE TABLE clauses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tender_version_id UUID REFERENCES tender_versions(id) NOT NULL,
  raw_text TEXT NOT NULL,
  source_page INT,
  source_span TEXT,
  category TEXT CHECK (category IN ('FINANCIAL','STATUTORY','TECHNICAL','EXPERIENCE','OTHER')),
  mandatory BOOLEAN NOT NULL DEFAULT TRUE,
  logic_tree JSONB NOT NULL,
  ambiguity_flag BOOLEAN DEFAULT FALSE,
  ambiguity_reason TEXT,
  extraction_confidence NUMERIC(4,3),
  grounding_verified BOOLEAN NOT NULL DEFAULT FALSE,
  superseded_by_clause_id UUID REFERENCES clauses(id),
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE clause_diffs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  old_clause_id UUID REFERENCES clauses(id),
  new_clause_id UUID REFERENCES clauses(id) NOT NULL,
  diff_type TEXT CHECK (diff_type IN ('ADDED','REMOVED','MODIFIED','UNCHANGED')),
  field_changed TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- ============ Bidding ============

CREATE TABLE bids (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tender_version_id UUID REFERENCES tender_versions(id) NOT NULL,
  bidder_org_id UUID REFERENCES organizations(id) NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('draft','submitted','under_review','decided')) DEFAULT 'draft',
  submitted_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  bid_id UUID REFERENCES bids(id) NOT NULL,
  file_path TEXT NOT NULL,
  file_hash TEXT NOT NULL,
  doc_type TEXT,
  classification_confidence NUMERIC(4,3),
  ocr_status TEXT CHECK (ocr_status IN ('PENDING','DONE','FAILED','UNSUPPORTED')) DEFAULT 'PENDING',
  uploaded_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE extracted_facts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID REFERENCES documents(id) NOT NULL,
  field_name TEXT NOT NULL,
  field_value TEXT NOT NULL,
  source_page INT,
  evidence_span TEXT NOT NULL,
  confidence NUMERIC(4,3) NOT NULL,
  meets_threshold BOOLEAN NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- ============ Entity Resolution ============

CREATE TABLE entity_resolution_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  bid_id UUID REFERENCES bids(id) NOT NULL,
  claimed_org_name TEXT NOT NULL,
  resolved_organization_id UUID REFERENCES organizations(id),
  match_method TEXT CHECK (match_method IN ('IDENTIFIER_EXACT','NAME_FUZZY','CONFLICT')),
  identifier_conflicts JSONB,
  status TEXT CHECK (status IN ('RESOLVED','CONFLICT','UNRESOLVED')),
  created_at TIMESTAMPTZ DEFAULT now()
);

-- ============ Verification ============

CREATE TABLE verification_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  extracted_fact_id UUID REFERENCES extracted_facts(id) NOT NULL,
  adapter_source TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('VERIFIED','MISMATCH','UNAVAILABLE','INCONCLUSIVE','PENDING','NOT_REQUIRED')),
  checked_at TIMESTAMPTZ NOT NULL,
  freshness_seconds INT,
  raw_response JSONB,
  evidence TEXT,
  error TEXT
);

-- ============ Compliance & Risk ============

CREATE TABLE compliance_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  bid_id UUID REFERENCES bids(id) NOT NULL,
  clause_id UUID REFERENCES clauses(id) NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('PASS','FAIL','WAIVED','REVIEW','NOT_EVALUATED')),
  reasoning_chain JSONB NOT NULL,
  evidence_refs JSONB NOT NULL,
  rule_version TEXT NOT NULL,
  evaluated_at TIMESTAMPTZ DEFAULT now(),
  CONSTRAINT evidence_required CHECK (jsonb_array_length(evidence_refs) > 0)
);

CREATE TABLE risk_signals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  bid_id UUID REFERENCES bids(id) NOT NULL,
  signal_type TEXT NOT NULL,
  weight NUMERIC(5,3) NOT NULL,
  severity NUMERIC(5,3) NOT NULL,

  extracted_fact_id UUID REFERENCES extracted_facts(id),
  verification_result_id UUID REFERENCES verification_results(id),
  entity_resolution_result_id UUID REFERENCES entity_resolution_results(id),
  compliance_result_id UUID REFERENCES compliance_results(id),

  policy_version TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),

  CONSTRAINT exactly_one_evidence_ref CHECK (
    (extracted_fact_id IS NOT NULL)::int +
    (verification_result_id IS NOT NULL)::int +
    (entity_resolution_result_id IS NOT NULL)::int +
    (compliance_result_id IS NOT NULL)::int = 1
  )
);

CREATE TABLE risk_assessments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  bid_id UUID REFERENCES bids(id) NOT NULL UNIQUE,
  total_score NUMERIC(6,3) NOT NULL,
  risk_level TEXT CHECK (risk_level IN ('LOW','MEDIUM','HIGH')),
  policy_version TEXT NOT NULL,
  computed_at TIMESTAMPTZ DEFAULT now()
);

-- ============ Human Review & Decisions ============

CREATE TABLE officer_decisions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  bid_id UUID REFERENCES bids(id) NOT NULL,
  officer_id UUID REFERENCES users(id) NOT NULL,
  ai_recommendation TEXT NOT NULL,
  final_decision TEXT NOT NULL CHECK (final_decision IN ('VERIFIED','NON_COMPLIANT','NEEDS_CLARIFICATION')),
  override_reason TEXT,
  decided_at TIMESTAMPTZ DEFAULT now()
);

-- ============ Audit (tamper-evident, append-only) ============

CREATE TABLE audit_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_type TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id UUID NOT NULL,
  actor_id UUID REFERENCES users(id),
  payload JSONB NOT NULL,
  prev_hash TEXT,
  event_hash TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE OR REPLACE FUNCTION prevent_audit_mutation() RETURNS TRIGGER AS $$
BEGIN
  RAISE EXCEPTION 'audit_events is append-only';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER no_update_audit
BEFORE UPDATE OR DELETE ON audit_events
FOR EACH ROW EXECUTE FUNCTION prevent_audit_mutation();
