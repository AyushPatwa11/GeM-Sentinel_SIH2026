"""
In-memory demo dataset for the hackathon build.

This stands in for the Postgres schema (db/schema.sql) so the API can run
without a live database — every shape here matches the real schema's
fields exactly, so swapping this module for real SQLAlchemy queries later
is a drop-in replacement, not a rewrite.

Three bidders are seeded, each hitting a different demo scenario:
  Northline Engineering  -> clean pass (Scenario A)
  Coastal Agro Supplies  -> GST return defaulter, MSME/EMD waiver (Scenario B/E)
  Meridian Textiles      -> GSTIN + Udyam identity contradiction (Scenario C)
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

TENDER_ID = "tender-101"
TENDER_VERSION_ID = "tv-101-v1"

TENDER = {
    "id": TENDER_ID,
    "title": "Supply of Industrial Textile Materials — GeM/2026/T-101",
    "organization": "Chennai Petroleum Corporation Limited",
    "status": "published",
}

TENDER_VERSION = {
    "id": TENDER_VERSION_ID,
    "tender_id": TENDER_ID,
    "version_number": "1.0",
    "is_corrigendum": False,
    "precedence_policy_version": "default_v1",
    "published_at": datetime(2026, 7, 1, tzinfo=timezone.utc).isoformat(),
}

# Multiple published tenders make the bidder workflow exercise the real
# tender -> bid relationship instead of treating seeded bidder scenarios as
# if they were different tenders.
TENDERS = {
    TENDER_ID: TENDER,
    "tender-102": {
        "id": "tender-102",
        "title": "Supply of Electrical Maintenance Components — GeM/2026/T-102",
        "organization": "Chennai Petroleum Corporation Limited",
        "status": "published",
    },
}

TENDER_VERSIONS = {
    TENDER_VERSION_ID: TENDER_VERSION,
    "tv-102-v1": {
        "id": "tv-102-v1",
        "tender_id": "tender-102",
        "version_number": "1.0",
        "is_corrigendum": False,
        "precedence_policy_version": "default_v1",
        "published_at": datetime(2026, 7, 4, tzinfo=timezone.utc).isoformat(),
    },
}

# Logic trees follow app.services.rules.schema exactly.
CLAUSES = [
    {
        "id": "clause-gst-pan",
        "tender_version_id": TENDER_VERSION_ID,
        "raw_text": "Bidder must possess a valid GST registration AND a valid PAN.",
        "category": "STATUTORY",
        "mandatory": True,
        "grounding_verified": True,
        "logic_tree": {
            "type": "AND",
            "children": [
                {"type": "LEAF", "condition": {"field": "gst_valid", "operator": "==", "value": True}},
                {"type": "LEAF", "condition": {"field": "pan_valid", "operator": "==", "value": True}},
            ],
        },
    },
    {
        "id": "clause-gstin-identity",
        "tender_version_id": TENDER_VERSION_ID,
        "raw_text": "The GSTIN submitted must be registered to the bidding entity.",
        "category": "STATUTORY",
        "mandatory": True,
        "grounding_verified": True,
        "logic_tree": {
            "type": "LEAF",
            "condition": {"field": "gstin_identity_match", "operator": "==", "value": True},
        },
    },
    {
        "id": "clause-turnover-or-experience",
        "tender_version_id": TENDER_VERSION_ID,
        "raw_text": "Bidder must have annual turnover of at least ₹1 crore OR at least 2 similar completed projects.",
        "category": "FINANCIAL",
        "mandatory": True,
        "grounding_verified": True,
        "logic_tree": {
            "type": "OR",
            "children": [
                {"type": "LEAF", "condition": {"field": "annual_turnover", "operator": ">=", "value": 10_000_000, "unit": "INR"}},
                {"type": "LEAF", "condition": {"field": "similar_project_count", "operator": ">=", "value": 2}},
            ],
        },
    },
    {
        "id": "clause-emd",
        "tender_version_id": TENDER_VERSION_ID,
        "raw_text": "EMD of ₹50,000 is mandatory unless the bidder qualifies for MSME exemption.",
        "category": "FINANCIAL",
        "mandatory": True,
        "grounding_verified": True,
        "logic_tree": {
            "type": "LEAF",
            "condition": {"field": "emd_paid", "operator": "==", "value": True},
            "exceptions": [
                {"applies_if": {"field": "msme_exemption", "operator": "==", "value": True}, "waives": True}
            ],
        },
    },
    {
        "id": "clause-not-blacklisted",
        "tender_version_id": TENDER_VERSION_ID,
        "raw_text": "Bidder must not be under any active blacklisting or debarment order.",
        "category": "STATUTORY",
        "mandatory": True,
        "grounding_verified": True,
        "logic_tree": {
            "type": "LEAF",
            "condition": {"field": "debarment_clear", "operator": "==", "value": True},
        },
    },
    {
        "id": "clause-experience-cert",
        "tender_version_id": TENDER_VERSION_ID,
        "raw_text": "Bidder must submit at least one adequate work-completion / experience certificate.",
        "category": "EXPERIENCE",
        "mandatory": False,
        "grounding_verified": False,
        "ambiguity_flag": True,
        "ambiguity_reason": "\"Adequate\" is not a measurable threshold — no minimum contract value or duration is defined.",
        "logic_tree": {
            "type": "LEAF",
            "condition": {"field": "experience_cert_present", "operator": "==", "value": True},
        },
    },
]

# The second tender intentionally uses a separate requirement set. The same
# evaluator consumes both sets, so tender-specific rules are never inferred
# from a frontend label.
CLAUSES_BY_TENDER_VERSION = {
    TENDER_VERSION_ID: CLAUSES,
    "tv-102-v1": [
        {
            "id": "clause-102-gst-pan",
            "tender_version_id": "tv-102-v1",
            "raw_text": "Bidder must possess a valid GST registration AND a valid PAN.",
            "category": "STATUTORY",
            "mandatory": True,
            "grounding_verified": True,
            "logic_tree": {
                "type": "AND",
                "children": [
                    {"type": "LEAF", "condition": {"field": "gst_valid", "operator": "==", "value": True}},
                    {"type": "LEAF", "condition": {"field": "pan_valid", "operator": "==", "value": True}},
                ],
            },
        },
        {
            "id": "clause-102-emd",
            "tender_version_id": "tv-102-v1",
            "raw_text": "EMD of ₹25,000 is mandatory unless the bidder qualifies for MSME exemption.",
            "category": "FINANCIAL",
            "mandatory": True,
            "grounding_verified": True,
            "logic_tree": {
                "type": "LEAF",
                "condition": {"field": "emd_paid", "operator": "==", "value": True},
                "exceptions": [
                    {"applies_if": {"field": "msme_exemption", "operator": "==", "value": True}, "waives": True}
                ],
            },
        },
    ],
}

# Bid-level extracted facts. Each fact carries evidence + confidence exactly
# as app/services/rules/schema.Fact and app/models ExtractedFact expect.
# `verification_status` here simulates what the adapter layer would return
# for each field once wired through app.adapters.registry.
BIDS = {
    "bid-northline": {
        "id": "bid-northline",
        "tender_version_id": TENDER_VERSION_ID,
        "bidder_org_name": "Northline Engineering Pvt Ltd",
        "gstin": "22ABCDE1234F1Z5",
        "status": "submitted",
        "documents": [
            {"id": "doc-n1", "doc_type": "GST_CERT", "ocr_status": "DONE"},
            {"id": "doc-n2", "doc_type": "PAN", "ocr_status": "DONE"},
            {"id": "doc-n3", "doc_type": "FINANCIAL_STMT", "ocr_status": "DONE"},
            {"id": "doc-n4", "doc_type": "EXPERIENCE_CERT", "ocr_status": "DONE"},
        ],
        "facts": [
            {"field": "gst_valid", "value": True, "confidence": 0.98, "evidence_ref": "doc-n1", "evidence_span": "GSTIN 22ABCDE1234F1Z5 — Status: Active"},
            {"field": "pan_valid", "value": True, "confidence": 0.97, "evidence_ref": "doc-n2", "evidence_span": "PAN ABCDE1234F"},
            {"field": "gstin_identity_match", "value": True, "confidence": 0.98, "evidence_ref": "doc-n1", "evidence_span": "GSTN registry legal_name matches bid organization name"},
            {"field": "annual_turnover", "value": 18_500_000, "confidence": 0.96, "evidence_ref": "doc-n3", "evidence_span": "FY 2025-26 Turnover: ₹1,85,00,000"},
            {"field": "similar_project_count", "value": 4, "confidence": 0.9, "evidence_ref": "doc-n4", "evidence_span": "4 completed contracts listed in experience certificate"},
            {"field": "emd_paid", "value": True, "confidence": 0.99, "evidence_ref": "doc-n3", "evidence_span": "EMD payment receipt ₹50,000 dated 2026-07-10"},
            {"field": "msme_exemption", "value": False, "confidence": 0.9, "evidence_ref": "doc-n1", "evidence_span": "No MSME/Udyam declaration submitted"},
            {"field": "debarment_clear", "value": True, "confidence": 1.0, "evidence_ref": "doc-n1", "evidence_span": "No debarment record found (BLACKLIST source)"},
            {"field": "experience_cert_present", "value": True, "confidence": 0.9, "evidence_ref": "doc-n4", "evidence_span": "Experience certificate uploaded"},
        ],
    },
    "bid-coastal": {
        "id": "bid-coastal",
        "tender_version_id": TENDER_VERSION_ID,
        "bidder_org_name": "Coastal Agro Supplies",
        "gstin": "27PQRSX5678K1Z2",
        "status": "submitted",
        "documents": [
            {"id": "doc-c1", "doc_type": "GST_CERT", "ocr_status": "DONE"},
            {"id": "doc-c2", "doc_type": "PAN", "ocr_status": "DONE"},
            {"id": "doc-c3", "doc_type": "UDYAM_CERT", "ocr_status": "DONE"},
        ],
        "facts": [
            {"field": "gst_valid", "value": True, "confidence": 0.95, "evidence_ref": "doc-c1", "evidence_span": "GSTIN 27PQRSX5678K1Z2 — Status: Active, filing DEFAULTER"},
            {"field": "pan_valid", "value": True, "confidence": 0.96, "evidence_ref": "doc-c2", "evidence_span": "PAN PQRSX5678K"},
            {"field": "gstin_identity_match", "value": True, "confidence": 0.95, "evidence_ref": "doc-c1", "evidence_span": "GSTN registry legal_name matches bid organization name"},
            {"field": "annual_turnover", "value": 4_200_000, "confidence": 0.85, "evidence_ref": "doc-c1", "evidence_span": "Self-declared turnover ₹42,00,000"},
            {"field": "similar_project_count", "value": 1, "confidence": 0.8, "evidence_ref": "doc-c1", "evidence_span": "1 prior project listed"},
            {"field": "emd_paid", "value": False, "confidence": 0.9, "evidence_ref": "doc-c3", "evidence_span": "No EMD receipt found in submission"},
            {"field": "msme_exemption", "value": True, "confidence": 0.94, "evidence_ref": "doc-c3", "evidence_span": "Udyam MICRO category certificate UDYAM-CT-02-0012345"},
            {"field": "debarment_clear", "value": True, "confidence": 1.0, "evidence_ref": "doc-c1", "evidence_span": "No debarment record found (BLACKLIST source)"},
            {"field": "experience_cert_present", "value": False, "confidence": 0.0, "evidence_ref": None, "evidence_span": None},
        ],
    },
    "bid-meridian": {
        "id": "bid-meridian",
        "tender_version_id": TENDER_VERSION_ID,
        "bidder_org_name": "Meridian Textiles Pvt Ltd",
        "gstin": "09MERID1122M1Z9",
        "status": "submitted",
        "documents": [
            {"id": "doc-m1", "doc_type": "GST_CERT", "ocr_status": "DONE"},
            {"id": "doc-m2", "doc_type": "PAN", "ocr_status": "DONE"},
            {"id": "doc-m3", "doc_type": "UDYAM_CERT", "ocr_status": "DONE"},
            {"id": "doc-m4", "doc_type": "FINANCIAL_STMT", "ocr_status": "DONE"},
        ],
        "facts": [
            {"field": "gst_valid", "value": True, "confidence": 0.97, "evidence_ref": "doc-m1", "evidence_span": "GSTIN 09MERID1122M1Z9 — Status: Active"},
            {"field": "pan_valid", "value": True, "confidence": 0.96, "evidence_ref": "doc-m2", "evidence_span": "PAN MERID1122M"},
            # Deliberate contradiction: GSTN registry legal_name is "Zenith Textile Traders",
            # not "Meridian Textiles Pvt Ltd" — this is Scenario C.
            "gstin_identity_match_placeholder",
            {"field": "annual_turnover", "value": 22_000_000, "confidence": 0.92, "evidence_ref": "doc-m4", "evidence_span": "FY 2025-26 Turnover: ₹2,20,00,000"},
            {"field": "similar_project_count", "value": 3, "confidence": 0.85, "evidence_ref": "doc-m4", "evidence_span": "3 completed contracts listed"},
            {"field": "emd_paid", "value": True, "confidence": 0.95, "evidence_ref": "doc-m4", "evidence_span": "EMD payment receipt ₹50,000"},
            {"field": "msme_exemption", "value": False, "confidence": 0.9, "evidence_ref": "doc-m3", "evidence_span": "Udyam category claimed as MICRO in bid narrative"},
            {"field": "debarment_clear", "value": True, "confidence": 1.0, "evidence_ref": "doc-m1", "evidence_span": "No debarment record found (BLACKLIST source)"},
            {"field": "experience_cert_present", "value": True, "confidence": 0.88, "evidence_ref": "doc-m4", "evidence_span": "Experience summary included in financial statement"},
        ],
    },
}
# clean up the placeholder marker from bid-meridian (kept above for readability of the diff)
BIDS["bid-meridian"]["facts"] = [
    f for f in BIDS["bid-meridian"]["facts"] if f != "gstin_identity_match_placeholder"
]
BIDS["bid-meridian"]["facts"].insert(
    2,
    {
        "field": "gstin_identity_match",
        "value": False,  # will be confirmed FALSE by live adapter check against GSTN_RECORDS
        "confidence": 0.93,
        "evidence_ref": "doc-m1",
        "evidence_span": "Bid claims 'Meridian Textiles Pvt Ltd'; cross-check required against GSTN registry",
    },
)
