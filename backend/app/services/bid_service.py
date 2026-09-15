"""Bid service layer for Phase 0 database integration."""
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.models import Bid, Tender, TenderVersion, Document, User, AuditEvent, Organization
import uuid
import hashlib


class BidService:
    """Service for managing bids with database persistence."""
    
    @staticmethod
    def create_bid(
        db: Session,
        tender_version_id: str,
        bidder_org_id: str,
        actor_id: str,
    ) -> Bid:
        """Create a new bid.
        
        Args:
            db: Database session
            tender_version_id: ID of tender version
            bidder_org_id: Organization ID of bidder
            actor_id: User ID creating the bid
            
        Returns:
            Created Bid object
        """
        # Convert string IDs to UUID if needed
        tender_version_id_uuid = uuid.UUID(tender_version_id) if isinstance(tender_version_id, str) else tender_version_id
        bidder_org_id_uuid = uuid.UUID(bidder_org_id) if isinstance(bidder_org_id, str) else bidder_org_id
        actor_id_uuid = uuid.UUID(actor_id) if isinstance(actor_id, str) else actor_id
        
        bid = Bid(
            id=uuid.uuid4(),
            tender_version_id=tender_version_id_uuid,
            bidder_org_id=bidder_org_id_uuid,
            status="draft",
        )
        db.add(bid)
        db.flush()
        
        # Log audit event
        BidService._log_audit_event(
            db,
            "BID_CREATED",
            "bid",
            str(bid.id),
            actor_id_uuid,
            {"tender_version_id": str(tender_version_id_uuid), "bidder_org_id": str(bidder_org_id_uuid)},
        )
        db.commit()
        
        return bid
    
    @staticmethod
    def get_bid(db: Session, bid_id: str) -> Optional[Bid]:
        """Get bid by ID.
        
        Args:
            db: Database session
            bid_id: Bid ID
            
        Returns:
            Bid object or None if not found
        """
        # Convert string ID to UUID if needed
        bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
        return db.query(Bid).filter(Bid.id == bid_id_uuid).first()
    
    @staticmethod
    def list_bids_for_org(db: Session, org_id: str) -> List[Bid]:
        """List all bids for an organization.
        
        Args:
            db: Database session
            org_id: Organization ID
            
        Returns:
            List of Bid objects
        """
        # Convert string ID to UUID if needed
        org_id_uuid = uuid.UUID(org_id) if isinstance(org_id, str) else org_id
        return db.query(Bid).filter(Bid.bidder_org_id == org_id_uuid).all()
    
    @staticmethod
    def list_all_bids(db: Session) -> List[Bid]:
        """List all bids (for officers).
        
        Args:
            db: Database session
            
        Returns:
            List of all Bid objects
        """
        return db.query(Bid).all()
    
    @staticmethod
    def update_bid_status(
        db: Session,
        bid_id: str,
        new_status: str,
        actor_id: str,
    ) -> Bid:
        """Update bid status.
        
        Args:
            db: Database session
            bid_id: Bid ID
            new_status: New status value
            actor_id: User ID making the change
            
        Returns:
            Updated Bid object
        """
        # Convert string IDs to UUID if needed
        bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
        actor_id_uuid = uuid.UUID(actor_id) if isinstance(actor_id, str) else actor_id
        
        bid = BidService.get_bid(db, str(bid_id_uuid))
        if not bid:
            raise ValueError(f"Bid {bid_id} not found")
        
        old_status = bid.status
        bid.status = new_status
        
        if new_status == "submitted":
            bid.submitted_at = datetime.utcnow()
        
        db.flush()
        
        # Log audit event
        BidService._log_audit_event(
            db,
            "BID_STATUS_CHANGED",
            "bid",
            str(bid.id),
            actor_id_uuid,
            {"old_status": old_status, "new_status": new_status},
        )
        db.commit()
        
        return bid
    
    @staticmethod
    def upload_document(
        db: Session,
        bid_id: str,
        file_path: str,
        file_hash: str,
        doc_type: str,
        actor_id: str,
    ) -> Document:
        """Upload a document for a bid.
        
        Args:
            db: Database session
            bid_id: Bid ID
            file_path: Path where file is stored
            file_hash: SHA256 hash of file
            doc_type: Document type (GST_CERT, PAN, etc.)
            actor_id: User ID uploading
            
        Returns:
            Created Document object
        """
        # Convert string IDs to UUID if needed
        bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
        actor_id_uuid = uuid.UUID(actor_id) if isinstance(actor_id, str) else actor_id
        
        document = Document(
            id=uuid.uuid4(),
            bid_id=bid_id_uuid,
            file_path=file_path,
            file_hash=file_hash,
            doc_type=doc_type,
            ocr_status="PENDING",
        )
        db.add(document)
        db.flush()
        
        # Log audit event
        BidService._log_audit_event(
            db,
            "DOCUMENT_UPLOADED",
            "document",
            str(document.id),
            actor_id_uuid,
            {"bid_id": str(bid_id_uuid), "doc_type": doc_type, "file_hash": file_hash},
        )
        db.commit()
        
        return document
    
    @staticmethod
    def get_documents(db: Session, bid_id: str) -> List[Document]:
        """Get all documents for a bid.
        
        Args:
            db: Database session
            bid_id: Bid ID
            
        Returns:
            List of Document objects
        """
        # Convert string ID to UUID if needed
        bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
        return db.query(Document).filter(Document.bid_id == bid_id_uuid).all()
    
    @staticmethod
    def delete_document(db: Session, document_id: str, actor_id: str):
        """Delete a document.
        
        Args:
            db: Database session
            document_id: Document ID
            actor_id: User ID deleting
        """
        # Convert string IDs to UUID if needed
        document_id_uuid = uuid.UUID(document_id) if isinstance(document_id, str) else document_id
        actor_id_uuid = uuid.UUID(actor_id) if isinstance(actor_id, str) else actor_id
        
        document = db.query(Document).filter(Document.id == document_id_uuid).first()
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        bid_id = document.bid_id
        db.delete(document)
        db.flush()
        
        # Log audit event
        BidService._log_audit_event(
            db,
            "DOCUMENT_DELETED",
            "document",
            str(document_id),
            actor_id_uuid,
            {"bid_id": str(bid_id)},
        )
        db.commit()
    
    @staticmethod
    def get_audit_events(db: Session, bid_id: Optional[str] = None) -> List[AuditEvent]:
        """Get audit events, optionally filtered by bid ID.
        
        Args:
            db: Database session
            bid_id: Optional bid ID to filter by
            
        Returns:
            List of AuditEvent objects sorted by timestamp descending
        """
        query = db.query(AuditEvent)
        if bid_id:
            # Convert string ID to UUID if needed
            bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
            query = query.filter(AuditEvent.entity_id == bid_id_uuid)
        return query.order_by(AuditEvent.created_at.desc()).all()
    
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
            event_type: Type of event (BID_CREATED, DOCUMENT_UPLOADED, etc.)
            entity_type: Type of entity (bid, document, etc.)
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
