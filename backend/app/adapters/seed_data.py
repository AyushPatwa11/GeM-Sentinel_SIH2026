"""
Seeded mock data standing in for GSTN / MCA / DigiLocker / NSIC.

Per PS26100 ("dummy bidder and tender datasets may be used for development
and testing") this is explicitly sanctioned, not a shortcut. Records are
hand-crafted (not bulk-generated) to deliberately cover the demo scenarios:
clean pass, missing/lapsed registration, identifier mismatch (contradiction),
and blacklist.
"""

GSTN_RECORDS = {
    # Clean, active bidder — Scenario A
    "22ABCDE1234F1Z5": {
        "legal_name": "Northline Engineering Pvt Ltd",
        "status": "ACTIVE",
        "return_filing_status": "REGULAR",
        "last_filed": "2026-07-20",
    },
    # Filing defaulter — contributes a risk signal, not an auto-fail
    "27PQRSX5678K1Z2": {
        "legal_name": "Coastal Agro Supplies",
        "status": "ACTIVE",
        "return_filing_status": "DEFAULTER",
        "last_filed": "2025-11-05",
    },
    # Registered to a DIFFERENT company than the bidder claims — Scenario C (contradiction)
    "09MERID1122M1Z9": {
        "legal_name": "Zenith Textile Traders",  # NOT "Meridian Textiles Pvt Ltd"
        "status": "ACTIVE",
        "return_filing_status": "REGULAR",
        "last_filed": "2026-06-15",
    },
}

MCA_RECORDS = {
    "U17124CT2015PTC098765": {
        "company_name": "Northline Engineering Pvt Ltd",
        "incorporation_date": "2015-04-11",
        "status": "ACTIVE",
    },
    "U74999MH2018PTC311122": {
        "company_name": "Coastal Agro Supplies",
        "incorporation_date": "2018-09-02",
        "status": "ACTIVE",
    },
}

NSIC_RECORDS = {
    "NSIC-CT-2021-004521": {
        "legal_name": "Northline Engineering Pvt Ltd",
        "category": "SMALL",
        "valid_until": "2027-03-31",
    },
}

UDYAM_RECORDS = {
    "UDYAM-CT-02-0012345": {
        "legal_name": "Coastal Agro Supplies",
        "category": "MICRO",
        "status": "ACTIVE",
    },
    # Bidder claims MSME/Micro but Udyam record shows a different category —
    # another flavor of Scenario C (contradiction), used in explainability demo
    "UDYAM-CT-02-0099887": {
        "legal_name": "Meridian Textiles Pvt Ltd",
        "category": "MEDIUM",  # bidder claimed MICRO in their bid documents
        "status": "ACTIVE",
    },
}

BLACKLIST_RECORDS = {
    # Deliberately blacklisted for demo purposes
    "27DEBAR9999X1Z1": {
        "legal_name": "Suraj Traders",
        "reason": "Debarred — prior contract non-performance",
        "debarred_until": "2027-01-01",
    }
}
