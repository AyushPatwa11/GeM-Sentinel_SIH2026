"""Clarification workflow service for Phase 7."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.models.models import (
    ClarificationRequest, ClarificationResponse, Bid, AuditEvent
)
import uuid
import hashlib


class ClarificationStatus:
    """Clarification status constants."""
    PENDING = "PENDING"
    RESOLVED = "RESOLVED"
    WITHDRAWN = "WITHDRAWN"


class ClarificationService:
    """Manage officer requests and bidder clarifications."""
    
    @staticmethod
    def create_request(
        db: Session,
        bid_id: str,
        officer_id: str,
        question_text: str,
        related_clause_id: Optional[str] = None,
        related_fact_id: Optional[str] = None,
    ) -> ClarificationRequest:
        """Create clarification request from officer.
        
        Args:
            db: Database session
            bid_id: Bid ID
            officer_id: Officer user ID
            question_text: Clarification question
            related_clause_id: Optional clause reference
            related_fact_id: Optional fact reference
            
        Returns:
            Created ClarificationRequest object
        """
        # Convert string IDs to UUID if needed
        bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
        officer_id_uuid = uuid.UUID(officer_id) if isinstance(officer_id, str) else officer_id
        related_clause_id_uuid = uuid.UUID(related_clause_id) if isinstance(related_clause_id, str) else related_clause_id if related_clause_id else None
        related_fact_id_uuid = uuid.UUID(related_fact_id) if isinstance(related_fact_id, str) else related_fact_id if related_fact_id else None
        
        request = ClarificationRequest(
            id=uuid.uuid4(),
            bid_id=bid_id_uuid,
            officer_id=officer_id_uuid,
            question_text=question_text,
            related_clause_id=related_clause_id_uuid,
            related_fact_id=related_fact_id_uuid,
            status=ClarificationStatus.PENDING,
        )
        db.add(request)
        db.flush()
        
        # Log audit
        ClarificationService._log_audit_event(
            db,
            "CLARIFICATION_REQUESTED",
            str(bid_id_uuid),
            officer_id_uuid,
            {
                "question_length": len(question_text),
                "related_clause_id": str(related_clause_id_uuid) if related_clause_id_uuid else None,
                "related_fact_id": str(related_fact_id_uuid) if related_fact_id_uuid else None,
            },
        )
        
        db.commit()
        return request
    
    @staticmethod
    def respond_to_request(
        db: Session,
        request_id: str,
        bidder_id: str,
        response_text: str,
        supporting_documents: Optional[Dict[str, str]] = None,
    ) -> ClarificationResponse:
        """Create clarification response from bidder.
        
        Args:
            db: Database session
            request_id: Clarification request ID
            bidder_id: Bidder user ID
            response_text: Response text
            supporting_documents: Optional dict of document names -> doc IDs
            
        Returns:
            Created ClarificationResponse object
        """
        # Convert string IDs to UUID if needed
        request_id_uuid = uuid.UUID(request_id) if isinstance(request_id, str) else request_id
        bidder_id_uuid = uuid.UUID(bidder_id) if isinstance(bidder_id, str) else bidder_id
        
        request = db.query(ClarificationRequest).filter(
            ClarificationRequest.id == request_id_uuid
        ).first()
        if not request:
            raise ValueError(f"Request {request_id} not found")
        
        response = ClarificationResponse(
            id=uuid.uuid4(),
            clarification_request_id=request_id_uuid,
            bidder_id=bidder_id_uuid,
            response_text=response_text,
            supporting_documents=supporting_documents,
        )
        db.add(response)
        db.flush()
        
        # Log audit
        ClarificationService._log_audit_event(
            db,
            "CLARIFICATION_RESPONDED",
            str(request.bid_id),
            bidder_id_uuid,
            {
                "request_id": str(request_id_uuid),
                "response_length": len(response_text),
                "document_count": len(supporting_documents) if supporting_documents else 0,
            },
        )
        
        db.commit()
        return response
    
    @staticmethod
    def resolve_request(
        db: Session,
        request_id: str,
        officer_id: str,
    ) -> ClarificationRequest:
        """Mark clarification request as resolved.
        
        Args:
            db: Database session
            request_id: Clarification request ID
            officer_id: Officer user ID
            
        Returns:
            Updated ClarificationRequest object
        """
        # Convert string IDs to UUID if needed
        request_id_uuid = uuid.UUID(request_id) if isinstance(request_id, str) else request_id
        officer_id_uuid = uuid.UUID(officer_id) if isinstance(officer_id, str) else officer_id
        
        request = db.query(ClarificationRequest).filter(
            ClarificationRequest.id == request_id_uuid
        ).first()
        if not request:
            raise ValueError(f"Request {request_id} not found")
        
        request.status = ClarificationStatus.RESOLVED
        request.resolved_at = datetime.utcnow()
        
        db.flush()
        
        # Log audit
        ClarificationService._log_audit_event(
            db,
            "CLARIFICATION_RESOLVED",
            str(request.bid_id),
            officer_id_uuid,
            {
                "request_id": str(request_id_uuid),
            },
        )
        
        db.commit()
        return request
    
    @staticmethod
    def get_request(db: Session, request_id: str) -> Optional[ClarificationRequest]:
        """Get clarification request by ID."""
        # Convert string ID to UUID if needed
        request_id_uuid = uuid.UUID(request_id) if isinstance(request_id, str) else request_id
        return db.query(ClarificationRequest).filter(
            ClarificationRequest.id == request_id_uuid
        ).first()
    
    @staticmethod
    def get_bid_requests(db: Session, bid_id: str) -> List[ClarificationRequest]:
        """Get all clarification requests for a bid."""
        # Convert string ID to UUID if needed
        bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
        return db.query(ClarificationRequest).filter(
            ClarificationRequest.bid_id == bid_id_uuid
        ).order_by(ClarificationRequest.created_at.desc()).all()
    
    @staticmethod
    def get_pending_requests(db: Session, bid_id: str) -> List[ClarificationRequest]:
        """Get pending clarification requests for a bid."""
        # Convert string ID to UUID if needed
        bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
        return db.query(ClarificationRequest).filter(
            ClarificationRequest.bid_id == bid_id_uuid,
            ClarificationRequest.status == ClarificationStatus.PENDING,
        ).all()
    
    @staticmethod
    def get_request_responses(
        db: Session,
        request_id: str,
    ) -> List[ClarificationResponse]:
        """Get all responses to a clarification request."""
        # Convert string ID to UUID if needed
        request_id_uuid = uuid.UUID(request_id) if isinstance(request_id, str) else request_id
        return db.query(ClarificationResponse).filter(
            ClarificationResponse.clarification_request_id == request_id_uuid
        ).order_by(ClarificationResponse.created_at.desc()).all()
    
    @staticmethod
    def has_pending_clarifications(db: Session, bid_id: str) -> bool:
        """Check if bid has pending clarification requests."""
        return bool(ClarificationService.get_pending_requests(db, bid_id))
    
    @staticmethod
    def _log_audit_event(
        db: Session,
        event_type: str,
        entity_id: str,
        actor_id: str,
        payload: dict,
    ):
        """Log clarification operation as audit event."""
        last_event = db.query(AuditEvent).order_by(AuditEvent.created_at.desc()).first()
        prev_hash = last_event.event_hash if last_event else "GENESIS_HASH"
        
        event_data = f"{event_type}:clarification:{entity_id}:{actor_id}:{str(payload)}:{prev_hash}"
        event_hash = hashlib.sha256(event_data.encode()).hexdigest()
        
        # Convert string IDs to UUID if needed
        entity_id_uuid = uuid.UUID(entity_id) if isinstance(entity_id, str) else entity_id
        actor_id_uuid = uuid.UUID(actor_id) if isinstance(actor_id, str) else actor_id
        
        audit_event = AuditEvent(
            id=uuid.uuid4(),
            event_type=event_type,
            entity_type="clarification",
            entity_id=entity_id_uuid,
            actor_id=actor_id_uuid,
            payload=payload,
            prev_hash=prev_hash,
            event_hash=event_hash,
        )
        db.add(audit_event)
