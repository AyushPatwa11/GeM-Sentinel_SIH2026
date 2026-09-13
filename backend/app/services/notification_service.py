"""Notification service for Phase 13."""
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.models import Notification, User, AuditEvent
import uuid
import hashlib


class NotificationType:
    """Notification type constants."""
    STATUS_CHANGE = "STATUS_CHANGE"
    CLARIFICATION_REQUEST = "CLARIFICATION_REQUEST"
    CLARIFICATION_RESPONSE = "CLARIFICATION_RESPONSE"
    DECISION_MADE = "DECISION_MADE"
    VERIFICATION_COMPLETE = "VERIFICATION_COMPLETE"
    RISK_FLAGGED = "RISK_FLAGGED"


class NotificationService:
    """Manage user notifications across email and in-app."""
    
    @staticmethod
    def create_notification(
        db: Session,
        user_id: str,
        notification_type: str,
        subject: str,
        message: str,
        related_bid_id: Optional[str] = None,
    ) -> Notification:
        """Create a notification for a user.
        
        Args:
            db: Database session
            user_id: User ID to notify
            notification_type: Type of notification
            subject: Notification subject
            message: Notification message
            related_bid_id: Optional bid ID reference
            
        Returns:
            Created Notification object
        """
        # Convert string IDs to UUID if needed
        user_id_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        related_bid_id_uuid = uuid.UUID(related_bid_id) if isinstance(related_bid_id, str) else related_bid_id if related_bid_id else None
        
        notification = Notification(
            id=uuid.uuid4(),
            user_id=user_id_uuid,
            notification_type=notification_type,
            subject=subject,
            message=message,
            related_bid_id=related_bid_id_uuid,
            is_read=False,
            email_sent=False,
        )
        db.add(notification)
        db.flush()
        
        # Log audit
        NotificationService._log_audit_event(
            db,
            "NOTIFICATION_CREATED",
            str(user_id_uuid),
            None,
            {
                "notification_type": notification_type,
                "related_bid_id": str(related_bid_id_uuid) if related_bid_id_uuid else None,
            },
        )
        
        db.commit()
        return notification
    
    @staticmethod
    def mark_read(db: Session, notification_id: str):
        """Mark notification as read."""
        # Convert string ID to UUID if needed
        notification_id_uuid = uuid.UUID(notification_id) if isinstance(notification_id, str) else notification_id
        notification = db.query(Notification).filter(
            Notification.id == notification_id_uuid
        ).first()
        
        if notification:
            notification.is_read = True
            db.commit()
    
    @staticmethod
    def mark_email_sent(
        db: Session,
        notification_id: str,
    ):
        """Mark notification as emailed."""
        # Convert string ID to UUID if needed
        notification_id_uuid = uuid.UUID(notification_id) if isinstance(notification_id, str) else notification_id
        notification = db.query(Notification).filter(
            Notification.id == notification_id_uuid
        ).first()
        
        if notification:
            notification.email_sent = True
            notification.email_sent_at = datetime.utcnow()
            db.commit()
    
    @staticmethod
    def get_notification(db: Session, notification_id: str) -> Optional[Notification]:
        """Get notification by ID."""
        # Convert string ID to UUID if needed
        notification_id_uuid = uuid.UUID(notification_id) if isinstance(notification_id, str) else notification_id
        return db.query(Notification).filter(
            Notification.id == notification_id_uuid
        ).first()
    
    @staticmethod
    def get_user_notifications(
        db: Session,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50,
    ) -> List[Notification]:
        """Get notifications for a user.
        
        Args:
            db: Database session
            user_id: User ID
            unread_only: If True, only unread notifications
            limit: Maximum number to return
            
        Returns:
            List of Notification objects
        """
        # Convert string ID to UUID if needed
        user_id_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        query = db.query(Notification).filter(Notification.user_id == user_id_uuid)
        
        if unread_only:
            query = query.filter(Notification.is_read == False)
        
        return query.order_by(
            Notification.created_at.desc()
        ).limit(limit).all()
    
    @staticmethod
    def get_unsent_notifications(db: Session, limit: int = 100) -> List[Notification]:
        """Get notifications that haven't been emailed yet.
        
        Args:
            db: Database session
            limit: Maximum number to return
            
        Returns:
            List of unsent Notification objects
        """
        return db.query(Notification).filter(
            Notification.email_sent == False
        ).order_by(
            Notification.created_at.asc()
        ).limit(limit).all()
    
    @staticmethod
    def get_bid_notifications(
        db: Session,
        bid_id: str,
    ) -> List[Notification]:
        """Get all notifications related to a bid."""
        # Convert string ID to UUID if needed
        bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
        return db.query(Notification).filter(
            Notification.related_bid_id == bid_id_uuid
        ).order_by(Notification.created_at.desc()).all()
    
    @staticmethod
    def notify_status_change(
        db: Session,
        bid_id: str,
        user_id: str,
        old_status: str,
        new_status: str,
    ) -> Notification:
        """Create notification for bid status change."""
        return NotificationService.create_notification(
            db,
            user_id,
            NotificationType.STATUS_CHANGE,
            f"Bid Status Updated",
            f"Your bid status has changed from {old_status} to {new_status}",
            bid_id,
        )
    
    @staticmethod
    def notify_clarification_request(
        db: Session,
        bid_id: str,
        bidder_user_id: str,
        question: str,
    ) -> Notification:
        """Create notification for clarification request."""
        return NotificationService.create_notification(
            db,
            bidder_user_id,
            NotificationType.CLARIFICATION_REQUEST,
            f"Clarification Needed",
            f"Officer has requested clarification: {question[:100]}...",
            bid_id,
        )
    
    @staticmethod
    def notify_decision_made(
        db: Session,
        bid_id: str,
        user_id: str,
        decision: str,
    ) -> Notification:
        """Create notification for officer decision."""
        return NotificationService.create_notification(
            db,
            user_id,
            NotificationType.DECISION_MADE,
            f"Bid Decision Made",
            f"Officer has made a decision on your bid: {decision}",
            bid_id,
        )
    
    @staticmethod
    def notify_risk_flagged(
        db: Session,
        bid_id: str,
        officer_user_id: str,
        risk_level: str,
        signal_type: str,
    ) -> Notification:
        """Create notification for flagged risk."""
        return NotificationService.create_notification(
            db,
            officer_user_id,
            NotificationType.RISK_FLAGGED,
            f"Risk Alert: {risk_level}",
            f"A {risk_level} risk has been flagged: {signal_type}",
            bid_id,
        )
    
    @staticmethod
    def get_unread_count(db: Session, user_id: str) -> int:
        """Get count of unread notifications for user."""
        # Convert string ID to UUID if needed
        user_id_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        return db.query(Notification).filter(
            Notification.user_id == user_id_uuid,
            Notification.is_read == False,
        ).count()
    
    @staticmethod
    def _log_audit_event(
        db: Session,
        event_type: str,
        entity_id: str,
        actor_id: Optional[str],
        payload: dict,
    ):
        """Log notification operation as audit event."""
        last_event = db.query(AuditEvent).order_by(AuditEvent.created_at.desc()).first()
        prev_hash = last_event.event_hash if last_event else "GENESIS_HASH"
        
        event_data = f"{event_type}:notification:{entity_id}:{actor_id}:{str(payload)}:{prev_hash}"
        event_hash = hashlib.sha256(event_data.encode()).hexdigest()
        
        # Convert string IDs to UUID if needed
        entity_id_uuid = uuid.UUID(entity_id) if isinstance(entity_id, str) else entity_id
        actor_id_uuid = uuid.UUID(actor_id) if isinstance(actor_id, str) else actor_id if actor_id else None
        
        audit_event = AuditEvent(
            id=uuid.uuid4(),
            event_type=event_type,
            entity_type="notification",
            entity_id=entity_id_uuid,
            actor_id=actor_id_uuid,
            payload=payload,
            prev_hash=prev_hash,
            event_hash=event_hash,
        )
        db.add(audit_event)
