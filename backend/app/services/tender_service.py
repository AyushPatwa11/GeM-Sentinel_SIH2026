"""Tender service for Phase 2: Tender Management & Bid Creation."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.models.models import Tender, TenderVersion, User, AuditEvent, Organization
import uuid
import hashlib


class TenderService:
    """Service for managing tenders with database persistence."""
    
    @staticmethod
    def create_tender(
        db: Session,
        title: str,
        created_by_id: str,
        organization_id: str,
        description: str = "",
        deadline: datetime = None,
        version_number: str = "1.0",
        required_documents: Optional[List[str]] = None,
        source_document_path: str = None,
    ) -> Tender:
        """Create a new tender.
        
        Args:
            db: Database session
            title: Tender title
            created_by_id: User ID of officer creating tender
            organization_id: Organization ID (officer's org)
            description: Tender description
            deadline: Tender submission deadline
            version_number: Initial version (default "1.0")
            required_documents: List of required document types
            source_document_path: Path to source tender document
            
        Returns:
            Created Tender object
        """
        # Convert string IDs to UUID if needed
        created_by_id_uuid = uuid.UUID(created_by_id) if isinstance(created_by_id, str) else created_by_id
        organization_id_uuid = uuid.UUID(organization_id) if isinstance(organization_id, str) else organization_id
        
        # Create tender in draft status
        tender = Tender(
            id=uuid.uuid4(),
            title=title,
            description=description,
            deadline=deadline,
            required_documents=required_documents or [],
            created_by=created_by_id_uuid,
            organization_id=organization_id_uuid,
            status="draft",
            created_at=datetime.utcnow(),
        )
        db.add(tender)
        db.flush()
        
        # Create initial version
        tender_version = TenderVersion(
            id=uuid.uuid4(),
            tender_id=tender.id,
            version_number=version_number,
            source_document_path=source_document_path or "",
            precedence_policy_version="default_v1",
            published_at=None,  # Not published yet
        )
        db.add(tender_version)
        db.flush()
        
        # Log audit event
        TenderService._log_audit_event(
            db,
            "TENDER_CREATED",
            "tender",
            str(tender.id),
            str(created_by_id_uuid),
            {
                "title": title,
                "version": version_number,
                "required_documents": required_documents or [],
            },
        )
        db.commit()
        
        return tender
    
    @staticmethod
    def publish_tender(db: Session, tender_id: str, actor_id: str) -> Tender:
        """Publish a draft tender.
        
        Args:
            db: Database session
            tender_id: Tender ID
            actor_id: User ID publishing
            
        Returns:
            Updated Tender object
            
        Raises:
            ValueError: If tender not found or already published
        """
        # Convert string IDs to UUID if needed
        tender_id_uuid = uuid.UUID(tender_id) if isinstance(tender_id, str) else tender_id
        actor_id_uuid = uuid.UUID(actor_id) if isinstance(actor_id, str) else actor_id
        
        tender = db.query(Tender).filter(Tender.id == tender_id_uuid).first()
        if not tender:
            raise ValueError(f"Tender {tender_id} not found")
        
        # Allow republishing (idempotent)
        if tender.status != "published":
            tender.status = "published"
            tender.updated_at = datetime.utcnow()
            
            # Update latest version published_at
            latest_version = (
                db.query(TenderVersion)
                .filter(TenderVersion.tender_id == tender_id_uuid)
                .order_by(TenderVersion.version_number.desc())
                .first()
            )
            if latest_version:
                latest_version.published_at = datetime.utcnow()
            
            db.flush()
            
            # Log audit event
            TenderService._log_audit_event(
                db,
                "TENDER_PUBLISHED",
                "tender",
                str(tender.id),
                str(actor_id_uuid),
                {"version": latest_version.version_number if latest_version else "1.0"},
            )
        
        db.commit()
        return tender
    
    @staticmethod
    def close_tender(db: Session, tender_id: str, actor_id: str) -> Tender:
        """Close a tender (no more bids accepted).
        
        Args:
            db: Database session
            tender_id: Tender ID
            actor_id: User ID closing
            
        Returns:
            Updated Tender object
        """
        # Convert string IDs to UUID if needed
        tender_id_uuid = uuid.UUID(tender_id) if isinstance(tender_id, str) else tender_id
        actor_id_uuid = uuid.UUID(actor_id) if isinstance(actor_id, str) else actor_id
        
        tender = db.query(Tender).filter(Tender.id == tender_id_uuid).first()
        if not tender:
            raise ValueError(f"Tender {tender_id} not found")
        
        tender.status = "closed"
        tender.updated_at = datetime.utcnow()
        db.flush()
        
        # Log audit event
        TenderService._log_audit_event(
            db,
            "TENDER_CLOSED",
            "tender",
            str(tender.id),
            str(actor_id_uuid),
            {},
        )
        
        db.commit()
        return tender
    
    @staticmethod
    def get_tender(db: Session, tender_id: str) -> Optional[Tender]:
        """Get tender by ID.
        
        Args:
            db: Database session
            tender_id: Tender ID
            
        Returns:
            Tender object or None if not found
        """
        # Convert string ID to UUID if needed
        tender_id_uuid = uuid.UUID(tender_id) if isinstance(tender_id, str) else tender_id
        return db.query(Tender).filter(Tender.id == tender_id_uuid).first()
    
    @staticmethod
    def list_published_tenders(
        db: Session,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Tender]:
        """List all published tenders.
        
        Args:
            db: Database session
            limit: Max results
            offset: Pagination offset
            
        Returns:
            List of published Tender objects
        """
        return (
            db.query(Tender)
            .filter(Tender.status == "published")
            .order_by(Tender.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
    
    @staticmethod
    def list_officer_tenders(
        db: Session,
        officer_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Tender]:
        """List tenders created by an officer.
        
        Args:
            db: Database session
            officer_id: User ID of officer
            limit: Max results
            offset: Pagination offset
            
        Returns:
            List of Tender objects
        """
        # Convert string ID to UUID if needed
        officer_id_uuid = uuid.UUID(officer_id) if isinstance(officer_id, str) else officer_id
        
        return (
            db.query(Tender)
            .filter(Tender.created_by == officer_id_uuid)
            .order_by(Tender.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
    
    @staticmethod
    def get_latest_tender_version(db: Session, tender_id: str) -> Optional[TenderVersion]:
        """Get latest published version of a tender.
        
        Args:
            db: Database session
            tender_id: Tender ID
            
        Returns:
            TenderVersion object or None if no published version
        """
        # Convert string ID to UUID if needed
        tender_id_uuid = uuid.UUID(tender_id) if isinstance(tender_id, str) else tender_id
        
        return (
            db.query(TenderVersion)
            .filter(
                TenderVersion.tender_id == tender_id_uuid,
                TenderVersion.published_at != None,
            )
            .order_by(TenderVersion.published_at.desc())
            .first()
        )
    
    @staticmethod
    def get_tender_with_details(db: Session, tender_id: str) -> Dict[str, Any]:
        """Get tender with full details including version and clauses.
        
        Args:
            db: Database session
            tender_id: Tender ID
            
        Returns:
            Dictionary with tender details or None if not found
        """
        tender = TenderService.get_tender(db, tender_id)
        if not tender:
            return None
        
        latest_version = TenderService.get_latest_tender_version(db, tender_id)
        
        deadline_iso = tender.deadline.isoformat() if tender.deadline else None
        return {
            "id": str(tender.id),
            "title": tender.title,
            "description": tender.description or "",
            "status": tender.status,
            "created_by": str(tender.created_by),
            "organization_id": str(tender.organization_id),
            "created_at": tender.created_at.isoformat() if tender.created_at else None,
            "published_at": latest_version.published_at.isoformat() if latest_version and latest_version.published_at else None,
            "version_number": latest_version.version_number if latest_version else "1.0",
            "deadline": deadline_iso,
            "bid_submission_end_date": deadline_iso,
            "required_documents": tender.required_documents or [],
            "clause_count": len(tender.versions[0].clauses) if tender.versions and tender.versions[0].clauses else len(tender.required_documents or []),
        }
    
    @staticmethod
    def _log_audit_event(
        db: Session,
        event_type: str,
        entity_type: str,
        entity_id: str,
        actor_id: str,
        payload: dict,
    ) -> AuditEvent:
        """Internal helper to log audit events with hash chaining.
        
        Args:
            db: Database session
            event_type: Type of event
            entity_type: Type of entity
            entity_id: ID of entity
            actor_id: User ID of actor
            payload: Additional event context
            
        Returns:
            Created AuditEvent object
        """
        # Convert string IDs to UUID if needed
        entity_id_uuid = uuid.UUID(entity_id) if isinstance(entity_id, str) else entity_id
        actor_id_uuid = uuid.UUID(actor_id) if isinstance(actor_id, str) else actor_id
        
        # Get last event for hash chaining
        last_event = db.query(AuditEvent).order_by(AuditEvent.created_at.desc()).first()
        prev_hash = last_event.event_hash if last_event else "GENESIS_HASH"
        
        # Create event hash
        event_data = f"{event_type}:{entity_type}:{entity_id}:{actor_id}:{str(payload)}:{prev_hash}"
        event_hash = hashlib.sha256(event_data.encode()).hexdigest()
        
        # Create audit event
        audit_event = AuditEvent(
            id=uuid.uuid4(),
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id_uuid,
            actor_id=actor_id_uuid,
            payload=payload,
            prev_hash=prev_hash,
            event_hash=event_hash,
        )
        db.add(audit_event)
        
        return audit_event
