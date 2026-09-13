"""Seed demo users and organizations into database on startup."""
from sqlalchemy.orm import Session
from app.models.models import Organization, User, Tender, TenderVersion
from app.security.auth import hash_password
from datetime import datetime, timezone
import uuid


def seed_demo_data(db: Session):
    """Seed demo organizations, users, and tenders if database is empty.
    
    Creates 5 bidder organizations + 1 officer organization with demo users.
    Also creates 2 published demo tenders for bidders to view.
    Idempotent: only runs if organizations table is empty.
    
    Args:
        db: SQLAlchemy session
    """
    # Check if already seeded (look for demo tenders first)
    existing_tenders = db.query(Tender).count()
    if existing_tenders > 0:
        return  # Already seeded
    
    # Check if organizations exist
    if db.query(Organization).count() == 0:
        # Bidder organizations with GST + PAN
        bidders = [
            {
                "legal_name": "ABC Manufacturing",
                "gstin": "22AABCT0001H1Z0",
                "pan": "AAAPA1234A",
                "email": "abc@bidder.com",
            },
            {
                "legal_name": "XYZ Traders",
                "gstin": "27XYZOP0002K2Z0",
                "pan": "BBBPB5678B",
                "email": "xyz@bidder.com",
            },
            {
                "legal_name": "GHI Services",
                "gstin": "29GHIJKL0003L3Z0",
                "pan": "CCCC7890C",
                "email": "ghi@bidder.com",
            },
            {
                "legal_name": "PQR Consultants",
                "gstin": "30PQRST0004M4Z0",
                "pan": "DDDDE1234D",
                "email": "pqr@bidder.com",
            },
            {
                "legal_name": "STU Solutions",
                "gstin": "31STUV0005N5Z0",
                "pan": "EEEEF5678E",
                "email": "stu@bidder.com",
            },
        ]
        
        # Create bidder organizations and users
        for bidder_data in bidders:
            email = bidder_data.pop("email")
            org = Organization(**bidder_data)
            db.add(org)
            db.flush()  # Get org.id assigned
            
            # Create user for this bidder org
            user = User(
                email=email,
                password_hash=hash_password("password123"),
                role="bidder",
                organization_id=org.id,
            )
            db.add(user)
        
        # Officer organization (GeM Ministry)
        officer_org = Organization(legal_name="GeM Ministry", gstin=None, pan=None)
        db.add(officer_org)
        db.flush()  # Get org.id assigned
        
        officer_user = User(
            email="officer@gem.gov",
            password_hash=hash_password("officer123"),
            role="officer",
            organization_id=officer_org.id,
        )
        db.add(officer_user)
        db.flush()
    else:
        # Organizations exist, just get officer user
        officer_user = db.query(User).filter(User.email == "officer@gem.gov").first()
        if not officer_user:
            officer_org = db.query(Organization).filter(Organization.legal_name == "GeM Ministry").first()
            if not officer_org:
                officer_org = Organization(legal_name="GeM Ministry", gstin=None, pan=None)
                db.add(officer_org)
                db.flush()
            officer_user = User(
                email="officer@gem.gov",
                password_hash=hash_password("officer123"),
                role="officer",
                organization_id=officer_org.id,
            )
            db.add(officer_user)
            db.flush()
    
    # Create demo tenders for bidders to view
    demo_tenders = [
        {
            "title": "Supply of Industrial Textile Materials — GeM/2026/T-101",
            "description": "Procurement of high-quality industrial textile materials for corporate use",
            "organization": "Chennai Petroleum Corporation Limited",
            "created_by": officer_user.id,
            "deadline": datetime(2026, 12, 31, tzinfo=timezone.utc),
        },
        {
            "title": "Supply of Electrical Maintenance Components — GeM/2026/T-102",
            "description": "Supply of electrical maintenance components and spare parts",
            "organization": "Chennai Petroleum Corporation Limited",
            "created_by": officer_user.id,
            "deadline": datetime(2026, 12, 31, tzinfo=timezone.utc),
        },
    ]
    
    for tender_data in demo_tenders:
        tender = Tender(
            id=uuid.uuid4(),
            title=tender_data["title"],
            description=tender_data["description"],
            created_by=tender_data["created_by"],
            deadline=tender_data["deadline"],
            status="published",
        )
        db.add(tender)
        db.flush()
        
        # Create published version
        version = TenderVersion(
            id=uuid.uuid4(),
            tender_id=tender.id,
            version_number="1.0",
            source_document_path="/uploads/tender.pdf",
            precedence_policy_version="default_v1",
            published_at=datetime.now(timezone.utc),
        )
        db.add(version)
    
    db.commit()
