"""Bid state machine for Phase 1+."""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.models import Bid, BidState, AuditEvent
import uuid
import hashlib


class BidStatus(str, Enum):
    """Valid bid states."""
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    VERIFYING = "VERIFYING"
    REVIEW = "REVIEW"
    CLARIFICATION = "CLARIFICATION"
    RESUBMITTED = "RESUBMITTED"
    DECIDED = "DECIDED"


class BidStateMachine:
    """Manage bid state transitions with validation and audit logging."""
    
    # Valid state transitions: from_state -> [to_states]
    VALID_TRANSITIONS = {
        BidStatus.DRAFT: [BidStatus.SUBMITTED],
        BidStatus.SUBMITTED: [BidStatus.VERIFYING, BidStatus.DRAFT],
        BidStatus.VERIFYING: [BidStatus.REVIEW, BidStatus.SUBMITTED],
        BidStatus.REVIEW: [BidStatus.CLARIFICATION, BidStatus.DECIDED, BidStatus.VERIFYING],
        BidStatus.CLARIFICATION: [BidStatus.RESUBMITTED, BidStatus.REVIEW],
        BidStatus.RESUBMITTED: [BidStatus.VERIFYING, BidStatus.DECIDED],
        BidStatus.DECIDED: [],  # Terminal state
    }
    
    @staticmethod
    def can_transition(from_state: str, to_state: str) -> bool:
        """Check if transition is valid."""
        current = BidStatus(from_state)
        target = BidStatus(to_state)
        return target in BidStateMachine.VALID_TRANSITIONS.get(current, [])
    
    @staticmethod
    def transition(
        db: Session,
        bid_id: str,
        new_state: str,
        actor_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Bid:
        """Transition bid to new state with validation and audit logging.
        
        Args:
            db: Database session
            bid_id: Bid ID
            new_state: Target state
            actor_id: User ID performing transition
            metadata: Optional transition metadata
            
        Returns:
            Updated Bid object
            
        Raises:
            ValueError: If transition is invalid
        """
        # Convert string bid_id to UUID if needed
        bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
        actor_id_uuid = uuid.UUID(actor_id) if isinstance(actor_id, str) else actor_id
        
        bid = db.query(Bid).filter(Bid.id == bid_id_uuid).first()
        if not bid:
            raise ValueError(f"Bid {bid_id} not found")
        
        current_state = bid.current_state or BidStatus.DRAFT
        
        # Validate transition
        if not BidStateMachine.can_transition(current_state, new_state):
            raise ValueError(
                f"Invalid transition: {current_state} -> {new_state}. "
                f"Valid targets: {BidStateMachine.VALID_TRANSITIONS.get(BidStatus(current_state), [])}"
            )
        
        # Exit current state
        if current_state != new_state:
            current_bid_state = db.query(BidState).filter(
                BidState.bid_id == bid_id_uuid,
                BidState.exited_at == None,
            ).first()
            
            if current_bid_state:
                current_bid_state.exited_at = datetime.utcnow()
        
        # Enter new state
        new_bid_state = BidState(
            id=uuid.uuid4(),
            bid_id=bid_id_uuid,
            state=new_state,
            entered_at=datetime.utcnow(),
            transition_metadata=metadata or {},
        )
        db.add(new_bid_state)
        
        # Update bid
        bid.current_state = new_state
        bid.state_entered_at = datetime.utcnow()
        bid.state_metadata = metadata
        
        db.flush()
        
        # Log audit event with hash chaining
        BidStateMachine._log_state_transition(
            db,
            bid_id,
            current_state,
            new_state,
            actor_id,
            metadata,
        )
        
        db.commit()
        return bid
    
    @staticmethod
    def _log_state_transition(
        db: Session,
        bid_id: str,
        from_state: str,
        to_state: str,
        actor_id: str,
        metadata: Optional[Dict],
    ):
        """Log state transition as audit event."""
        last_event = db.query(AuditEvent).order_by(AuditEvent.created_at.desc()).first()
        prev_hash = last_event.event_hash if last_event else "GENESIS_HASH"
        
        event_data = f"BID_STATE_TRANSITION:{bid_id}:{from_state}:{to_state}:{actor_id}:{str(metadata)}:{prev_hash}"
        event_hash = hashlib.sha256(event_data.encode()).hexdigest()
        
        # Convert IDs to UUID if needed
        bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
        actor_id_uuid = uuid.UUID(actor_id) if isinstance(actor_id, str) else actor_id
        
        audit_event = AuditEvent(
            id=uuid.uuid4(),
            event_type="BID_STATE_TRANSITION",
            entity_type="bid",
            entity_id=bid_id_uuid,
            actor_id=actor_id_uuid,
            payload={
                "from_state": from_state,
                "to_state": to_state,
                "metadata": metadata,
            },
            prev_hash=prev_hash,
            event_hash=event_hash,
        )
        db.add(audit_event)
    
    @staticmethod
    def get_state_history(db: Session, bid_id: str) -> list:
        """Get complete state transition history for a bid."""
        # Convert string bid_id to UUID if needed
        bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
        
        states = db.query(BidState).filter(
            BidState.bid_id == bid_id_uuid
        ).order_by(BidState.entered_at).all()
        
        return [
            {
                "state": s.state,
                "entered_at": s.entered_at.isoformat() if s.entered_at else None,
                "exited_at": s.exited_at.isoformat() if s.exited_at else None,
                "metadata": s.transition_metadata,
            }
            for s in states
        ]
