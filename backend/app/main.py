"""GeM Sentinel API - Phases 0-13: Complete Implementation."""
from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import hashlib
import os
import uuid
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

from app.db.base import get_db
from app.models.models import (
    User, Tender, TenderVersion, Bid, Document, AuditEvent,
    BidState, DocumentVersion, OCRJob, ClarificationRequest, 
    ClarificationResponse, OfficerDecision, Notification,
    ComplianceResult, RiskAssessment, ExtractedFact, RiskSignal
)
from app.security.auth import create_access_token, verify_password, hash_password, JWT_EXPIRATION_MINUTES
from app.schemas.auth import LoginRequest, TokenResponse, RegisterRequest, UserResponse
from app.schemas.common import (
    TenderCreateRequest,
    TenderResponse,
    BidCreateRequest,
    BidResponse,
)
from app.exceptions import (
    GemSentinelException,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    DuplicateResourceError
)
from app.db.seed import seed_demo_data
from app.middleware.auth import AuthMiddleware
from app.security.rbac import require_role
from app.services.bid_service import BidService
from app.services.state_machine import BidStateMachine, BidStatus
from app.services.tender_service import TenderService
from app.services.document_service import DocumentService
from app.services.ocr_service import OCRService
from app.services.verification_service import VerificationService
from app.services.compliance_service import ComplianceService
from app.services.compliance_rule_engine import ComplianceRuleEngine
from app.services.evidence_traceability_phase4 import EvidenceTraceabilityPhase4
from app.services.adapter_orchestrator_phase5 import AdapterOrchestratorPhase5
from app.services.risk_service import RiskService
from app.services.risk_scoring_engine import RiskScoringEngine
from app.services.officer_decision_engine import DecisionRecommendationEngine, OfficerDecisionWorkflow, OfficerDashboardHelper
from app.services.clarification_service import ClarificationService
from app.services.officer_decision_service import OfficerDecisionService
from app.services.notification_service import NotificationService
from app.services.evidence_traceability import EvidenceTraceability

app = FastAPI(
    title="GeM Sentinel API (Phases 0-13)",
    version="1.0.0",
    description="Complete procurement fraud detection system"
)

# Middleware - CORS must be added first (executed last)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers including Authorization
)

# ============================================================================
# GLOBAL EXCEPTION HANDLERS
# ============================================================================

@app.exception_handler(GemSentinelException)
async def gem_sentinel_exception_handler(request: Request, exc: GemSentinelException):
    """Handle application exceptions."""
    logger.error(
        f"Application error: {exc.code}",
        extra={
            "endpoint": request.url.path,
            "error_details": exc.details,
        }
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "error_code": exc.code,
            "details": exc.details,
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.exception(
        f"Unexpected error: {exc}",
        extra={
            "endpoint": request.url.path,
        }
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_code": "INTERNAL_ERROR",
        }
    )

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_user_from_request(request: Request) -> dict:
    """Extract user info from request or Authorization token."""
    if hasattr(request.state, 'user') and request.state.user:
        return request.state.user
    
    # Extract from Authorization header
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            from app.security.auth import decode_access_token
            payload = decode_access_token(token)
            user = {
                "id": payload["user_id"],
                "role": payload.get("role", "bidder"),
            }
            request.state.user = user
            return user
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    
    raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

# Startup
@app.on_event("startup")
async def startup_event():
    """Create database tables and seed demo data on startup."""
    from app.db.base import SessionLocal, engine
    from app.models.models import Base
    
    try:
        # Create all tables from models
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.warning(f"Could not create tables: {str(e)}")
    
    # Then seed demo data
    db = SessionLocal()
    try:
        try:
            seed_demo_data(db)
            logger.info("Demo data seeded successfully")
        except Exception as e:
            logger.warning(f"Could not seed demo data: {str(e)}")
    finally:
        db.close()

# ============================================================================
# HEALTH & INFO
# ============================================================================

@app.get("/health")
def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "version": "1.0.0",
        "phases": "0-13",
        "components": [
            "database_persistence",
            "authentication_rbac",
            "state_machine",
            "document_versioning",
            "ocr_extraction",
            "verification",
            "compliance",
            "risk_scoring",
            "clarification",
            "officer_decisions",
            "notifications",
        ]
    }

# ============================================================================
# AUTHENTICATION
# ============================================================================

@app.post("/api/auth/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token.
    
    Example:
        POST /api/auth/login
        Body: {"email": "officer@gem.gov", "password": "officer123"}
        Returns: {"access_token": "...", "token_type": "bearer", "expires_in": 3600}
    """
    user = db.query(User).filter(User.email == body.email).first()
    
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_access_token(str(user.id), user.role, JWT_EXPIRATION_MINUTES)
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=JWT_EXPIRATION_MINUTES * 60,
        role=user.role,
        user_id=str(user.id),
    )


@app.post("/api/auth/register", response_model=TokenResponse, status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user account.
    
    Requirements:
        - Email must be unique
        - Password >= 8 chars with uppercase and digit
        - Role must be 'officer', 'bidder', or 'admin'
        - Bidders must provide organization_id
    
    Example:
        POST /api/auth/register
        Body: {
            "email": "bidder@company.com",
            "password": "SecurePass123",
            "password_confirm": "SecurePass123",
            "role": "bidder",
            "organization_id": "550e8400-e29b-41d4-a716-446655440000"
        }
        Returns: {"access_token": "...", "token_type": "bearer", "expires_in": 3600}
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == body.email).first()
    if existing_user:
        raise HTTPException(
            status_code=409,
            detail=f"User with email {body.email} already exists"
        )
    
    # Validate bidder has organization_id
    if body.role == "bidder" and not body.organization_id:
        raise HTTPException(
            status_code=400,
            detail="Bidders must provide organization_id"
        )
    
    # Create new user
    new_user = User(
        id=uuid.uuid4(),
        email=body.email,
        password_hash=hash_password(body.password),
        role=body.role,
        organization_id=body.organization_id if body.role == "bidder" else None,
        created_at=datetime.utcnow()
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create JWT token
    access_token = create_access_token(str(new_user.id), new_user.role, JWT_EXPIRATION_MINUTES)
    
    # Log registration audit event
    audit_event = AuditEvent(
        id=uuid.uuid4(),
        event_type="USER_REGISTERED",
        actor_id=str(new_user.id),
        actor_role=new_user.role,
        entity_type="User",
        entity_id=str(new_user.id),
        details={"email": new_user.email, "role": new_user.role},
        timestamp=datetime.utcnow()
    )
    db.add(audit_event)
    db.commit()
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=JWT_EXPIRATION_MINUTES * 60,
        role=new_user.role,
        user_id=str(new_user.id),
    )


@app.get("/api/user/profile", response_model=UserResponse)
def get_user_profile(request: Request, db: Session = Depends(get_db)):
    """Get authenticated user profile.
    
    Requires: Valid JWT token in Authorization header
    Returns: User details including organization info
    """
    user = get_user_from_request(request)
    user_id = user["id"]
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        role=user.role,
        organization_id=str(user.organization_id) if user.organization_id else None
    )

# ============================================================================
# PHASE 2: TENDER MANAGEMENT & BID CREATION
# ============================================================================

@app.post("/api/officer/tenders", response_model=TenderResponse, status_code=201)
def create_tender(
    body: TenderCreateRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Create a new tender (officer only).
    
    Example:
        POST /api/officer/tenders
        Body: {"title": "Procurement for IT Equipment", "version_number": "1.0"}
        Returns: Tender details with status=draft
    """
    officer = get_user_from_request(request)
    officer_id = officer["id"]
    if not officer_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Get officer to get organization
    officer = db.query(User).filter(User.id == officer_id).first()
    if not officer:
        raise HTTPException(status_code=404, detail="Officer not found")
    
    # Create tender using service
    tender = TenderService.create_tender(
        db=db,
        title=body.title,
        description=body.description,
        deadline=body.deadline,
        created_by_id=str(officer.id),
        organization_id=str(officer.organization_id or officer.id),
        version_number=body.version_number,
        required_documents=body.required_documents,
        source_document_path=body.source_document_path,
    )
    
    return TenderResponse(
        id=str(tender.id),
        title=tender.title,
        status=tender.status,
        created_by=str(tender.created_by),
        organization_id=str(tender.organization_id),
        version_number=body.version_number,
        created_at=tender.created_at.isoformat() if tender.created_at else None,
    )


@app.post("/api/officer/tenders/{tender_id}/publish", response_model=TenderResponse)
def publish_tender(
    tender_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Publish a draft tender (officer only).
    
    Example:
        POST /api/officer/tenders/550e8400-e29b-41d4-a716-446655440000/publish
        Returns: Updated tender with status=published and published_at timestamp
    """
    officer = get_user_from_request(request)
    officer_id = officer["id"]
    if not officer_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        tender = TenderService.publish_tender(db, tender_id, str(officer_id))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    return TenderResponse(
        id=str(tender.id),
        title=tender.title,
        status=tender.status,
        created_by=str(tender.created_by),
        organization_id=str(tender.organization_id),
        created_at=tender.created_at.isoformat() if tender.created_at else None,
    )


@app.get("/api/officer/tenders", response_model=List[TenderResponse])
def list_officer_tenders(
    request: Request,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List tenders created by authenticated officer.
    
    Example:
        GET /api/officer/tenders?limit=20&offset=0
        Returns: List of tenders created by this officer
    """
    officer = get_user_from_request(request)
    officer_id = officer["id"]
    if not officer_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    tenders = TenderService.list_officer_tenders(db, str(officer_id), limit, offset)
    
    return [
        TenderResponse(
            id=str(t.id),
            title=t.title,
            status=t.status,
            created_by=str(t.created_by),
            organization_id=str(t.organization_id),
            version_number="1.0",  # Default to 1.0
            created_at=t.created_at.isoformat() if t.created_at else None,
        )
        for t in tenders
    ]


@app.get("/api/bidder/tenders", response_model=List[TenderResponse])
def list_published_tenders(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List all published tenders (public endpoint, no auth required).
    
    Example:
        GET /api/bidder/tenders?limit=20&offset=0
        Returns: List of published tenders
    """
    tenders = TenderService.list_published_tenders(db, limit, offset)
    
    return [
        TenderResponse(
            id=str(t.id),
            title=t.title,
            status=t.status,
            created_by=str(t.created_by),
            organization_id=str(t.organization_id),
            version_number="1.0",
            created_at=t.created_at.isoformat() if t.created_at else None,
        )
        for t in tenders
    ]


@app.get("/api/bidder/tenders/{tender_id}", response_model=TenderResponse)
def get_tender_detail(
    tender_id: str,
    db: Session = Depends(get_db)
):
    """Get tender details including required documents (public endpoint).
    
    Example:
        GET /api/bidder/tenders/550e8400-e29b-41d4-a716-446655440000
        Returns: Full tender details
    """
    tender_details = TenderService.get_tender_with_details(db, tender_id)
    if not tender_details:
        raise HTTPException(status_code=404, detail="Tender not found")
    
    return TenderResponse(**tender_details)


@app.post("/api/bidder/tenders/{tender_id}/bids", response_model=BidResponse, status_code=201)
@require_role("bidder")
def create_bid(
    tender_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Create a new bid for a tender (bidder only).
    
    Example:
        POST /api/bidder/tenders/550e8400-e29b-41d4-a716-446655440000/bids
        Returns: New bid in DRAFT state
    """
    bidder = get_user_from_request(request)
    bidder_id = bidder["id"]
    if not bidder_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Get bidder to get organization
    bidder = db.query(User).filter(User.id == bidder_id).first()
    if not bidder or not bidder.organization_id:
        raise HTTPException(status_code=400, detail="Bidder organization not found")
    
    # Get tender version
    tender_version = TenderService.get_latest_tender_version(db, tender_id)
    if not tender_version:
        # If no published version, get any version
        tender_version = (
            db.query(TenderVersion)
            .filter(TenderVersion.tender_id == tender_id)
            .first()
        )
    
    if not tender_version:
        raise HTTPException(status_code=404, detail="Tender not found")
    
    # Check if bidder already has a draft bid
    existing_bid = (
        db.query(Bid)
        .filter(
            Bid.tender_version_id == tender_version.id,
            Bid.bidder_org_id == bidder.organization_id,
            Bid.status == "draft"
        )
        .first()
    )
    
    if existing_bid:
        raise HTTPException(
            status_code=409,
            detail="You already have a draft bid for this tender"
        )
    
    # Create bid using service
    bid = BidService.create_bid(
        db=db,
        tender_version_id=str(tender_version.id),
        bidder_org_id=str(bidder.organization_id),
        actor_id=str(bidder.id),
    )
    
    return BidResponse(
        id=str(bid.id),
        tender_id=str(tender_version.tender_id),
        tender_version_id=str(bid.tender_version_id),
        bidder_org_id=str(bid.bidder_org_id),
        status=bid.status,
        current_state=bid.current_state or "DRAFT",
        created_at=bid.created_at.isoformat() if bid.created_at else None,
    )


@app.get("/api/bidder/bids", response_model=List[BidResponse])
def list_bidder_bids(
    request: Request,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List bids for authenticated bidder (bidder only).
    
    Example:
        GET /api/bidder/bids?limit=20&offset=0
        Returns: List of bidder's bids
    """
    bidder = get_user_from_request(request)
    bidder_id = bidder["id"]
    if not bidder_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Get bidder to get organization
    bidder = db.query(User).filter(User.id == bidder_id).first()
    if not bidder or not bidder.organization_id:
        raise HTTPException(status_code=400, detail="Bidder organization not found")
    
    bids = (
        db.query(Bid)
        .filter(Bid.bidder_org_id == bidder.organization_id)
        .order_by(Bid.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    return [
        BidResponse(
            id=str(bid.id),
            tender_id=str(bid.tender_version.tender_id) if bid.tender_version else None,
            tender_version_id=str(bid.tender_version_id),
            bidder_org_id=str(bid.bidder_org_id),
            status=bid.status,
            current_state=bid.current_state or "DRAFT",
            created_at=bid.created_at.isoformat() if bid.created_at else None,
        )
        for bid in bids
    ]

class CreateTenderRequest(BaseModel):
    title: str
    version_number: str = "1.0"
    source_document_path: str = "/uploads/tender.pdf"

@app.post("/api/officer/tenders")
@require_role("officer")
def create_tender(body: CreateTenderRequest, request: Request, db: Session = Depends(get_db)):
    """Officer creates a new tender (DRAFT state) - Phase 0."""
    officer = request.state.user
    
    tender = Tender(
        title=body.title,
        created_by=uuid.UUID(officer["id"]),
        status="draft",
    )
    db.add(tender)
    db.flush()
    
    version = TenderVersion(
        tender_id=tender.id,
        version_number=body.version_number,
        source_document_path=body.source_document_path,
        precedence_policy_version="default_v1",
    )
    db.add(version)
    db.flush()
    
    BidService._log_audit_event(
        db,
        "TENDER_CREATED",
        "tender",
        str(tender.id),
        officer["id"],
        {"title": body.title, "version": body.version_number},
    )
    db.commit()
    
    return {
        "id": str(tender.id),
        "title": tender.title,
        "status": tender.status,
        "version_id": str(version.id),
        "version_number": version.version_number,
    }

@app.post("/api/officer/tenders/{tender_id}/publish")
@require_role("officer")
def publish_tender(tender_id: str, request: Request, db: Session = Depends(get_db)):
    """Officer publishes a tender (DRAFT → PUBLISHED) - Phase 0."""
    officer = request.state.user
    
    tender_id_uuid = uuid.UUID(tender_id) if isinstance(tender_id, str) else tender_id
    tender = db.query(Tender).filter(Tender.id == tender_id_uuid).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    
    tender.status = "published"
    
    version = db.query(TenderVersion).filter(TenderVersion.tender_id == tender_id_uuid).first()
    if version:
        version.published_at = datetime.utcnow()
    
    db.flush()
    
    BidService._log_audit_event(
        db,
        "TENDER_PUBLISHED",
        "tender",
        str(tender.id),
        officer["id"],
        {"version_id": str(version.id) if version else None},
    )
    db.commit()
    
    return {
        "id": str(tender.id),
        "title": tender.title,
        "status": tender.status,
        "published_at": version.published_at.isoformat() if version and version.published_at else None,
    }

@app.get("/api/officer/tenders")
@require_role("officer")
def list_officer_tenders(request: Request, db: Session = Depends(get_db)):
    """Officer lists all tenders they created."""
    officer = request.state.user
    officer_id = uuid.UUID(officer["id"])
    
    tenders = db.query(Tender).filter(Tender.created_by == officer_id).all()
    
    result = []
    for tender in tenders:
        version = db.query(TenderVersion).filter(TenderVersion.tender_id == tender.id).first()
        result.append({
            "id": str(tender.id),
            "title": tender.title,
            "status": tender.status,
            "version_number": version.version_number if version else "1.0",
            "created_at": tender.created_at.isoformat() if tender.created_at else None,
            "published_at": version.published_at.isoformat() if version and version.published_at else None,
        })
    
    return result

@app.get("/api/tenders")
def list_tenders(db: Session = Depends(get_db)):
    """List all published tenders - Phase 0."""
    tenders = db.query(Tender).filter(Tender.status == "published").all()
    
    result = []
    for tender in tenders:
        version = db.query(TenderVersion).filter(
            TenderVersion.tender_id == tender.id,
            TenderVersion.published_at != None,
        ).order_by(TenderVersion.version_number.desc()).first()
        
        result.append({
            "id": str(tender.id),
            "title": tender.title,
            "status": tender.status,
            "version_id": str(version.id) if version else None,
            "version_number": version.version_number if version else "1.0",
            "published_at": version.published_at.isoformat() if version and version.published_at else None,
        })
    
    return result

# ============================================================================
# PHASE 0 & 1: BID ENDPOINTS (Officer)
# ============================================================================

@app.get("/api/officer/bids")
@require_role("officer")
def list_bids_officer(request: Request, db: Session = Depends(get_db)):
    """Officer views all bids with enriched data including org, risk, compliance - Phase 2."""
    from app.models.models import Organization, TenderVersion, Tender
    
    try:
        bids = BidService.list_all_bids(db)
    except Exception as e:
        logger.error(f"Error listing bids: {str(e)}")
        return []
    
    result = []
    for bid in bids:
        try:
            # Get bidder organization
            bidder_org = None
            try:
                bidder_org = db.query(Organization).filter(Organization.id == bid.bidder_org_id).first()
            except Exception as e:
                logger.error(f"Error querying bidder org: {str(e)}")
                db.rollback()
                bidder_org = None
            
            # Get tender info via tender_version
            tender_version = None
            tender = None
            tender_org = None
            try:
                tender_version = db.query(TenderVersion).filter(TenderVersion.id == bid.tender_version_id).first()
                if tender_version:
                    tender = db.query(Tender).filter(Tender.id == tender_version.tender_id).first()
                    if tender:
                        tender_org = db.query(Organization).filter(Organization.id == tender.organization_id).first()
            except Exception as e:
                logger.error(f"Error querying tender info: {str(e)}")
                db.rollback()
                tender_version = None
                tender = None
                tender_org = None
            
            # Get latest compliance result
            compliance_status = "PENDING"
            try:
                compliance = db.query(ComplianceResult).filter(ComplianceResult.bid_id == bid.id).order_by(ComplianceResult.evaluated_at.desc()).first()
                if compliance:
                    compliance_status = compliance.explanation or "PENDING"
            except Exception as e:
                logger.debug(f"No compliance result for bid {bid.id}: {str(e)}")
                db.rollback()
                compliance_status = "PENDING"
            
            # Get latest risk assessment
            risk_level = "UNKNOWN"
            risk_score = 0
            try:
                risk = db.query(RiskAssessment).filter(RiskAssessment.bid_id == bid.id).order_by(RiskAssessment.assessed_at.desc()).first()
                if risk:
                    risk_score = float(risk.overall_risk_score or 0)
                    risk_level = risk.risk_level
            except Exception as e:
                logger.debug(f"No risk assessment for bid {bid.id}: {str(e)}")
                db.rollback()
                risk_level = "UNKNOWN"
                risk_score = 0
            
            # Get latest officer decision
            decision_text = "PENDING"
            try:
                decision = db.query(OfficerDecision).filter(OfficerDecision.bid_id == bid.id).order_by(OfficerDecision.decided_at.desc()).first()
                if decision:
                    decision_text = decision.decision or "PENDING"
            except Exception as e:
                logger.debug(f"No officer decision for bid {bid.id}: {str(e)}")
                db.rollback()
                decision_text = "PENDING"
            
            result.append({
                "bid_id": str(bid.id),
                "id": str(bid.id),
                "tender_version_id": str(bid.tender_version_id),
                "bidder_org_id": str(bid.bidder_org_id),
                "bidder_org_name": bidder_org.legal_name if bidder_org else "Unknown Bidder",
                "gstin": bidder_org.gstin if bidder_org else None,
                "udyam": bidder_org.udyam_number if bidder_org else None,
                "pan": bidder_org.pan if bidder_org else None,
                "tender": {
                    "title": tender.title if tender else "Unknown Tender",
                    "organization": tender_org.legal_name if tender_org else "Unknown Organization"
                } if tender else {"title": "Unknown", "organization": "Unknown"},
                "status": bid.status,
                "current_state": bid.current_state,
                "compliance_status": compliance_status,
                "risk_level": risk_level,
                "risk_score": risk_score,
                "decision": decision_text,
                "submitted_at": bid.submitted_at.isoformat() if bid.submitted_at else None,
                "created_at": bid.created_at.isoformat() if bid.created_at else None,
            })
        except Exception as e:
            logger.error(f"Error processing bid {bid.id}: {str(e)}")
            db.rollback()
            continue
    
    return result

@app.get("/api/officer/bids/{bid_id}")
@require_role("officer")
def get_bid_detail_officer(bid_id: str, request: Request, db: Session = Depends(get_db)):
    """Officer views bid details with compliance and risk - Phase 0+."""
    bid = BidService.get_bid(db, bid_id)
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    documents = BidService.get_documents(db, bid_id)
    compliance = ComplianceService.get_bid_compliance(db, bid_id)
    compliance_summary = ComplianceService.compute_bid_compliance_summary(db, bid_id)
    risk_assessment = RiskService.get_bid_risk_assessment(db, bid_id)
    clarifications = ClarificationService.get_bid_requests(db, bid_id)
    state_history = BidStateMachine.get_state_history(db, bid_id)
    decision = OfficerDecisionService.get_bid_decision(db, bid_id)
    
    # Safely extract risk assessment data
    risk_data = {
        "total_score": 0,
        "risk_level": "UNKNOWN",
        "signals": []
    }
    if risk_assessment:
        try:
            # Handle both old and new schema
            total_score = getattr(risk_assessment, 'total_score', None) or getattr(risk_assessment, 'overall_risk_score', 0)
            risk_level = getattr(risk_assessment, 'risk_level', None)
            if not risk_level and hasattr(risk_assessment, 'overall_risk_score'):
                # Derive from score
                score_val = float(total_score or 0)
                if score_val < 30:
                    risk_level = "LOW"
                elif score_val < 70:
                    risk_level = "MEDIUM"
                else:
                    risk_level = "HIGH"
            risk_data = {
                "total_score": float(total_score or 0),
                "risk_level": risk_level or "UNKNOWN",
                "signals": []
            }
        except Exception as e:
            logger.debug(f"Error extracting risk data: {str(e)}")
    
    # Safely extract decision data
    decision_data = {
        "id": None,
        "final_decision": "PENDING",
        "decided_at": None,
        "reason": None,
    }
    if decision:
        try:
            # Handle both old and new schema
            final_decision = getattr(decision, 'final_decision', None) or getattr(decision, 'decision', 'PENDING')
            decision_data = {
                "id": str(decision.id),
                "final_decision": final_decision,
                "decided_at": decision.decided_at.isoformat() if hasattr(decision, 'decided_at') and decision.decided_at else None,
                "reason": getattr(decision, 'reason', None) or getattr(decision, 'override_reason', None),
            }
        except Exception as e:
            logger.debug(f"Error extracting decision data: {str(e)}")
    
    return {
        "id": str(bid.id),
        "tender_version_id": str(bid.tender_version_id),
        "bidder_org_id": str(bid.bidder_org_id),
        "status": bid.status,
        "current_state": bid.current_state,
        "state_history": state_history,
        "submitted_at": bid.submitted_at.isoformat() if bid.submitted_at else None,
        "documents": [
            {
                "id": str(doc.id),
                "doc_type": doc.doc_type,
                "file_hash": doc.file_hash,
                "ocr_status": doc.ocr_status,
                "current_version": doc.current_version,
                "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
            }
            for doc in documents
        ],
        "compliance": compliance_summary,
        "risk_assessment": risk_data,  # Changed from "risk" to "risk_assessment"
        "compliance_results": compliance or [],  # Include compliance results for clause-by-clause display
        "ai_recommendation": "REVIEW",  # Default recommendation
        "clarifications": [
            {
                "id": str(c.id),
                "status": c.status,
                "question": c.question_text,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in clarifications
        ],
        "decision": decision_data,
        "compliance_status": compliance_summary.get("overall", "PENDING") if compliance_summary else "PENDING",
    }

# ============================================================================
# PHASE 0 & 1: BID ENDPOINTS (Bidder)
# ============================================================================

@app.get("/api/bidder/tenders")
@require_role("bidder")
def list_tenders_bidder(request: Request, db: Session = Depends(get_db)):
    """Bidder views published tenders - Phase 0."""
    tenders = db.query(Tender).filter(Tender.status == "published").all()
    
    result = []
    for tender in tenders:
        version = db.query(TenderVersion).filter(
            TenderVersion.tender_id == tender.id,
            TenderVersion.published_at != None,
        ).order_by(TenderVersion.version_number.desc()).first()
        
        result.append({
            "id": str(tender.id),
            "title": tender.title,
            "status": tender.status,
            "organization": tender.created_by or "Government of India",
            "version": version.version_number if version else "1.0",
            "version_id": str(version.id) if version else None,
            "clause_count": 3,
            "required_documents": ["GST_CERT", "PAN", "COMPANY_REG"],
            "published_at": version.published_at.isoformat() if version and version.published_at else None,
        })
    
    return result

@app.get("/api/bidder/tenders/{tender_id}")
@require_role("bidder")
def get_tender_detail_bidder(tender_id: str, request: Request, db: Session = Depends(get_db)):
    """Bidder views tender details - Phase 0."""
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    
    version = db.query(TenderVersion).filter(
        TenderVersion.tender_id == tender_id,
        TenderVersion.published_at != None,
    ).order_by(TenderVersion.version_number.desc()).first()
    
    if not version:
        raise HTTPException(status_code=404, detail="No published version found")
    
    return {
        "id": str(tender.id),
        "title": tender.title,
        "status": tender.status,
        "organization": tender.created_by or "Government of India",
        "version": version.version_number if version else "1.0",
        "version_id": str(version.id) if version else None,
        "clause_count": 3,
        "required_documents": ["GST_CERT", "PAN", "COMPANY_REG"],
        "published_at": version.published_at.isoformat() if version and version.published_at else None,
    }



@app.put("/api/bidder/bids/{bid_id}")
@require_role("bidder")
def update_bid(bid_id: str, body: dict, request: Request, db: Session = Depends(get_db)):
    """Bidder updates their bid details (only before submission) - Phase 2."""
    bidder = request.state.user
    
    bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
    bid = db.query(Bid).filter(Bid.id == bid_id_uuid).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    # Verify ownership
    bidder_id_uuid = uuid.UUID(bidder["id"]) if isinstance(bidder["id"], str) else bidder["id"]
    user = db.query(User).filter(User.id == bidder_id_uuid).first()
    if not user or bid.bidder_org_id != user.organization_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this bid")
    
    # Only allow updates before submission
    if bid.status not in ["DRAFT", "SUBMITTED"]:
        raise HTTPException(status_code=400, detail="Bid cannot be edited after submission")
    
    # Update allowed fields
    if "bidder_org_name" in body:
        bid.bidder_org_name = body["bidder_org_name"]
    if "bid_amount" in body:
        bid.bid_amount = body["bid_amount"]
    if "delivery_location" in body:
        bid.delivery_location = body["delivery_location"]
    if "technical_specs" in body:
        bid.technical_specs = body["technical_specs"]
    
    db.commit()
    db.refresh(bid)
    
    return {
        "status": "success",
        "message": "Bid updated successfully",
        "bid_id": str(bid_id_uuid),
        "bidder_org_name": bid.bidder_org_name,
        "bid_amount": bid.bid_amount,
        "delivery_location": bid.delivery_location,
        "technical_specs": bid.technical_specs,
    }

@app.get("/api/bidder/bids")
@require_role("bidder")
def list_bids_bidder(request: Request, db: Session = Depends(get_db)):
    """Bidder views their own bids - Phase 0."""
    bidder = request.state.user
    
    bidder_id_uuid = uuid.UUID(bidder["id"]) if isinstance(bidder["id"], str) else bidder["id"]
    user = db.query(User).filter(User.id == bidder_id_uuid).first()
    if not user or not user.organization_id:
        raise HTTPException(status_code=400, detail="User not associated with organization")
    
    bids = BidService.list_bids_for_org(db, str(user.organization_id))
    
    return [
        {
            "id": str(bid.id),
            "tender_version_id": str(bid.tender_version_id),
            "status": bid.status,
            "current_state": bid.current_state,
            "submitted_at": bid.submitted_at.isoformat() if bid.submitted_at else None,
            "created_at": bid.created_at.isoformat() if bid.created_at else None,
        }
        for bid in bids
    ]

@app.get("/api/bidder/bids/{bid_id}")
@require_role("bidder")
def get_bid_detail_bidder(bid_id: str, request: Request, db: Session = Depends(get_db)):
    """Bidder views their bid details with document versioning - Phase 0+1."""
    bidder = request.state.user
    
    bid = BidService.get_bid(db, bid_id)
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    # Verify ownership
    bidder_id_uuid = uuid.UUID(bidder["id"]) if isinstance(bidder["id"], str) else bidder["id"]
    user = db.query(User).filter(User.id == bidder_id_uuid).first()
    if not user or bid.bidder_org_id != user.organization_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this bid")
    
    documents = BidService.get_documents(db, bid_id)
    clarifications_pending = ClarificationService.get_pending_requests(db, bid_id)
    state_history = BidStateMachine.get_state_history(db, bid_id)
    
    return {
        "id": str(bid.id),
        "tender_version_id": str(bid.tender_version_id),
        "status": bid.status,
        "current_state": bid.current_state,
        "state_history": state_history,
        "submitted_at": bid.submitted_at.isoformat() if bid.submitted_at else None,
        "documents": [
            {
                "id": str(doc.id),
                "doc_type": doc.doc_type,
                "file_hash": doc.file_hash,
                "ocr_status": doc.ocr_status,
                "current_version": doc.current_version,
                "version_history": DocumentService.get_version_history(db, str(doc.id)),
                "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
            }
            for doc in documents
        ],
        "clarifications_pending": len(clarifications_pending),
    }

# ============================================================================
# PHASE 1: STATE MACHINE
# ============================================================================

class BidStateTransitionRequest(BaseModel):
    new_state: str
    metadata: Optional[Dict[str, Any]] = None

@app.post("/api/bids/{bid_id}/state/transition")
@require_role("officer", "bidder")
def transition_bid_state(
    bid_id: str,
    body: BidStateTransitionRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Transition bid state - Phase 1."""
    user = request.state.user
    
    try:
        bid = BidStateMachine.transition(
            db,
            bid_id,
            body.new_state,
            user["id"],
            body.metadata,
        )
        
        return {
            "id": str(bid.id),
            "current_state": bid.current_state,
            "state_entered_at": bid.state_entered_at.isoformat() if bid.state_entered_at else None,
            "metadata": bid.state_metadata,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/bids/{bid_id}/state/history")
def get_bid_state_history(bid_id: str, request: Request, db: Session = Depends(get_db)):
    """Get bid state transition history - Phase 1."""
    history = BidStateMachine.get_state_history(db, bid_id)
    if not history:
        raise HTTPException(status_code=404, detail="Bid not found")
    return {"bid_id": bid_id, "state_history": history}

# ============================================================================
# PHASE 1: DOCUMENT VERSIONING
# ============================================================================

@app.post("/api/bidder/bids/{bid_id}/documents")
@require_role("bidder")
async def upload_document(
    bid_id: str,
    doc_type: str,
    file: UploadFile = File(...),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Upload document with versioning - Phase 1."""
    bidder = request.state.user
    
    # Verify ownership
    bid = BidService.get_bid(db, bid_id)
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    bidder_id_uuid = uuid.UUID(bidder["id"]) if isinstance(bidder["id"], str) else bidder["id"]
    user = db.query(User).filter(User.id == bidder_id_uuid).first()
    if not user or bid.bidder_org_id != user.organization_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Read file and compute hash
    contents = await file.read()
    file_hash = hashlib.sha256(contents).hexdigest()
    
    # Store file (mock)
    file_path = f"/uploads/bids/{bid_id}/{doc_type}_{uuid.uuid4()}.pdf"
    
    # Create or upload new version
    existing_doc = db.query(Document).filter(
        Document.bid_id == bid_id,
        Document.doc_type == doc_type,
    ).first()
    
    if existing_doc:
        # Upload new version
        version = DocumentService.upload_new_version(
            db,
            str(existing_doc.id),
            file_path,
            file_hash,
            bidder["id"],
            "Updated by bidder",
        )
        document_id = existing_doc.id
    else:
        # Create new document
        doc = DocumentService.create_document(
            db,
            bid_id,
            file_path,
            file_hash,
            doc_type,
            bidder["id"],
            "Initial upload",
        )
        document_id = doc.id
        version = db.query(DocumentVersion).filter(
            DocumentVersion.document_id == doc.id,
            DocumentVersion.version_number == 1,
        ).first()
    
    return {
        "document_id": str(document_id),
        "doc_type": doc_type,
        "version_number": version.version_number if version else 1,
        "file_hash": file_hash,
        "ocr_status": "PENDING",
        "uploaded_at": datetime.utcnow().isoformat(),
    }

@app.get("/api/bidder/bids/{bid_id}/documents")
@require_role("bidder")
def get_bid_documents(bid_id: str, request: Request, db: Session = Depends(get_db)):
    """Get bid documents with version history - Phase 1."""
    bidder = request.state.user
    
    bid = BidService.get_bid(db, bid_id)
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    bidder_id_uuid = uuid.UUID(bidder["id"]) if isinstance(bidder["id"], str) else bidder["id"]
    user = db.query(User).filter(User.id == bidder_id_uuid).first()
    if not user or bid.bidder_org_id != user.organization_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    documents = BidService.get_documents(db, bid_id)
    
    return [
        {
            "id": str(doc.id),
            "doc_type": doc.doc_type,
            "current_version": doc.current_version,
            "ocr_status": doc.ocr_status,
            "version_history": DocumentService.get_version_history(db, str(doc.id)),
            "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
        }
        for doc in documents
    ]

@app.post("/api/bidder/bids/{bid_id}/submit")
@require_role("bidder")
def submit_bid(bid_id: str, request: Request, db: Session = Depends(get_db)):
    """Bidder submits bid (DRAFT → SUBMITTED) - Phase 1."""
    bidder = request.state.user
    
    bid = BidService.get_bid(db, bid_id)
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    bidder_id_uuid = uuid.UUID(bidder["id"]) if isinstance(bidder["id"], str) else bidder["id"]
    user = db.query(User).filter(User.id == bidder_id_uuid).first()
    if not user or bid.bidder_org_id != user.organization_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Transition state
    updated_bid = BidStateMachine.transition(
        db,
        bid_id,
        BidStatus.SUBMITTED,
        str(bidder_id_uuid),
        {"submitted_via_api": True},
    )
    
    return {
        "id": str(updated_bid.id),
        "status": updated_bid.status,
        "current_state": updated_bid.current_state,
        "submitted_at": datetime.utcnow().isoformat(),
    }

# ============================================================================
# PHASE 2: BIDDER VERIFICATION & READINESS
# ============================================================================

@app.post("/api/bidder/bids/{bid_id}/verify-stage1")
@require_role("bidder")
def verify_bid_stage1(bid_id: str, request: Request, db: Session = Depends(get_db)):
    """Bidder Stage 1 verification - validate uploaded documents - Phase 2."""
    bidder = request.state.user
    
    bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
    bid = db.query(Bid).filter(Bid.id == bid_id_uuid).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    user = db.query(User).filter(User.id == bidder["id"]).first()
    if not user or bid.bidder_org_id != user.organization_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check documents
    documents = db.query(Document).filter(Document.bid_id == bid_id_uuid).all()
    doc_types_uploaded = {doc.doc_type for doc in documents}
    
    # Get tender requirements
    tender = bid.tender
    required_docs = {"GST", "PAN", "CERTIFICATE_OF_INCORPORATION"}  # Mock requirement
    
    uploaded_mandatory = len(doc_types_uploaded & required_docs)
    total_mandatory = len(required_docs)
    
    return {
        "passed": uploaded_mandatory == total_mandatory,
        "slots": [
            {"type": doc_type, "uploaded": doc_type in doc_types_uploaded}
            for doc_type in required_docs
        ],
        "uploaded_mandatory": uploaded_mandatory,
        "total_mandatory": total_mandatory,
    }

@app.post("/api/bidder/bids/{bid_id}/verify-stage2")
@require_role("bidder")
def verify_bid_stage2(bid_id: str, request: Request, db: Session = Depends(get_db)):
    """Bidder Stage 2 verification - eligibility checks - Phase 2."""
    bidder = request.state.user
    
    bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
    bid = db.query(Bid).filter(Bid.id == bid_id_uuid).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    user = db.query(User).filter(User.id == bidder["id"]).first()
    if not user or bid.bidder_org_id != user.organization_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Run eligibility checks
    compliance_results = []
    
    # Mock compliance checks
    checks = [
        {"rule": "Must be registered on GeM", "passed": True},
        {"rule": "No pending litigation", "passed": True},
        {"rule": "Valid GST certificate", "passed": True},
    ]
    
    passed = all(c["passed"] for c in checks)
    
    return {
        "compliance_status": "COMPLIANT" if passed else "NON_COMPLIANT",
        "ai_recommendation": "PROCEED_TO_SUBMISSION" if passed else "DO_NOT_PROCEED",
        "clause_results": checks,
        "risk_assessment": {
            "overall_risk": "LOW" if passed else "HIGH",
            "risk_factors": [] if passed else ["Compliance failure"],
        },
    }

@app.get("/api/bidder/bids/{bid_id}/readiness")
@require_role("bidder")
def get_bid_readiness(bid_id: str, request: Request, db: Session = Depends(get_db)):
    """Get bid readiness compliance check - Phase 2."""
    bidder = request.state.user
    
    bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
    bid = db.query(Bid).filter(Bid.id == bid_id_uuid).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    user = db.query(User).filter(User.id == bidder["id"]).first()
    if not user or bid.bidder_org_id != user.organization_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Calculate readiness
    documents = db.query(Document).filter(Document.bid_id == bid_id_uuid).all()
    
    requirements = [
        {"requirement": "GST Certificate", "status": any(d.doc_type == "GST" for d in documents), "evidence": len([d for d in documents if d.doc_type == "GST"])},
        {"requirement": "PAN Card", "status": any(d.doc_type == "PAN" for d in documents), "evidence": len([d for d in documents if d.doc_type == "PAN"])},
        {"requirement": "Certificate of Incorporation", "status": any(d.doc_type == "CERTIFICATE_OF_INCORPORATION" for d in documents), "evidence": len([d for d in documents if d.doc_type == "CERTIFICATE_OF_INCORPORATION"])},
    ]
    
    satisfied = sum(1 for r in requirements if r["status"])
    total = len(requirements)
    readiness_percent = int((satisfied / total) * 100) if total > 0 else 0
    
    return {
        "readiness_percent": readiness_percent,
        "items": [
            {
                "requirement": r["requirement"],
                "status": "SATISFIED" if r["status"] else "MISSING",
                "evidence_count": r["evidence"],
            }
            for r in requirements
        ],
        "tender": {
            "id": str(bid.tender_version_id),
            "title": bid.tender.title if bid.tender else "Unknown",
            "version": "1.0",
        },
    }

@app.get("/api/bidder/bids/{bid_id}/status")
@require_role("bidder")
def get_bid_status(bid_id: str, request: Request, db: Session = Depends(get_db)):
    """Get detailed bid status with decision and compliance tracking - Phase 2."""
    bidder = request.state.user
    
    bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
    bid = db.query(Bid).filter(Bid.id == bid_id_uuid).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    user = db.query(User).filter(User.id == bidder["id"]).first()
    if not user or bid.bidder_org_id != user.organization_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get decision if exists
    decision_record = db.query(OfficerDecision).filter(OfficerDecision.bid_id == bid_id_uuid).first()
    
    return {
        "status": bid.status,
        "decision": {
            "final_decision": decision_record.decision if decision_record else "PENDING",
            "decided_at": decision_record.decided_at.isoformat() if decision_record else None,
            "reason": decision_record.reason if decision_record else None,
        } if decision_record else {"final_decision": "PENDING", "decided_at": None, "reason": None},
        "compliance_status": "PENDING",
        "risk_level": "LOW",
        "officer_notes": [],
        "document_flags": [],
        "tender": {
            "id": str(bid.tender_version_id),
            "title": bid.tender.title if bid.tender else "Unknown",
            "organization": "Government of India",
            "version": "1.0",
        },
        "submitted_at": bid.submitted_at.isoformat() if bid.submitted_at else None,
        "current_step": "EVALUATION" if bid.status == "SUBMITTED" else bid.status,
    }

# ============================================================================
# PHASE 3: OCR & EXTRACTION
# ============================================================================

@app.post("/api/bidder/bids/{bid_id}/documents/upload")
@require_role("bidder")
async def upload_bid_document(
    bid_id: str,
    doc_type: str,
    file: UploadFile = File(...),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Upload document with validation, hashing, and OCR queueing - Phase 3."""
    bidder = request.state.user
    
    # Verify bid exists and belongs to bidder
    bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
    bid = db.query(Bid).filter(Bid.id == bid_id_uuid).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    bidder_id_uuid = uuid.UUID(bidder["id"]) if isinstance(bidder["id"], str) else bidder["id"]
    user = db.query(User).filter(User.id == bidder_id_uuid).first()
    if not user or bid.bidder_org_id != user.organization_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Read and validate file
    contents = await file.read()
    is_valid, error_msg = DocumentService.validate_file_upload(contents, file.filename)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"File validation failed: {error_msg}")
    
    # Compute file hash
    file_hash = DocumentService.compute_file_hash(contents)
    
    # Store file (mock file path)
    file_path = f"/uploads/bids/{bid_id}/{doc_type}_{uuid.uuid4()}.{file.filename.split('.')[-1]}"
    
    # Create or upload new version
    existing_doc = db.query(Document).filter(
        Document.bid_id == bid_id_uuid,
        Document.doc_type == doc_type,
    ).first()
    
    if existing_doc:
        # Upload new version
        version = DocumentService.upload_new_version(
            db,
            str(existing_doc.id),
            file_path,
            file_hash,
            bidder["id"],
            f"Updated {doc_type} document",
        )
        document_id = existing_doc.id
    else:
        # Create new document
        doc = DocumentService.create_document(
            db,
            bid_id,
            file_path,
            file_hash,
            doc_type,
            bidder["id"],
            f"Initial {doc_type} upload",
        )
        document_id = doc.id
        version = db.query(DocumentVersion).filter(
            DocumentVersion.document_id == doc.id,
            DocumentVersion.version_number == 1,
        ).first()
    
    # Enqueue OCR job
    ocr_job = DocumentService.enqueue_ocr_job(
        db,
        str(document_id),
        bidder["id"],
    )
    
    from app.schemas.common import DocumentUploadResponse
    return DocumentUploadResponse(
        document_id=str(document_id),
        version_number=version.version_number,
        file_hash=file_hash,
        ocr_job_id=str(ocr_job.id),
        message=f"Document uploaded and queued for OCR processing"
    )


@app.get("/api/bidder/bids/{bid_id}/documents/list")
@require_role("bidder")
def list_bid_documents_v2(bid_id: str, request: Request = None, db: Session = Depends(get_db)):
    """List all documents for a bid with OCR status - Phase 3."""
    bidder = request.state.user
    
    bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
    bid = db.query(Bid).filter(Bid.id == bid_id_uuid).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    bidder_id_uuid = uuid.UUID(bidder["id"]) if isinstance(bidder["id"], str) else bidder["id"]
    user = db.query(User).filter(User.id == bidder_id_uuid).first()
    if not user or bid.bidder_org_id != user.organization_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    documents = db.query(Document).filter(Document.bid_id == bid_id_uuid).all()
    
    result = []
    for doc in documents:
        ocr_status = DocumentService.get_ocr_job_status(db, str(doc.id))
        result.append({
            "id": str(doc.id),
            "doc_type": doc.doc_type,
            "current_version": doc.current_version,
            "file_hash": doc.file_hash,
            "ocr_status": doc.ocr_status,
            "ocr_job": ocr_status,
            "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
        })
    
    return result


@app.get("/api/bidder/documents/{doc_id}/ocr-status")
@require_role("bidder")
def get_document_ocr_status(doc_id: str, request: Request = None, db: Session = Depends(get_db)):
    """Poll OCR processing status for document - Phase 3."""
    bidder = request.state.user
    
    doc_id_uuid = uuid.UUID(doc_id) if isinstance(doc_id, str) else doc_id
    doc = db.query(Document).filter(Document.id == doc_id_uuid).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Verify authorization
    bidder_id_uuid = uuid.UUID(bidder["id"]) if isinstance(bidder["id"], str) else bidder["id"]
    user = db.query(User).filter(User.id == bidder_id_uuid).first()
    if not user or doc.bid_id:
        bid = db.query(Bid).filter(Bid.id == doc.bid_id).first()
        if not bid or bid.bidder_org_id != user.organization_id:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    ocr_status = DocumentService.get_ocr_job_status(db, str(doc_id))
    if not ocr_status:
        raise HTTPException(status_code=404, detail="No OCR job found for document")
    
    from app.schemas.common import OCRStatusResponse
    return OCRStatusResponse(
        job_id=ocr_status["job_id"],
        status=ocr_status["status"],
        version_number=ocr_status["version_number"],
        created_at=ocr_status["requested_at"] or "",
        completed_at=ocr_status["completed_at"],
        error_message=ocr_status["error_message"],
        extracted_text=ocr_status["extracted_text"],
        entities=ocr_status.get("entities"),
    )


@app.post("/api/bidder/bids/{bid_id}/verify-stage1")
@require_role("bidder")
def verify_bid_stage1_v2(bid_id: str, request: Request = None, db: Session = Depends(get_db)):
    """Verify Stage 1 (document slots) - Phase 3."""
    bidder = request.state.user
    
    bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
    bid = db.query(Bid).filter(Bid.id == bid_id_uuid).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    bidder_id_uuid = uuid.UUID(bidder["id"]) if isinstance(bidder["id"], str) else bidder["id"]
    user = db.query(User).filter(User.id == bidder_id_uuid).first()
    if not user or bid.bidder_org_id != user.organization_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get tender to check required documents
    tender = db.query(Tender).filter(Tender.id == bid.tender_id).first()
    required_docs = tender.required_documents if tender else []
    
    # Check which documents are uploaded
    uploaded_docs = db.query(Document).filter(Document.bid_id == bid_id_uuid).all()
    uploaded_types = {doc.doc_type for doc in uploaded_docs}
    
    # Check if all mandatory slots filled
    mandatory_slots = [doc for doc in required_docs if doc]  # Non-empty
    uploaded_mandatory = len([slot for slot in mandatory_slots if slot in uploaded_types])
    total_mandatory = len(mandatory_slots)
    
    passed = uploaded_mandatory == total_mandatory
    
    slots = [
        {
            "document_type": doc,
            "uploaded": doc in uploaded_types,
            "mandatory": True,
        }
        for doc in required_docs
    ]
    
    from app.schemas.common import Stage1VerificationResponse
    return Stage1VerificationResponse(
        passed=passed,
        slots=slots,
        uploaded_mandatory=uploaded_mandatory,
        total_mandatory=total_mandatory,
    )


@app.post("/api/officer/documents/{document_id}/ocr/process")
@require_role("officer")
def process_document_ocr(document_id: str, request: Request, db: Session = Depends(get_db)):
    """Trigger OCR processing on document - Phase 3."""
    officer = request.state.user
    
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Create OCR job
    job = DocumentService.enqueue_ocr_job(db, document_id, officer["id"])
    
    return {
        "job_id": str(job.id),
        "document_id": document_id,
        "status": job.status,
        "message": "OCR job enqueued for processing",
    }

@app.get("/api/officer/documents/{document_id}/ocr/status")
@require_role("officer")
def get_ocr_status(document_id: str, request: Request, db: Session = Depends(get_db)):
    """Get OCR processing status - Phase 3."""
    job = db.query(OCRJob).filter(
        OCRJob.document_id == document_id
    ).order_by(OCRJob.created_at.desc()).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="No OCR job found")
    
    return {
        "job_id": str(job.id),
        "status": job.status,
        "text_content": job.text_content,
        "confidence_score": float(job.confidence_score) if job.confidence_score else None,
        "error_message": job.error_message,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
    }

# ============================================================================
# PHASE 4: COMPLIANCE RULE ENGINE & EVIDENCE TRACEABILITY
# ============================================================================

@app.get("/api/compliance/rules")
@require_role("officer")
def list_compliance_rules(context: Optional[str] = None, request: Request = None, db: Session = Depends(get_db)):
    """List available compliance rules - Phase 4."""
    from app.services.compliance_rule_engine import ComplianceRuleEngine
    
    engine = ComplianceRuleEngine()
    rules = engine.list_rules(context)
    
    from app.schemas.common import ComplianceRuleResponse
    return [
        ComplianceRuleResponse(
            id=rule.id,
            name=rule.name,
            description=rule.description,
            rule_type=rule.rule_type.value,
            severity=rule.severity,
            version=rule.version,
            applicable_contexts=rule.applicable_contexts,
        )
        for rule in rules
    ]


@app.post("/api/officer/bids/{bid_id}/evaluate-compliance")
@require_role("officer")
def evaluate_bid_compliance(
    bid_id: str,
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Evaluate bid against compliance rules - Phase 4."""
    officer = request.state.user
    bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
    
    # Get bid
    bid = db.query(Bid).filter(Bid.id == bid_id_uuid).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    # Gather bid data
    documents = db.query(Document).filter(Document.bid_id == bid_id_uuid).all()
    extracted_facts = db.query(ExtractedFact).filter(
        ExtractedFact.bid_id == bid_id_uuid
    ).all() if hasattr(ExtractedFact, 'bid_id') else []
    
    bid_data = {
        "bid_id": str(bid_id_uuid),
        "organization_name": bid.bidder_org_id.hex if hasattr(bid.bidder_org_id, 'hex') else str(bid.bidder_org_id),
        "documents": [
            {
                "id": str(doc.id),
                "type": doc.doc_type,
                "version": doc.current_version,
            }
            for doc in documents
        ],
        "extracted_facts": [
            {
                "type": fact.fact_type,
                "value": fact.extracted_value,
                "confidence": float(fact.confidence_score) if fact.confidence_score else 0.0,
            }
            for fact in extracted_facts
        ],
    }
    
    # Prepare evidence data (placeholder for Phase 5 integrations)
    evidence_data = {
        "verification_status": "PENDING",
        "references": [str(doc.id) for doc in documents],
        "extracted_facts": {
            "company_name": next((f.extracted_value for f in extracted_facts if f.fact_type == "COMPANY_NAME"), None),
        },
    }
    
    # Evaluate using rule engine
    from app.services.compliance_rule_engine import ComplianceRuleEngine
    engine = ComplianceRuleEngine()
    
    evaluation_result = engine.evaluate_bid_compliance(
        bid_data,
        evidence_data,
        context="officer_review"
    )
    
    # Store compliance results for each rule
    for rule_result in evaluation_result.get("rule_results", []):
        compliance_record = ComplianceService.evaluate_compliance(
            db,
            str(bid_id_uuid),
            rule_result.get("rule_id"),
            "PASS" if rule_result.get("passed") else "FAIL",
            {
                "reasoning": rule_result.get("reasoning_chain", []),
                "rule_id": rule_result.get("rule_id"),
                "severity": rule_result.get("severity"),
            },
            rule_result.get("evidence_references", []),
            "1.0.0",
            officer["id"],
        )
    
    # Log audit event
    BidService._log_audit_event(
        db,
        "COMPLIANCE_EVALUATION_COMPLETED",
        str(bid_id_uuid),
        officer["id"],
        {
            "overall_status": evaluation_result.get("overall_status"),
            "rules_evaluated": evaluation_result.get("total_rules"),
            "rules_passed": evaluation_result.get("passed_count"),
            "rules_failed": evaluation_result.get("failed_count"),
        },
    )
    
    from app.schemas.common import BidComplianceEvaluationResponse
    return BidComplianceEvaluationResponse(
        overall_status=evaluation_result.get("overall_status"),
        passed_count=evaluation_result.get("passed_count"),
        failed_count=evaluation_result.get("failed_count"),
        total_rules=evaluation_result.get("total_rules"),
        risk_signals_triggered=evaluation_result.get("risk_signals_triggered"),
        rule_results=evaluation_result.get("rule_results"),
    )


@app.get("/api/officer/bids/{bid_id}/compliance-summary")
@require_role("officer")
def get_bid_compliance_summary(bid_id: str, request: Request = None, db: Session = Depends(get_db)):
    """Get compliance summary for bid - Phase 4."""
    officer = request.state.user
    bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
    
    # Get bid
    bid = db.query(Bid).filter(Bid.id == bid_id_uuid).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    summary = ComplianceService.compute_bid_compliance_summary(db, str(bid_id_uuid))
    
    return summary


@app.post("/api/officer/compliance/{compliance_result_id}/create-evidence-chain")
@require_role("officer")
def create_evidence_chain(
    compliance_result_id: str,
    body: dict,
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Create immutable evidence chain for compliance decision - Phase 4."""
    officer = request.state.user
    
    bid_id = body.get("bid_id")
    rule_id = body.get("rule_id")
    evidence_items = body.get("evidence_items", [])
    
    from app.services.evidence_traceability_phase4 import EvidenceTraceabilityPhase4
    
    try:
        chain_info = EvidenceTraceabilityPhase4.create_compliance_evidence_chain(
            db,
            compliance_result_id,
            bid_id,
            rule_id,
            evidence_items,
            officer["id"],
        )
        
        from app.schemas.common import EvidenceChainResponse
        return EvidenceChainResponse(
            compliance_result_id=chain_info["compliance_result_id"],
            chain_hash=chain_info["chain_hash"],
            evidence_count=chain_info["evidence_count"],
            created_at=chain_info["created_at"],
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/officer/compliance/{compliance_result_id}/trace-evidence")
@require_role("officer")
def trace_compliance_evidence(
    compliance_result_id: str,
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Trace compliance decision back to source evidence - Phase 4."""
    officer = request.state.user
    
    from app.services.evidence_traceability_phase4 import EvidenceTraceabilityPhase4
    
    try:
        traceability = EvidenceTraceabilityPhase4.trace_compliance_to_evidence(
            db,
            compliance_result_id,
        )
        return traceability
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/officer/compliance/{compliance_result_id}/create-risk-signal")
@require_role("officer")
def create_risk_signal_from_compliance(
    compliance_result_id: str,
    body: dict,
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Create risk signal when compliance rule fails - Phase 4."""
    officer = request.state.user
    
    bid_id = body.get("bid_id")
    rule_id = body.get("rule_id")
    signal_weight = body.get("signal_weight", 1.0)
    
    from app.services.evidence_traceability_phase4 import EvidenceTraceabilityPhase4
    
    try:
        signal_info = EvidenceTraceabilityPhase4.create_risk_signal_from_compliance(
            db,
            bid_id,
            compliance_result_id,
            rule_id,
            signal_weight,
            officer["id"],
        )
        
        from app.schemas.common import RiskSignalResponse
        return RiskSignalResponse(
            signal_id=signal_info["signal_id"],
            bid_id=signal_info["bid_id"],
            signal_type=signal_info["signal_type"],
            weight=signal_info["weight"],
            severity=signal_info["severity"],
            created_at=signal_info["created_at"],
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# PHASE 5: EXTERNAL DATA VERIFICATION (ADAPTERS & ORCHESTRATION)
# ============================================================================

@app.post("/api/officer/bids/{bid_id}/verify-external-data")
@require_role("officer")
async def verify_external_data(
    bid_id: str,
    body: dict,
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Verify extracted facts against government sources - Phase 5."""
    officer = request.state.user
    bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
    
    # Get bid
    bid = db.query(Bid).filter(Bid.id == bid_id_uuid).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    # Get extracted facts for bid
    extracted_facts_records = db.query(ExtractedFact).filter(
        ExtractedFact.bid_id == bid_id_uuid
    ).all() if hasattr(ExtractedFact, 'bid_id') else []
    
    extracted_facts = []
    for fact in extracted_facts_records:
        extracted_facts.append({
            "fact_id": str(fact.id),
            "fact_type": fact.fact_type,
            "extracted_value": fact.extracted_value,
            "entity_name": body.get("entity_name"),  # Can be overridden from request
            "source_document_id": str(fact.source_document_id) if hasattr(fact, 'source_document_id') else None,
        })
    
    # Run verification orchestration
    from app.services.adapter_orchestrator_phase5 import AdapterOrchestratorPhase5
    
    result = await AdapterOrchestratorPhase5.verify_extracted_facts(
        db,
        str(bid_id_uuid),
        extracted_facts,
        officer["id"],
    )
    
    from app.schemas.common import BidVerificationResponse
    return BidVerificationResponse(
        bid_id=result["bid_id"],
        overall_status=result["overall_status"],
        total_facts=result["total_facts"],
        verified_count=result["verified_count"],
        mismatch_count=result["mismatch_count"],
        unavailable_count=result["unavailable_count"],
        inconclusive_count=result["inconclusive_count"],
        error_count=result["error_count"],
        verification_results=result["verification_results"],
    )


@app.post("/api/officer/verify-single-fact")
@require_role("officer")
def verify_single_fact(
    body: dict,
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Verify a single fact against external source - Phase 5."""
    officer = request.state.user
    
    fact_type = body.get("fact_type")
    extracted_value = body.get("extracted_value")
    entity_name = body.get("entity_name")
    
    if not fact_type or not extracted_value:
        raise HTTPException(status_code=400, detail="fact_type and extracted_value required")
    
    from app.services.adapter_orchestrator_phase5 import AdapterOrchestratorPhase5
    
    result = AdapterOrchestratorPhase5.verify_single_fact(
        fact_type,
        extracted_value,
        entity_name,
    )
    
    from app.schemas.common import VerificationResultResponse
    return VerificationResultResponse(
        fact_type=result["fact_type"],
        extracted_value=result["extracted_value"],
        verification_status=result["verification_status"],
        api_response_code=result.get("api_response_code"),
        authority_value=result.get("authority_value"),
        match_result=result.get("match_result"),
        match_score=result.get("match_score"),
        verified_at=result.get("verified_at"),
    )


@app.get("/api/officer/verification-history")
@require_role("officer")
def get_verification_history(
    fact_id: Optional[str] = None,
    document_id: Optional[str] = None,
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Get verification history for fact or document - Phase 5."""
    officer = request.state.user
    
    from app.services.adapter_orchestrator_phase5 import AdapterOrchestratorPhase5
    
    history = AdapterOrchestratorPhase5.get_verification_history(
        db,
        fact_id,
        document_id,
    )
    
    return {"verification_history": history}


@app.post("/api/officer/test-name-matching")
@require_role("officer")
def test_name_matching(
    body: dict,
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Test name matching algorithm - Phase 5."""
    officer = request.state.user
    
    document_name = body.get("document_name", "")
    authority_name = body.get("authority_name", "")
    use_fuzzy = body.get("use_fuzzy", True)
    threshold = body.get("threshold", 0.85)
    
    from app.services.name_matching import match_names, normalize_name
    
    match_result, match_score = match_names(
        document_name,
        authority_name,
        use_fuzzy,
        threshold,
    )
    
    from app.schemas.common import NameMatchResultResponse
    return NameMatchResultResponse(
        document_name=document_name,
        authority_name=authority_name,
        match_result=match_result,
        match_score=match_score,
    )


@app.get("/api/officer/adapters/status")
@require_role("officer")
def get_adapters_status_v2(request: Request = None, db: Session = Depends(get_db)):
    """Get status of all verification adapters - Phase 5."""
    officer = request.state.user
    
    from app.adapters.registry import ADAPTER_REGISTRY
    
    adapter_statuses = []
    for source_name, adapter in ADAPTER_REGISTRY.items():
        status = {
            "source": source_name,
            "enabled": adapter.enabled if hasattr(adapter, 'enabled') else True,
            "class": adapter.__class__.__name__,
        }
        adapter_statuses.append(status)
    
    return {"adapters": adapter_statuses}

# ============================================================================
# PHASE 6: RISK ASSESSMENT & SCORING
# ============================================================================

@app.post("/api/officer/bids/{bid_id}/assess-risk")
@require_role("officer")
def assess_bid_risk(
    bid_id: str,
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Assess risk for bid using signal aggregation - Phase 6."""
    officer = request.state.user
    bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
    
    # Get bid
    bid = db.query(Bid).filter(Bid.id == bid_id_uuid).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    # Get all risk signals for bid
    signals = db.query(RiskSignal).filter(RiskSignal.bid_id == bid_id_uuid).all()
    
    # Convert to signal dicts
    signal_dicts = [
        {
            "signal_type": s.signal_type,
            "weight": float(s.weight),
            "severity": float(s.severity),
            "source": "compliance_rule" if s.compliance_result_id else "verification",
        }
        for s in signals
    ]
    
    # Aggregate using risk engine
    from app.services.risk_scoring_engine import RiskScoringEngine
    engine = RiskScoringEngine()
    
    assessment = engine.aggregate_signals(signal_dicts)
    
    # Store risk assessment
    risk_assessment = RiskService.assess_risk(
        db,
        str(bid_id_uuid),
        assessment["total_score"],
        assessment["risk_level"],
        "1.0.0",
        officer["id"],
    )
    
    # Get recommendations
    recommendations = engine.recommend_actions(assessment)
    
    from app.schemas.common import RiskScoringResultResponse
    return {
        "assessment": RiskScoringResultResponse(
            total_score=assessment["total_score"],
            risk_level=assessment["risk_level"],
            signal_count=assessment["signal_count"],
            signals_by_type=assessment["signals_by_type"],
            signal_breakdown=assessment["signal_breakdown"],
            risk_factors=assessment["risk_factors"],
            mitigating_factors=assessment["mitigating_factors"],
        ),
        "recommendations": recommendations,
    }


@app.get("/api/officer/bids/{bid_id}/risk-assessment")
@require_role("officer")
def get_bid_risk_assessment(
    bid_id: str,
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Get current risk assessment for bid - Phase 6."""
    officer = request.state.user
    bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
    
    # Get bid
    bid = db.query(Bid).filter(Bid.id == bid_id_uuid).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    # Get latest risk assessment
    assessment = RiskService.get_bid_risk_assessment(db, str(bid_id_uuid))
    if not assessment:
        raise HTTPException(status_code=404, detail="Risk assessment not found")
    
    from app.schemas.common import RiskAssessmentResponse
    return RiskAssessmentResponse(
        overall_risk_score=float(assessment.total_score),
        risk_level=assessment.risk_level,
        signal_breakdown={},
        assessed_at=assessment.computed_at.isoformat() if assessment.computed_at else "",
    )


@app.get("/api/officer/bids/{bid_id}/risk-signals")
@require_role("officer")
def get_bid_risk_signals(
    bid_id: str,
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Get all risk signals for bid - Phase 6."""
    officer = request.state.user
    bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
    
    # Get bid
    bid = db.query(Bid).filter(Bid.id == bid_id_uuid).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    # Get signals
    signals = RiskService.get_bid_signals(db, str(bid_id_uuid))
    
    return {
        "bid_id": str(bid_id_uuid),
        "signal_count": len(signals),
        "signals": [
            {
                "signal_id": str(s.id),
                "signal_type": s.signal_type,
                "weight": float(s.weight),
                "severity": float(s.severity),
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in signals
        ],
    }


@app.post("/api/officer/bids/{bid_id}/decompose-risk")
@require_role("officer")
def decompose_bid_risk(
    bid_id: str,
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Decompose risk score by source - Phase 6."""
    officer = request.state.user
    bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
    
    # Get bid
    bid = db.query(Bid).filter(Bid.id == bid_id_uuid).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    # Get signals
    signals = RiskService.get_bid_signals(db, str(bid_id_uuid))
    
    signal_dicts = [
        {
            "signal_type": s.signal_type,
            "weight": float(s.weight),
            "severity": float(s.severity),
            "source": "compliance_rule" if s.compliance_result_id else "verification",
        }
        for s in signals
    ]
    
    # Decompose
    from app.services.risk_scoring_engine import RiskScoringEngine
    engine = RiskScoringEngine()
    
    decomposition = engine.decompose_score(signal_dicts)
    
    from app.schemas.common import RiskDecompositionResponse
    return RiskDecompositionResponse(
        total_contribution=decomposition["total_contribution"],
        sources=decomposition["sources"],
    )


@app.post("/api/officer/bids/{bid_id}/risk-recommendations")
@require_role("officer")
def get_risk_recommendations(
    bid_id: str,
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Get recommended actions based on risk assessment - Phase 6."""
    officer = request.state.user
    bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
    
    # Get bid
    bid = db.query(Bid).filter(Bid.id == bid_id_uuid).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    # Get risk assessment
    assessment = RiskService.get_bid_risk_assessment(db, str(bid_id_uuid))
    if not assessment:
        raise HTTPException(status_code=404, detail="Risk assessment not found")
    
    # Get recommendations
    from app.services.risk_scoring_engine import RiskScoringEngine
    engine = RiskScoringEngine()
    
    # Build assessment dict for recommendation engine
    assessment_dict = {
        "risk_level": assessment.risk_level,
        "risk_factors": [],  # Would be populated from signals
    }
    
    recommendations = engine.recommend_actions(assessment_dict)
    
    return {
        "bid_id": str(bid_id_uuid),
        "risk_level": assessment.risk_level,
        "recommendations": recommendations,
    }


# ============================================================================
# PHASE 7: OFFICER DECISION SUPPORT
# ============================================================================

@app.post("/api/officer/bids/{bid_id}/get-recommendation")
@require_role("officer")
def get_bid_recommendation(
    bid_id: str,
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Get AI recommendation for bid decision - Phase 7."""
    officer = request.state.user
    bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
    
    # Get bid
    bid = db.query(Bid).filter(Bid.id == bid_id_uuid).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    # Get risk assessment
    risk_assessment = db.query(RiskAssessment).filter(
        RiskAssessment.bid_id == bid_id_uuid
    ).first()
    
    if not risk_assessment:
        raise HTTPException(status_code=404, detail="Risk assessment not found")
    
    # Get compliance results
    compliance_results = db.query(ComplianceResult).filter(
        ComplianceResult.bid_id == bid_id_uuid
    ).all()
    
    compliance_dicts = [
        {"passed": c.explanation == "PASS"}
        for c in compliance_results
    ]
    
    # Count pending clarifications
    pending_clarifs = db.query(ClarificationRequest).filter(
        ClarificationRequest.bid_id == bid_id_uuid,
        ClarificationRequest.status == "PENDING"
    ).count()
    
    # Generate recommendation
    from app.services.officer_decision_engine import DecisionRecommendationEngine
    
    risk_dict = {
        "risk_level": risk_assessment.risk_level,
        "total_score": float(risk_assessment.total_score),
    }
    
    recommendation = DecisionRecommendationEngine.generate_recommendation(
        str(bid_id_uuid),
        risk_dict,
        compliance_dicts,
        0,
        pending_clarifs,
    )
    
    # Validate recommendation
    validation = DecisionRecommendationEngine.validate_recommendation(recommendation)
    
    return {
        "bid_id": str(bid_id_uuid),
        "recommendation": recommendation,
        "validation": validation,
    }


@app.get("/api/officer/bids/{bid_id}/decision-readiness")
@require_role("officer")
def check_decision_readiness(
    bid_id: str,
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Check if bid is ready for officer decision - Phase 7."""
    officer = request.state.user
    bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
    
    from app.services.officer_decision_engine import OfficerDecisionWorkflow
    
    can_decide, reason = OfficerDecisionWorkflow.can_make_decision(db, str(bid_id_uuid))
    
    return {
        "bid_id": str(bid_id_uuid),
        "can_make_decision": can_decide,
        "reason": reason,
    }


@app.post("/api/officer/bids/{bid_id}/request-clarification-v2")
@require_role("officer")
def request_clarification_v2(
    bid_id: str,
    body: dict,
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Request clarification from bidder - Phase 7."""
    officer = request.state.user
    bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
    
    question_text = body.get("question_text", "")
    related_clause_id = body.get("related_clause_id")
    related_fact_id = body.get("related_fact_id")
    
    if not question_text:
        raise HTTPException(status_code=400, detail="question_text required")
    
    # Create clarification request
    clarif_request = ClarificationService.create_request(
        db,
        str(bid_id_uuid),
        officer["id"],
        question_text,
        related_clause_id,
        related_fact_id,
    )
    
    return {
        "request_id": str(clarif_request.id),
        "bid_id": str(bid_id_uuid),
        "status": clarif_request.status,
        "created_at": clarif_request.created_at.isoformat() if clarif_request.created_at else None,
    }


@app.get("/api/officer/bids/{bid_id}/clarifications-v2")
@require_role("officer")
def get_bid_clarifications_v2(
    bid_id: str,
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Get clarification requests and responses - Phase 7."""
    officer = request.state.user
    bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
    
    # Get all clarification requests
    requests = ClarificationService.get_bid_requests(db, str(bid_id_uuid))
    
    result = []
    for req in requests:
        # Get responses
        responses = db.query(ClarificationResponse).filter(
            ClarificationResponse.clarification_request_id == req.id
        ).all()
        
        result.append({
            "request_id": str(req.id),
            "question": req.question_text,
            "status": req.status,
            "response_count": len(responses),
            "created_at": req.created_at.isoformat() if req.created_at else None,
        })
    
    return {
        "bid_id": str(bid_id_uuid),
        "total_requests": len(requests),
        "requests": result,
    }


@app.post("/api/officer/bids/{bid_id}/make-decision-v2")
@require_role("officer")
def make_officer_decision_v2(
    bid_id: str,
    body: dict,
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Officer makes final decision on bid - Phase 7."""
    officer = request.state.user
    bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
    
    # Get bid
    bid = db.query(Bid).filter(Bid.id == bid_id_uuid).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    # Get recommendation (for reference)
    ai_recommendation = body.get("ai_recommendation", "MANUAL_REVIEW")
    final_decision = body.get("final_decision")  # VERIFIED, NON_COMPLIANT, NEEDS_CLARIFICATION
    override_reason = body.get("override_reason")
    
    if not final_decision:
        raise HTTPException(status_code=400, detail="final_decision required")
    
    # Validate final_decision
    valid_decisions = ["VERIFIED", "NON_COMPLIANT", "NEEDS_CLARIFICATION", "REJECTED"]
    if final_decision not in valid_decisions:
        raise HTTPException(status_code=400, detail=f"Invalid decision: {final_decision}")
    
    # Make decision
    decision = OfficerDecisionService.make_decision(
        db,
        str(bid_id_uuid),
        officer["id"],
        ai_recommendation,
        final_decision,
        override_reason,
    )
    
    # Transition bid state based on decision
    from app.services.officer_decision_engine import OfficerDecisionWorkflow
    
    if final_decision == "VERIFIED":
        new_state = "VERIFIED"
    elif final_decision == "NON_COMPLIANT" or final_decision == "REJECTED":
        new_state = "REJECTED"
    else:
        new_state = "NEEDS_CLARIFICATION"
    
    transition = OfficerDecisionWorkflow.transition_bid_state(
        db,
        str(bid_id_uuid),
        bid.status,
        new_state,
        officer["id"],
        f"Officer decision: {final_decision}",
    )
    
    # Log audit
    BidService._log_audit_event(
        db,
        "OFFICER_DECISION_MADE",
        str(bid_id_uuid),
        officer["id"],
        {
            "decision": final_decision,
            "ai_recommendation": ai_recommendation,
            "is_override": ai_recommendation != final_decision,
            "override_reason": override_reason,
        },
    )
    
    return {
        "bid_id": str(bid_id_uuid),
        "decision": final_decision,
        "decision_id": str(decision.id),
        "new_bid_status": new_state,
        "decided_at": decision.decided_at.isoformat() if decision.decided_at else None,
    }


@app.get("/api/officer/bids/{bid_id}/dashboard-summary")
@require_role("officer")
def get_bid_dashboard(
    bid_id: str,
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Get comprehensive bid summary for officer dashboard - Phase 7."""
    officer = request.state.user
    bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
    
    from app.services.officer_decision_engine import OfficerDashboardHelper
    
    summary = OfficerDashboardHelper.get_bid_summary(db, str(bid_id_uuid))
    
    if not summary:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    return summary

# ============================================================================

@app.get("/api/officer/bids/{bid_id}/compliance")
@require_role("officer")
def get_bid_compliance(bid_id: str, request: Request, db: Session = Depends(get_db)):
    """Get compliance evaluation results - Phase 5."""
    bid = BidService.get_bid(db, bid_id)
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    compliance_summary = ComplianceService.compute_bid_compliance_summary(db, bid_id)
    
    return {
        "bid_id": bid_id,
        "compliance": compliance_summary,
    }

# ============================================================================
# PHASE 6: RISK ASSESSMENT
# ============================================================================

@app.get("/api/officer/bids/{bid_id}/risk")
@require_role("officer")
def get_bid_risk(bid_id: str, request: Request, db: Session = Depends(get_db)):
    """Get risk assessment for bid - Phase 6."""
    bid = BidService.get_bid(db, bid_id)
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    risk_assessment = RiskService.get_bid_risk_assessment(db, bid_id)
    signals = RiskService.get_bid_signals(db, bid_id)
    
    return {
        "bid_id": bid_id,
        "risk_assessment": {
            "total_score": float(risk_assessment.total_score) if risk_assessment else None,
            "risk_level": risk_assessment.risk_level if risk_assessment else None,
        },
        "signals": [
            {
                "id": str(s.id),
                "signal_type": s.signal_type,
                "weight": float(s.weight),
                "severity": float(s.severity),
            }
            for s in signals
        ],
    }

@app.get("/api/officer/bids/{bid_id}/risk-signals")
@require_role("officer")
def get_bid_risk_signals(bid_id: str, request: Request, db: Session = Depends(get_db)):
    """Get all risk signals for bid with decomposition - Phase 6."""
    bid = BidService.get_bid(db, bid_id)
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    signals = RiskService.get_bid_signals(db, bid_id)
    
    signal_details = []
    for signal in signals:
        decompositions = RiskService.get_signal_decomposition(db, str(signal.id))
        signal_details.append({
            "signal_id": str(signal.id),
            "signal_type": signal.signal_type,
            "weight": float(signal.weight),
            "severity": float(signal.severity),
            "compliance_result_id": str(signal.compliance_result_id) if signal.compliance_result_id else None,
            "components": [
                {
                    "name": d.component_name,
                    "weight": float(d.component_weight),
                    "evidence": d.component_evidence,
                }
                for d in decompositions
            ],
        })
    
    return {
        "bid_id": bid_id,
        "signal_count": len(signals),
        "signals": signal_details,
    }

@app.post("/api/officer/bids/{bid_id}/risk-assessment")
@require_role("officer")
def assess_bid_risk(bid_id: str, request: Request, db: Session = Depends(get_db)):
    """Compute and store risk assessment for bid - Phase 6."""
    officer = request.state.user
    
    bid = BidService.get_bid(db, bid_id)
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    # Get all signals for this bid
    signals = RiskService.get_bid_signals(db, bid_id)
    
    # Compute aggregate risk score
    if signals:
        # Weighted average of signals
        total_weight = sum(float(s.weight) * float(s.severity) for s in signals)
        average_weight = total_weight / len(signals)
        total_score = min(100, average_weight * 100)
    else:
        total_score = 0
    
    # Determine risk level
    risk_level = RiskService.compute_risk_level(total_score)
    
    # Store assessment
    assessment = RiskService.assess_risk(
        db=db,
        bid_id=bid_id,
        total_score=total_score,
        risk_level=risk_level,
        actor_id=officer.id,
    )
    
    return {
        "assessment_id": str(assessment.id),
        "bid_id": bid_id,
        "total_score": float(assessment.total_score),
        "risk_level": assessment.risk_level,
        "signal_count": len(signals),
    }

# ============================================================================
# PHASE 7: CLARIFICATION
# ============================================================================

class ClarificationRequestBody(BaseModel):
    question_text: str
    related_clause_id: Optional[str] = None
    related_fact_id: Optional[str] = None

@app.post("/api/officer/bids/{bid_id}/clarifications/request")
@require_role("officer")
def request_clarification(
    bid_id: str,
    body: ClarificationRequestBody,
    request: Request,
    db: Session = Depends(get_db),
):
    """Officer requests clarification - Phase 7."""
    officer = request.state.user
    
    bid = BidService.get_bid(db, bid_id)
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    clarification = ClarificationService.create_request(
        db,
        bid_id,
        officer["id"],
        body.question_text,
        body.related_clause_id,
        body.related_fact_id,
    )
    
    # Transition bid state
    BidStateMachine.transition(
        db,
        bid_id,
        BidStatus.CLARIFICATION,
        officer["id"],
        {"reason": "clarification_requested"},
    )
    
    return {
        "id": str(clarification.id),
        "bid_id": bid_id,
        "status": clarification.status,
        "created_at": clarification.created_at.isoformat(),
    }

class ClarificationResponseBody(BaseModel):
    response_text: str
    supporting_documents: Optional[Dict[str, str]] = None

@app.post("/api/bidder/clarifications/{request_id}/respond")
@require_role("bidder")
def respond_to_clarification(
    request_id: str,
    body: ClarificationResponseBody,
    request: Request,
    db: Session = Depends(get_db),
):
    """Bidder responds to clarification - Phase 7."""
    bidder = request.state.user
    
    clarification = ClarificationService.get_request(db, request_id)
    if not clarification:
        raise HTTPException(status_code=404, detail="Clarification not found")
    
    response = ClarificationService.respond_to_request(
        db,
        request_id,
        bidder["id"],
        body.response_text,
        body.supporting_documents,
    )
    
    return {
        "id": str(response.id),
        "request_id": request_id,
        "responded_at": response.created_at.isoformat(),
    }

@app.get("/api/bids/{bid_id}/clarifications")
def get_bid_clarifications(bid_id: str, request: Request, db: Session = Depends(get_db)):
    """Get clarification requests for bid - Phase 7."""
    clarifications = ClarificationService.get_bid_requests(db, bid_id)
    
    return [
        {
            "id": str(c.id),
            "status": c.status,
            "question": c.question_text,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "resolved_at": c.resolved_at.isoformat() if c.resolved_at else None,
        }
        for c in clarifications
    ]

# ============================================================================
# PHASE 8: OFFICER DECISION & OVERRIDE
# ============================================================================

class MakeDecisionRequest(BaseModel):
    ai_recommendation: str
    final_decision: str
    override_reason: Optional[str] = None

@app.post("/api/officer/bids/{bid_id}/decision")
@require_role("officer")
def make_officer_decision(
    bid_id: str,
    body: MakeDecisionRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Officer makes final decision on bid - Phase 8."""
    officer = request.state.user
    
    bid = BidService.get_bid(db, bid_id)
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    decision = OfficerDecisionService.make_decision(
        db,
        bid_id,
        officer["id"],
        body.ai_recommendation,
        body.final_decision,
        body.override_reason,
    )
    
    # Transition bid state to REVIEW first if in DRAFT/SUBMITTED, then to DECIDED
    current_bid = BidService.get_bid(db, bid_id)
    current_state = current_bid.current_state if current_bid else "DRAFT"
    
    # If in DRAFT, move to SUBMITTED first
    if current_state == "DRAFT":
        BidStateMachine.transition(
            db,
            bid_id,
            BidStatus.SUBMITTED,
            officer["id"],
            {"reason": "auto_submitted_for_review"},
        )
    
    # Then transition through the proper chain to DECIDED
    # SUBMITTED -> VERIFYING -> REVIEW -> DECIDED
    if current_state in ["DRAFT", "SUBMITTED"]:
        BidStateMachine.transition(
            db,
            bid_id,
            BidStatus.VERIFYING,
            officer["id"],
            {"reason": "verifying_for_decision"},
        )
        BidStateMachine.transition(
            db,
            bid_id,
            BidStatus.REVIEW,
            officer["id"],
            {"reason": "reviewing_for_decision"},
        )
    
    # Final transition to DECIDED
    if current_state in ["DRAFT", "SUBMITTED", "VERIFYING"]:
        BidStateMachine.transition(
            db,
            bid_id,
            BidStatus.DECIDED,
            officer["id"],
            {"reason": "decision_made", "decision": body.final_decision},
        )
    
    return {
        "id": str(decision.id),
        "bid_id": bid_id,
        "final_decision": decision.decision,
        "decided_at": decision.decided_at.isoformat() if decision.decided_at else None,
    }

@app.get("/api/officer/bids/{bid_id}/decision")
@require_role("officer")
def get_officer_decision(bid_id: str, request: Request, db: Session = Depends(get_db)):
    """Get officer decision on bid - Phase 8."""
    decision = OfficerDecisionService.get_bid_decision(db, bid_id)
    if not decision:
        raise HTTPException(status_code=404, detail="No decision found")
    
    overrides = OfficerDecisionService.get_decision_overrides(db, str(decision.id))
    
    return {
        "id": str(decision.id),
        "bid_id": bid_id,
        "final_decision": decision.decision,
        "reason": decision.reason,
        "decided_at": decision.decided_at.isoformat() if decision.decided_at else None,
        "overrides": [
            {
                "id": str(o.id),
                "status": o.override_status,
                "created_at": o.created_at.isoformat() if o.created_at else None,
            }
            for o in overrides
        ],
    }

# ============================================================================
# PHASE 8: OFFICER EVALUATION & NOTES
# ============================================================================

@app.post("/api/officer/bids/{bid_id}/evaluate")
@require_role("officer")
def evaluate_bid(bid_id: str, request: Request, db: Session = Depends(get_db)):
    """Officer evaluates a bid (alias for evaluate-compliance) - Phase 8."""
    officer = request.state.user
    
    bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
    bid = db.query(Bid).filter(Bid.id == bid_id_uuid).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    # Run compliance orchestration
    try:
        orchestrator = ComplianceOrchestrator(db)
        result = orchestrator.evaluate_bid_compliance(str(bid_id_uuid))
        return {
            "bid_id": str(bid_id_uuid),
            "status": "EVALUATED",
            "compliance_result": result,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/officer/bids/{bid_id}/verify-source")
@require_role("officer")
def trigger_bid_verification(bid_id: str, body: dict, request: Request, db: Session = Depends(get_db)):
    """Officer triggers manual verification of bid against data source - Phase 8."""
    officer = request.state.user
    
    bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
    bid = db.query(Bid).filter(Bid.id == bid_id_uuid).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    source_name = body.get("source_name")
    if not source_name:
        raise HTTPException(status_code=400, detail="source_name is required")
    
    # Trigger verification through adapter
    try:
        from app.adapters.registry import AdapterRegistry
        registry = AdapterRegistry()
        adapter = registry.get_adapter(source_name)
        if not adapter:
            raise HTTPException(status_code=404, detail=f"Adapter {source_name} not found")
        
        result = adapter.verify(bid)
        return {
            "bid_id": str(bid_id_uuid),
            "source": source_name,
            "verification_result": result,
            "triggered_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Verification failed: {str(e)}")

@app.post("/api/officer/bids/{bid_id}/notes")
@require_role("officer")
def add_bid_note(bid_id: str, body: dict, request: Request, db: Session = Depends(get_db)):
    """Officer adds note/comment to bid - Phase 8."""
    officer = request.state.user
    
    bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
    bid = db.query(Bid).filter(Bid.id == bid_id_uuid).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    note_text = body.get("note")
    category = body.get("category", "GENERAL")
    
    if not note_text or not note_text.strip():
        raise HTTPException(status_code=400, detail="Note text is required")
    
    # Create note (using a simple approach - storing in metadata)
    # In production, you'd have a BidNote model
    note = {
        "id": str(uuid.uuid4()),
        "bid_id": str(bid_id_uuid),
        "author_id": officer["id"],
        "note": note_text,
        "category": category,
        "created_at": datetime.utcnow().isoformat(),
    }
    
    return note

@app.delete("/api/officer/bids/{bid_id}")
@require_role("officer")
def delete_bid(bid_id: str, request: Request, db: Session = Depends(get_db)):
    """Officer removes/deletes a bid - Phase 8."""
    officer = request.state.user
    
    bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
    bid = db.query(Bid).filter(Bid.id == bid_id_uuid).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    # Verify ownership - officer must have created the tender this bid is for
    tender = db.query(Tender).filter(Tender.id == bid.tender_id).first()
    if not tender or tender.created_by_officer_id != officer["id"]:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this bid")
    
    # Delete the bid
    db.delete(bid)
    db.commit()
    
    # Log audit entry
    audit_log = {
        "timestamp": datetime.utcnow().isoformat(),
        "action": "BID_DELETED",
        "actor_id": officer["id"],
        "actor_role": officer["role"],
        "bid_id": str(bid_id_uuid),
        "reason": "Officer deleted bid from dashboard",
    }
    
    return {
        "status": "success",
        "message": "Bid deleted successfully",
        "bid_id": str(bid_id_uuid),
        "audit": audit_log,
    }

# ============================================================================
# PHASE 13: NOTIFICATIONS
# ============================================================================

@app.get("/api/notifications")
@require_role("officer", "bidder")
def get_user_notifications(
    unread_only: bool = False,
    limit: int = 50,
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Get notifications for logged-in user - Phase 13."""
    user = request.state.user
    
    notifications = NotificationService.get_user_notifications(
        db,
        user["id"],
        unread_only,
        limit,
    )
    
    return [
        {
            "id": str(n.id),
            "notification_type": n.notification_type,
            "subject": n.subject,
            "message": n.message,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in notifications
    ]

@app.post("/api/notifications/{notification_id}/read")
@require_role("officer", "bidder")
def mark_notification_read(
    notification_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """Mark notification as read - Phase 13."""
    NotificationService.mark_read(db, notification_id)
    return {"notification_id": notification_id, "is_read": True}

# ============================================================================
# AUDIT TRAIL
# ============================================================================

@app.get("/api/audit")
@require_role("officer")
def get_audit_trail(db: Session = Depends(get_db)):
    """Get system audit trail - Phase 0."""
    events = db.query(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(100).all()
    
    return [
        {
            "id": str(e.id),
            "event_type": e.event_type,
            "entity_type": e.entity_type,
            "entity_id": str(e.entity_id),
            "actor_id": str(e.actor_id) if e.actor_id else None,
            "created_at": e.created_at.isoformat() if e.created_at else None,
            "event_hash": e.event_hash,
            "prev_hash": e.prev_hash,
        }
        for e in events
    ]

@app.get("/api/bids/{bid_id}/audit")
@require_role("officer", "bidder")
def get_bid_audit(bid_id: str, request: Request, db: Session = Depends(get_db)):
    """Get audit trail for bid - Phase 0."""
    events = BidService.get_audit_events(db, bid_id)
    
    return [
        {
            "id": str(e.id),
            "event_type": e.event_type,
            "actor_id": str(e.actor_id) if e.actor_id else None,
            "created_at": e.created_at.isoformat() if e.created_at else None,
            "payload": e.payload,
        }
        for e in events
    ]

# ============================================================================
# PHASE 2: EVIDENCE TRACEABILITY
# ============================================================================

@app.get("/api/officer/compliance/{compliance_result_id}/evidence-trace")
@require_role("officer")
def trace_compliance_evidence(
    compliance_result_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """Trace compliance result back to source evidence - Phase 2."""
    officer = request.state.user
    
    try:
        trace = EvidenceTraceability.trace_compliance_result(db, compliance_result_id)
        
        EvidenceTraceability._log_audit_event(
            db,
            "EVIDENCE_TRACED",
            compliance_result_id,
            officer["id"],
            {"action": "trace_compliance"},
        )
        db.commit()
        
        return trace
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/officer/risk-signals/{signal_id}/evidence-trace")
@require_role("officer")
def trace_risk_signal_evidence(
    signal_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """Trace risk signal to root cause - Phase 2."""
    officer = request.state.user
    
    try:
        trace = EvidenceTraceability.trace_risk_signal(db, signal_id)
        
        EvidenceTraceability._log_audit_event(
            db,
            "RISK_SIGNAL_TRACED",
            signal_id,
            officer["id"],
            {"action": "trace_signal"},
        )
        db.commit()
        
        return trace
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/officer/bids/{bid_id}/evidence-summary")
@require_role("officer")
def get_bid_evidence_summary(
    bid_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """Get complete evidence summary for a bid - Phase 2."""
    officer = request.state.user
    
    summary = EvidenceTraceability.get_bid_evidence_summary(db, bid_id)
    
    EvidenceTraceability._log_audit_event(
        db,
        "EVIDENCE_SUMMARY_ACCESSED",
        bid_id,
        officer["id"],
        {
            "compliance_count": summary["compliance_count"],
            "risk_signal_count": summary["risk_signal_count"],
        },
    )
    db.commit()
    
    return summary

@app.get("/api/officer/compliance/{compliance_result_id}/drill-down")
@require_role("officer")
def drill_down_compliance_evidence(
    compliance_result_id: str,
    request: Request,
    db: Session = Depends(get_db),
    fact_id: Optional[str] = None,
):
    """Officer drill-down into compliance evidence chain - Phase 2."""
    officer = request.state.user
    
    chain = EvidenceTraceability.get_drill_down_path(db, compliance_result_id, fact_id)
    
    EvidenceTraceability._log_audit_event(
        db,
        "COMPLIANCE_DRILL_DOWN",
        compliance_result_id,
        officer["id"],
        {"fact_id": fact_id, "chain_depth": len(chain)},
    )
    db.commit()
    
    return {
        "compliance_result_id": compliance_result_id,
        "chain": [
            {
                "level": link.level,
                "entity_id": link.entity_id,
                "entity_type": link.entity_type,
                "details": link.details,
            }
            for link in chain
        ],
    }


# ============================================================================
# PHASE 3: OCR & EXTRACTION
# ============================================================================

from app.services.ocr_processor import OCRProcessor

class ProcessOCRRequest(BaseModel):
    text_content: str
    doc_type_hint: Optional[str] = None

@app.post("/api/officer/documents/{document_id}/ocr/process-text")
@require_role("officer")
async def process_ocr_text(
    document_id: str,
    body: ProcessOCRRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Process OCR text and extract fields - Phase 3."""
    officer = request.state.user
    
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Create OCR job
    job = OCRService.create_ocr_job(db, document_id, "PROCESSOR_V1")
    
    # Process document
    result = await OCRProcessor.process_document(
        body.text_content,
        document_id,
        body.doc_type_hint,
    )
    
    # Update job
    if result["status"] == "COMPLETED":
        job = OCRService.update_ocr_job(
            db,
            str(job.id),
            "COMPLETED",
            text_content=result.get("text_preprocessed"),
            confidence_score=result.get("quality_score"),
            raw_response=result,
        )
        
        # Extract fields from result
        if "extracted_fields" in result:
            fields_dict = {}
            for field in result["extracted_fields"]:
                fields_dict[field["field_name"]] = {
                    "value": field["field_value"],
                    "confidence": field["confidence"],
                    "evidence_span": field["evidence_span"],
                }
            
            OCRService.extract_fields(
                db,
                str(job.id),
                fields_dict,
                officer["id"],
            )
    else:
        OCRService.update_ocr_job(
            db,
            str(job.id),
            "FAILED",
            error_message=result.get("error"),
        )
    
    return {
        "job_id": str(job.id),
        "status": result["status"],
        "document_type": result.get("document_type"),
        "quality_score": result.get("quality_score"),
        "extracted_fields": result.get("extracted_fields", []),
    }

@app.get("/api/officer/documents/{document_id}/extracted-fields")
@require_role("officer")
def get_extracted_fields(
    document_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """Get all extracted fields for a document - Phase 3."""
    officer = request.state.user
    
    facts = db.query(ExtractedFact).filter(
        ExtractedFact.document_id == document_id
    ).all()
    
    return [
        {
            "field_name": f.field_name,
            "field_value": f.field_value,
            "confidence": float(f.confidence) if f.confidence else None,
            "meets_threshold": f.meets_threshold,
            "evidence_span": f.evidence_span,
            "extracted_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in facts
    ]

@app.get("/api/officer/bids/{bid_id}/extraction-summary")
@require_role("officer")
def get_bid_extraction_summary(
    bid_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """Get extraction summary for bid documents - Phase 3."""
    officer = request.state.user
    
    documents = db.query(Document).filter(
        Document.bid_id == bid_id
    ).all()
    
    summary = {
        "bid_id": bid_id,
        "total_documents": len(documents),
        "documents": [],
    }
    
    for doc in documents:
        facts = db.query(ExtractedFact).filter(
            ExtractedFact.document_id == doc.id
        ).all()
        
        job = db.query(OCRJob).filter(
            OCRJob.document_id == doc.id
        ).order_by(OCRJob.created_at.desc()).first()
        
        summary["documents"].append({
            "document_id": str(doc.id),
            "doc_type": doc.doc_type,
            "ocr_status": doc.ocr_status,
            "extracted_fields_count": len(facts),
            "high_confidence_fields": sum(1 for f in facts if f.confidence and float(f.confidence) >= 0.7),
            "ocr_job": {
                "job_id": str(job.id) if job else None,
                "status": job.status if job else None,
                "quality_score": float(job.confidence_score) if job and job.confidence_score else None,
            },
        })
    
    return summary


# ============================================================================
# PHASE 4: VERIFICATION INTEGRATION
# ============================================================================

from app.services.adapter_orchestrator import AdapterOrchestrator

class VerifyFieldRequest(BaseModel):
    field_name: str
    field_value: str
    adapter_name: Optional[str] = None

@app.post("/api/officer/verify/field")
@require_role("officer")
async def verify_single_field(
    body: VerifyFieldRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Verify single field value against external sources - Phase 4."""
    officer = request.state.user
    
    result = await AdapterOrchestrator.verify_field(
        body.field_name,
        body.field_value,
        body.adapter_name,
    )
    
    return result.to_dict()

class VerifyBidFieldsRequest(BaseModel):
    bid_id: str
    fields: Dict[str, str]
    priority_adapters: Optional[List[str]] = None

@app.post("/api/officer/verify/bid-fields")
@require_role("officer")
async def verify_bid_fields(
    body: VerifyBidFieldsRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Verify multiple fields for bid against adapters - Phase 4."""
    officer = request.state.user
    
    results = await AdapterOrchestrator.verify_bid_fields(
        body.fields,
        body.priority_adapters,
    )
    
    # Store results in database
    for result in results:
        # Find extracted fact for this field and store verification
        # This would be coordinated with Phase 3 field extraction
        pass
    
    return {
        "bid_id": body.bid_id,
        "verifications": [r.to_dict() for r in results],
        "timestamp": datetime.utcnow().isoformat(),
    }

@app.get("/api/adapters/status")
@require_role("officer")
def get_adapters_status(request: Request, db: Session = Depends(get_db)):
    """Get status of all verification adapters - Phase 4."""
    officer = request.state.user
    
    status = AdapterOrchestrator.get_adapter_status()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "adapters": status,
        "note": "All adapters marked as MOCK. Change label to LIVE only after verifying real credentials and testing endpoints.",
    }

@app.get("/api/adapters/{adapter_name}/test")
@require_role("officer")
async def test_adapter(
    adapter_name: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """Test a specific adapter with sample data - Phase 4."""
    officer = request.state.user
    
    # Sample test values
    test_values = {
        "GSTN": {"field_name": "gst_number", "field_value": "27AAFCU5055K1Z5"},
        "MCA": {"field_name": "cin", "field_value": "U72900MH2015PTC265160"},
        "UDYAM": {"field_name": "udyam_number", "field_value": "UDYAM-XXXXX"},
        "NSIC": {"field_name": "nsic_number", "field_value": "NSIC-12345"},
        "DIGILOCKER": {"field_name": "document_hash", "field_value": "abcd1234"},
    }
    
    if adapter_name not in test_values:
        raise HTTPException(status_code=404, detail=f"Adapter {adapter_name} not found")
    
    test_data = test_values[adapter_name]
    
    result = await AdapterOrchestrator.verify_field(
        test_data["field_name"],
        test_data["field_value"],
        adapter_name,
    )
    
    return {
        "adapter": adapter_name,
        "test_field": test_data["field_name"],
        "test_value": test_data["field_value"],
        "result": result.to_dict(),
    }


# ============================================================================
# PHASE 5: DETERMINISTIC COMPLIANCE
# ============================================================================

from app.services.compliance_orchestrator import ComplianceOrchestrator

@app.post("/api/officer/bids/{bid_id}/evaluate-compliance")
@require_role("officer")
def evaluate_bid_compliance(
    bid_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """Evaluate bid compliance deterministically - Phase 5.
    
    IMMUTABILITY GUARANTEE:
    - FAIL results are immutable (cannot be changed to PASS)
    - Officer OVERRIDE is a separate decision artifact
    - Historical compliance results are preserved
    """
    officer = request.state.user
    
    try:
        result = ComplianceOrchestrator.evaluate_bid_compliance(
            db,
            bid_id,
            officer["id"],
        )
        
        return {
            "bid_id": bid_id,
            "evaluation": result,
            "immutability_enforced": True,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/officer/bids/{bid_id}/compliance-state")
@require_role("officer")
def get_compliance_state(
    bid_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """Get compliance state showing immutable results separate from officer decision - Phase 5."""
    officer = request.state.user
    
    state = ComplianceOrchestrator.get_compliance_state(db, bid_id)
    
    return {
        "bid_id": bid_id,
        "compliance_state": state,
        "phase_5_guarantees": {
            "immutability_enforced": True,
            "fail_results_immutable": True,
            "decision_separate_from_compliance": True,
        },
    }


# ============================================================================
# NEW: BIDDER DOCUMENT EXTRACTION & AUTO-POPULATION
# ============================================================================

@app.post("/api/bidder/bids/{bid_id}/extract-documents")
@require_role("bidder")
def extract_documents_for_bid(bid_id: str, request: Request, db: Session = Depends(get_db)):
    """
    Extract company details from uploaded documents via OCR.
    
    This endpoint:
    1. Retrieves all uploaded documents for the bid
    2. Runs OCR extraction on each
    3. Aggregates extracted fields (company name, GSTIN, PAN, CIN, Udyam, etc.)
    4. Returns structured data for auto-populating the bidder form
    
    Response includes:
    - extracted_fields: Aggregated fields from all documents
    - confidence_scores: Confidence for each extracted field
    - source_documents: Which documents contributed which fields
    """
    from app.services.ocr_service import OCRService
    
    try:
        bidder = request.state.user
        bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
        
        # Get bid
        bid = db.query(Bid).filter(Bid.id == bid_id_uuid).first()
        if not bid:
            raise HTTPException(status_code=404, detail="Bid not found")
        
        # Verify ownership
        user = db.query(User).filter(User.id == uuid.UUID(bidder["id"]) if isinstance(bidder["id"], str) else bidder["id"]).first()
        if not user or bid.bidder_org_id != user.organization_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this bid")
        
        # Get all documents
        documents = db.query(Document).filter(Document.bid_id == bid_id_uuid).all()
        if not documents:
            raise HTTPException(status_code=400, detail="No documents uploaded yet")
        
        # Aggregate extracted fields from all documents
        aggregated_fields = {
            "company_name": None,
            "organization_name": None,
            "gstin": None,
            "pan": None,
            "cin": None,
            "company_registration_number": None,
            "udyam_number": None,
            "msme_registration": None,
            "annual_turnover": None,
            "turnover_amount": None,
            "project_count": None,
            "emd_paid": False,
            "is_msme": False,
        }
        
        confidence_scores = {key: 0 for key in aggregated_fields.keys()}
        field_sources = {key: [] for key in aggregated_fields.keys()}
        
        # Extract from each document
        for doc in documents:
            try:
                # Get OCR result
                ocr_job = db.query(OCRJob).filter(
                    OCRJob.document_id == doc.id,
                    OCRJob.status == "COMPLETED"
                ).first()
                
                if not ocr_job:
                    continue
                
                # Get extracted facts
                facts = db.query(ExtractedFact).filter(
                    ExtractedFact.ocr_job_id == ocr_job.id
                ).all()
                
                # Populate aggregated fields
                for fact in facts:
                    field_name = fact.field_name.lower()
                    if field_name in aggregated_fields:
                        if aggregated_fields[field_name] is None:
                            aggregated_fields[field_name] = fact.extracted_value
                            confidence_scores[field_name] = fact.confidence or 0.85
                            field_sources[field_name].append({
                                "doc_id": str(doc.id),
                                "doc_type": doc.document_type,
                                "filename": doc.filename,
                            })
                        elif fact.confidence > confidence_scores.get(field_name, 0):
                            # Replace with higher confidence value
                            aggregated_fields[field_name] = fact.extracted_value
                            confidence_scores[field_name] = fact.confidence
                            field_sources[field_name] = [{
                                "doc_id": str(doc.id),
                                "doc_type": doc.document_type,
                                "filename": doc.filename,
                            }]
            except Exception as e:
                logger.warning(f"Failed to extract from document {doc.id}: {str(e)}")
                continue
        
        return {
            "bid_id": str(bid_id_uuid),
            "extracted_fields": aggregated_fields,
            "confidence_scores": confidence_scores,
            "field_sources": field_sources,
            "extraction_timestamp": datetime.utcnow().isoformat(),
            "documents_processed": len(documents),
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document extraction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


# ============================================================================
# NEW: DETAILED VERIFICATION ENDPOINTS WITH MATCH/MISMATCH REPORTING
# ============================================================================

class VerificationRequest(BaseModel):
    """Request body for government database verification"""
    gstin: Optional[str] = None
    pan: Optional[str] = None
    cin: Optional[str] = None
    udyam_number: Optional[str] = None
    company_name: Optional[str] = None


@app.post("/api/verify/gstin")
def verify_gstin_detailed(body: VerificationRequest):
    """
    Verify GSTIN against GSTN mock registry.
    
    Returns:
    - status: "verified" if GSTIN exists and registered name matches, "mismatch" if not
    - registered_name: Name registered in GSTN for this GSTIN
    - company_name: Company name extracted from documents
    - matches: Boolean indicating if names match
    - status_in_registry: ACTIVE, INACTIVE, etc.
    - filing_status: REGULAR, DEFAULTER, etc.
    """
    if not body.gstin:
        raise HTTPException(status_code=400, detail="GSTIN required")
    
    from app.adapters.seed_data import GSTN_RECORDS
    
    record = GSTN_RECORDS.get(body.gstin)
    if not record:
        return {
            "status": "not_found",
            "gstin": body.gstin,
            "error": "GSTIN not found in registry",
            "message": "This GSTIN is not registered with GSTN"
        }
    
    registered_name = record.get("legal_name", "")
    extracted_name = (body.company_name or "").strip().upper()
    registered_name_upper = registered_name.upper()
    
    names_match = extracted_name == registered_name_upper or \
                  registered_name_upper in extracted_name or \
                  extracted_name in registered_name_upper
    
    return {
        "status": "verified" if names_match else "mismatch",
        "gstin": body.gstin,
        "registered_name": registered_name,
        "company_name": body.company_name,
        "matches": names_match,
        "registry_status": record.get("status", "UNKNOWN"),
        "filing_status": record.get("return_filing_status", "UNKNOWN"),
        "last_filed": record.get("last_filed", "Unknown"),
        "message": f"Registry name: {registered_name}" if names_match else f"⚠ Name mismatch: Registry shows '{registered_name}'",
    }


@app.post("/api/verify/pan")
def verify_pan_detailed(body: VerificationRequest):
    """
    Verify PAN against mock PAN registry.
    
    Note: In real implementation, this would call the Income Tax Dept API.
    For MVP, we check format validity and return generic status.
    """
    if not body.pan:
        raise HTTPException(status_code=400, detail="PAN required")
    
    # Simple format check
    import re
    pan_pattern = r"^[A-Z]{5}[0-9]{4}[A-Z]$"
    is_valid = bool(re.match(pan_pattern, body.pan))
    
    return {
        "status": "verified" if is_valid else "invalid",
        "pan": body.pan,
        "is_valid": is_valid,
        "format_correct": is_valid,
        "message": "✓ PAN format is valid" if is_valid else "✗ Invalid PAN format",
    }


@app.post("/api/verify/cin")
def verify_cin_detailed(body: VerificationRequest):
    """
    Verify CIN (Corporate Identity Number) against MCA21 registry.
    
    Returns company registration details if found.
    """
    if not body.cin:
        raise HTTPException(status_code=400, detail="CIN required")
    
    from app.adapters.seed_data import MCA_RECORDS
    
    record = MCA_RECORDS.get(body.cin)
    if not record:
        return {
            "status": "not_found",
            "cin": body.cin,
            "error": "CIN not found in MCA21 registry",
            "message": "This CIN is not registered with MCA"
        }
    
    return {
        "status": "verified",
        "cin": body.cin,
        "company_name": record.get("company_name", ""),
        "incorporation_date": record.get("incorporation_date", ""),
        "company_status": record.get("status", "ACTIVE"),
        "message": f"✓ Registered company: {record.get('company_name', '')}"
    }


@app.post("/api/verify/udyam")
def verify_udyam_detailed(body: VerificationRequest):
    """
    Verify Udyam (MSME) registration.
    
    Returns MSME category and registration details.
    """
    if not body.udyam_number:
        raise HTTPException(status_code=400, detail="Udyam number required")
    
    from app.adapters.seed_data import UDYAM_RECORDS
    
    record = UDYAM_RECORDS.get(body.udyam_number)
    if not record:
        return {
            "status": "not_found",
            "udyam_number": body.udyam_number,
            "error": "Udyam number not found",
            "message": "This Udyam registration is not found (May not be MSME registered)"
        }
    
    return {
        "status": "verified",
        "udyam_number": body.udyam_number,
        "registered_name": record.get("legal_name", ""),
        "msme_category": record.get("category", ""),
        "registration_status": record.get("status", "ACTIVE"),
        "message": f"✓ MSME registered as {record.get('category', '')} enterprise"
    }
