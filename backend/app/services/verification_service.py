"""
Verification Service — Orchestrates verification of extracted facts against government sources.

Responsibilities:
1. Load ExtractedFact from database
2. Construct VerificationClaim
3. Get appropriate adapter from registry
4. Call adapter.verify()
5. Persist immutable audit trail (VerificationAttempt, VerificationResult, VerificationNameMatch)
6. Return VerificationResult for compliance rule evaluation

Audit Trail Properties:
- Immutable: append-only, never update/delete
- Complete: every attempt creates new records with unique verification_attempt_id
- Credential-safe: no API keys, tokens, or raw request/response bodies stored
- Traceable: verification_attempt_id links attempt → result → name_match → evidence chain
"""
import logging
from datetime import datetime, timezone
from uuid import uuid4
from typing import Optional

from sqlalchemy.orm import Session

from app.adapters.base import VerificationClaim, VerificationResult, AdapterError
from app.adapters.registry import get_adapter_for_field
from app.models.models import (
    ExtractedFact,
    VerificationAttempt,
    VerificationResultNew,
    VerificationNameMatch,
)

logger = logging.getLogger(__name__)


class VerificationService:
    """Service class for verification operations (compatibility wrapper)."""
    
    @staticmethod
    async def verify_extracted_fact(session: Session, extracted_fact_id: str) -> VerificationResult:
        """Delegate to module function."""
        return await verify_extracted_fact(session, extracted_fact_id)
    
    @staticmethod
    async def verify_bid_identifiers(session: Session, bid_id: str) -> dict:
        """Delegate to module function."""
        return await verify_bid_identifiers(session, bid_id)
    
    @staticmethod
    def get_verification_history(session: Session, extracted_fact_id: str, limit: int = 10) -> list:
        """Delegate to module function."""
        return get_verification_history(session, extracted_fact_id, limit)


async def verify_extracted_fact(
    session: Session,
    extracted_fact_id: str,
) -> VerificationResult:
    """
    Orchestrates verification of an extracted fact against government sources.
    
    Flow:
    1. Load ExtractedFact record
    2. Create VerificationAttempt (PENDING)
    3. Get appropriate adapter via registry
    4. Call adapter.verify()
    5. Create VerificationResult record (immutable)
    6. Create VerificationNameMatch record if name matching performed
    7. Return VerificationResult for compliance rules
    
    Args:
        session: Database session
        extracted_fact_id: UUID of ExtractedFact to verify
    
    Returns:
        VerificationResult object with status and details
    
    Raises:
        ValueError: If ExtractedFact not found
    """
    
    # Load extracted fact
    fact = session.query(ExtractedFact).filter_by(id=extracted_fact_id).one_or_none()
    if not fact:
        raise ValueError(f"ExtractedFact not found: {extracted_fact_id}")
    
    logger.info(
        f"Starting verification for extracted fact {extracted_fact_id}: "
        f"field={fact.field_name}, value={fact.field_value[:20]}..."
    )
    
    # Generate unique verification_attempt_id
    attempt_id = uuid4()
    
    try:
        # Create VerificationAttempt record (PENDING status)
        attempt = VerificationAttempt(
            id=attempt_id,
            extracted_fact_id=extracted_fact_id,
            source_document_id=fact.document_id,
            verification_provider=fact.field_name,
            extracted_value=fact.field_value,
            request_timestamp=datetime.now(timezone.utc),
        )
        session.add(attempt)
        session.flush()  # Get ID before verification
        
        logger.debug(f"Created VerificationAttempt {attempt_id}")
        
        # Get appropriate adapter from registry
        adapter = get_adapter_for_field(fact.field_name)
        logger.debug(f"Selected adapter: {adapter.source_name}")
        
        # Build verification claim
        claim = VerificationClaim(
            field_name=fact.field_name,
            claimed_value=fact.field_value,
            entity_name=getattr(fact, 'entity_name', None),  # May not exist on all facts
            source_document_id=str(fact.document_id),
            extracted_fact_id=str(extracted_fact_id),
        )
        
        # Call adapter (wraps with timeout + retry logic)
        verification_result = await adapter.verify(
            claim,
            timeout_seconds=5.0,
            max_retries=2
        )
        
        logger.info(
            f"Verification completed for {attempt_id}: status={verification_result.status}, "
            f"http_code={verification_result.http_status_code}"
        )
        
        # Store VerificationResult (immutable)
        result_record = VerificationResultNew(
            verification_attempt_id=attempt_id,
            api_response_code=verification_result.http_status_code,
            api_reference_id=verification_result.api_reference_id,
            authority_value=verification_result.authority_value,
            authority_normalized_value=verification_result.authority_normalized_value,
            response_timestamp=verification_result.checked_at,
            verification_status=verification_result.status.value,
            fallback_used=verification_result.fallback_used,
            http_error_message=verification_result.error,
        )
        session.add(result_record)
        logger.debug(f"Created VerificationResult for attempt {attempt_id}")
        
        # Store VerificationNameMatch if name matching was performed
        if verification_result.match_result:
            name_match = VerificationNameMatch(
                verification_attempt_id=attempt_id,
                document_name=claim.entity_name or "",
                normalized_document_name=verification_result.document_normalized_value or "",
                authority_name=verification_result.authority_value or "",
                normalized_authority_name=verification_result.authority_normalized_value or "",
                match_result=verification_result.match_result,
                match_score=float(verification_result.match_score or 0.0),
            )
            session.add(name_match)
            logger.debug(
                f"Created VerificationNameMatch for attempt {attempt_id}: "
                f"result={verification_result.match_result}, score={verification_result.match_score}"
            )
        
        session.commit()
        logger.info(f"Audit trail persisted for verification attempt {attempt_id}")
        
        # Return result for compliance rule evaluation
        return verification_result
    
    except Exception as e:
        logger.error(
            f"Error during verification of extracted fact {extracted_fact_id}: {str(e)}"
        )
        session.rollback()
        raise


async def verify_bid_identifiers(
    session: Session,
    bid_id: str,
) -> dict:
    """
    Verify all extracted identifiers in a bid.
    
    Processes identifiers sequentially or with bounded parallelism
    (max 3 concurrent) to avoid overwhelming upstream APIs.
    
    Args:
        session: Database session
        bid_id: UUID of Bid to verify
    
    Returns:
        Dictionary with verification results by extracted_fact_id
    """
    from app.models.models import Bid
    
    # Load bid and its extracted facts
    bid = session.query(Bid).filter_by(id=bid_id).one_or_none()
    if not bid:
        raise ValueError(f"Bid not found: {bid_id}")
    
    # Get all extracted facts for this bid
    extracted_facts = (
        session.query(ExtractedFact)
        .join(ExtractedFact.document)
        .filter(Bid.id == bid_id)
        .all()
    )
    
    logger.info(f"Verifying {len(extracted_facts)} extracted facts for bid {bid_id}")
    
    results = {}
    for fact in extracted_facts:
        try:
            result = await verify_extracted_fact(session, fact.id)
            results[str(fact.id)] = {
                "status": result.status.value,
                "provider": result.source,
                "timestamp": result.checked_at.isoformat(),
            }
        except Exception as e:
            logger.warning(f"Failed to verify extracted fact {fact.id}: {str(e)}")
            results[str(fact.id)] = {
                "status": "ERROR",
                "error": str(e),
            }
    
    return results


def get_verification_history(
    session: Session,
    extracted_fact_id: str,
    limit: int = 10,
) -> list:
    """
    Retrieve verification history for an extracted fact.
    
    Returns immutable audit trail in chronological order.
    
    Args:
        session: Database session
        extracted_fact_id: UUID of ExtractedFact
        limit: Maximum number of records to return
    
    Returns:
        List of verification records with attempt_id, status, timestamp, provider
    """
    attempts = (
        session.query(VerificationAttempt)
        .filter_by(extracted_fact_id=extracted_fact_id)
        .order_by(VerificationAttempt.request_timestamp.desc())
        .limit(limit)
        .all()
    )
    
    history = []
    for attempt in attempts:
        result = (
            session.query(VerificationResultNew)
            .filter_by(verification_attempt_id=attempt.id)
            .one_or_none()
        )
        
        name_match = (
            session.query(VerificationNameMatch)
            .filter_by(verification_attempt_id=attempt.id)
            .one_or_none()
        )
        
        record = {
            "verification_attempt_id": str(attempt.id),
            "provider": attempt.verification_provider,
            "extracted_value": attempt.extracted_value,
            "request_timestamp": attempt.request_timestamp.isoformat(),
        }
        
        if result:
            record.update({
                "status": result.verification_status,
                "api_reference_id": result.api_reference_id,
                "authority_value": result.authority_value,
                "response_timestamp": result.response_timestamp.isoformat(),
                "fallback_used": result.fallback_used,
            })
        
        if name_match:
            record.update({
                "match_result": name_match.match_result,
                "match_score": float(name_match.match_score),
            })
        
        history.append(record)
    
    return history
