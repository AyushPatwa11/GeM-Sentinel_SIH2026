"""Audit trail service for Phase 0."""
import hashlib
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.models.models import AuditEvent


class AuditService:
    """Service for managing audit events with hash chaining."""
    
    @staticmethod
    def log_event(
        db: Session,
        event_type: str,
        entity_type: str,
        entity_id: str,
        actor_id: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        """Log an audit event with hash chaining.
        
        Args:
            db: Database session
            event_type: Type of event (e.g., BID_CREATED, DOCUMENT_UPLOADED)
            entity_type: Type of entity (e.g., bid, document, tender)
            entity_id: ID of entity being acted upon
            actor_id: ID of user performing the action
            payload: Additional contextual data
            
        Returns:
            Created AuditEvent object
        """
        if payload is None:
            payload = {}
        
        # Get previous event for hash chaining
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
            entity_id=entity_id,
            actor_id=actor_id,
            payload=payload,
            prev_hash=prev_hash,
            event_hash=event_hash,
        )
        db.add(audit_event)
        db.flush()
        
        return audit_event
    
    @staticmethod
    def get_events(
        db: Session,
        entity_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        event_type: Optional[str] = None,
        actor_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditEvent]:
        """Query audit events with optional filters.
        
        Args:
            db: Database session
            entity_id: Filter by entity ID
            entity_type: Filter by entity type
            event_type: Filter by event type
            actor_id: Filter by actor ID
            limit: Maximum number of events to return
            
        Returns:
            List of AuditEvent objects
        """
        query = db.query(AuditEvent)
        
        if entity_id:
            query = query.filter(AuditEvent.entity_id == entity_id)
        if entity_type:
            query = query.filter(AuditEvent.entity_type == entity_type)
        if event_type:
            query = query.filter(AuditEvent.event_type == event_type)
        if actor_id:
            query = query.filter(AuditEvent.actor_id == actor_id)
        
        return query.order_by(AuditEvent.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def verify_chain(db: Session, start_event_id: Optional[str] = None) -> bool:
        """Verify hash chain integrity.
        
        Iterates through audit events and verifies each event's hash matches
        its hash chain. Useful for detecting tampering.
        
        Args:
            db: Database session
            start_event_id: Optional event ID to start verification from
            
        Returns:
            True if all hashes valid, False if any mismatch found
        """
        events = db.query(AuditEvent).order_by(AuditEvent.created_at.asc()).all()
        
        if not events:
            return True
        
        prev_hash = "GENESIS_HASH"
        
        for event in events:
            # Reconstruct event data
            event_data = f"{event.event_type}:{event.entity_type}:{event.entity_id}:{event.actor_id}:{str(event.payload)}:{event.prev_hash}"
            expected_hash = hashlib.sha256(event_data.encode()).hexdigest()
            
            # Verify hash
            if event.event_hash != expected_hash:
                return False
            
            # Verify chain link
            if event.prev_hash != prev_hash:
                return False
            
            prev_hash = event.event_hash
        
        return True
