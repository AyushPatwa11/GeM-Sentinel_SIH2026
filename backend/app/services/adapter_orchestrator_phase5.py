"""Adapter Orchestrator for Phase 5 - External Data Verification Orchestration."""
import asyncio
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from app.models.models import (
    ExtractedFact, VerificationAttempt, VerificationResultNew, 
    VerificationNameMatch, AuditEvent, Document
)
from app.adapters.base import VerificationClaim, VerificationStatus
from app.adapters.registry import get_adapter_for_field, CLAIM_AUTHORITY_MAP
from app.services.name_matching import match_names, normalize_name
import uuid
import hashlib
import logging

logger = logging.getLogger(__name__)


class AdapterOrchestratorPhase5:
    """Orchestrates external data verification across multiple government sources."""
    
    @staticmethod
    async def verify_extracted_facts(
        db: Session,
        bid_id: str,
        extracted_facts: List[Dict[str, Any]],
        actor_id: str,
    ) -> Dict[str, Any]:
        """Verify multiple extracted facts against government sources.
        
        Args:
            db: Database session
            bid_id: Bid ID
            extracted_facts: List of extracted facts
                [
                    {
                        "fact_id": "fact-123",
                        "fact_type": "GSTIN",
                        "extracted_value": "27AAPPL1234L1Z5",
                        "entity_name": "Test Company Ltd",
                        "source_document_id": "doc-456",
                    },
                    ...
                ]
            actor_id: User ID requesting verification
            
        Returns:
            Verification results with summary
        """
        bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
        actor_id_uuid = uuid.UUID(actor_id) if isinstance(actor_id, str) else actor_id
        
        verification_results = []
        verification_mapping = {}  # Map fact_id -> verification result
        
        # Process each extracted fact
        for fact in extracted_facts:
            fact_id = fact.get("fact_id")
            fact_type = fact.get("fact_type")  # GSTIN, PAN, COMPANY_NAME, etc.
            extracted_value = fact.get("extracted_value")
            entity_name = fact.get("entity_name")
            source_document_id = fact.get("source_document_id")
            
            if not fact_type or not extracted_value:
                continue
            
            try:
                # Get adapter for this fact type
                adapter = get_adapter_for_field(fact_type.lower())
                
                # Create verification claim
                claim = VerificationClaim(
                    field_name=fact_type.lower(),
                    claimed_value=extracted_value,
                    entity_name=entity_name,
                    source_document_id=source_document_id,
                    extracted_fact_id=fact_id,
                    organization_id=str(bid_id_uuid),
                )
                
                # Verify the claim
                result = await adapter.verify(claim)
                
                # Store verification attempt and result
                attempt, verification_result = AdapterOrchestratorPhase5._store_verification(
                    db,
                    fact_id,
                    source_document_id,
                    fact_type,
                    extracted_value,
                    entity_name,
                    result,
                    actor_id_uuid,
                )
                
                verification_results.append({
                    "fact_id": fact_id,
                    "fact_type": fact_type,
                    "extracted_value": extracted_value,
                    "verification_status": result.status.value,
                    "api_response_code": result.http_status_code,
                    "api_reference_id": result.api_reference_id,
                    "authority_value": result.authority_value,
                    "match_result": result.match_result,
                    "match_score": result.match_score,
                    "verified_at": result.checked_at.isoformat() if result.checked_at else None,
                })
                
                verification_mapping[fact_id] = {
                    "status": result.status,
                    "result": verification_result,
                }
                
            except Exception as e:
                logger.error(f"Error verifying fact {fact_id}: {e}")
                verification_results.append({
                    "fact_id": fact_id,
                    "fact_type": fact_type,
                    "extracted_value": extracted_value,
                    "verification_status": "ERROR",
                    "error": str(e),
                })
        
        # Log audit event
        AdapterOrchestratorPhase5._log_verification_batch(
            db,
            bid_id_uuid,
            len(verification_results),
            actor_id_uuid,
        )
        
        db.commit()
        
        # Aggregate results
        verified_count = sum(1 for r in verification_results if r.get("verification_status") == "VERIFIED")
        mismatch_count = sum(1 for r in verification_results if r.get("verification_status") == "MISMATCH")
        unavailable_count = sum(1 for r in verification_results if r.get("verification_status") == "UNAVAILABLE")
        inconclusive_count = sum(1 for r in verification_results if r.get("verification_status") == "INCONCLUSIVE")
        error_count = sum(1 for r in verification_results if r.get("verification_status") == "ERROR")
        
        overall_status = "ALL_VERIFIED" if error_count == 0 and mismatch_count == 0 else "PARTIAL_FAILURE"
        
        return {
            "bid_id": str(bid_id_uuid),
            "overall_status": overall_status,
            "total_facts": len(verification_results),
            "verified_count": verified_count,
            "mismatch_count": mismatch_count,
            "unavailable_count": unavailable_count,
            "inconclusive_count": inconclusive_count,
            "error_count": error_count,
            "verification_results": verification_results,
        }
    
    @staticmethod
    def _store_verification(
        db: Session,
        fact_id: str,
        source_document_id: str,
        fact_type: str,
        extracted_value: str,
        entity_name: Optional[str],
        verification_result,
        actor_id_uuid: uuid.UUID,
    ) -> tuple:
        """Store verification attempt and result in database.
        
        Returns:
            Tuple of (VerificationAttempt, VerificationResultNew)
        """
        fact_id_uuid = uuid.UUID(fact_id) if isinstance(fact_id, str) else fact_id
        doc_id_uuid = uuid.UUID(source_document_id) if isinstance(source_document_id, str) else source_document_id
        
        # Create verification attempt record
        attempt = VerificationAttempt(
            id=uuid.uuid4(),
            extracted_fact_id=fact_id_uuid,
            source_document_id=doc_id_uuid,
            verification_provider=verification_result.source,
            extracted_value=extracted_value,
        )
        db.add(attempt)
        db.flush()
        
        # Create verification result record
        result = VerificationResultNew(
            id=uuid.uuid4(),
            verification_attempt_id=attempt.id,
            api_response_code=verification_result.http_status_code,
            api_reference_id=verification_result.api_reference_id,
            authority_value=verification_result.authority_value,
            authority_normalized_value=normalize_name(verification_result.authority_value) if verification_result.authority_value else None,
            response_timestamp=verification_result.checked_at,
            verification_status=verification_result.status.value,
            fallback_used=verification_result.fallback_used,
            http_error_message=verification_result.error,
        )
        db.add(result)
        db.flush()
        
        # If name matching occurred, record it
        if entity_name and verification_result.match_result:
            name_match = VerificationNameMatch(
                id=uuid.uuid4(),
                verification_attempt_id=attempt.id,
                document_name=entity_name,
                normalized_document_name=normalize_name(entity_name),
                authority_name=verification_result.authority_value or "",
                normalized_authority_name=normalize_name(verification_result.authority_value) if verification_result.authority_value else "",
                match_result=verification_result.match_result,
                match_score=verification_result.match_score or 0.0,
            )
            db.add(name_match)
            db.flush()
        
        return attempt, result
    
    @staticmethod
    def verify_single_fact(
        fact_type: str,
        extracted_value: str,
        entity_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Synchronous wrapper for single fact verification (for API endpoints).
        
        Args:
            fact_type: Type of fact (GSTIN, PAN, etc.)
            extracted_value: Value to verify
            entity_name: Optional entity name for matching
            
        Returns:
            Verification result
        """
        try:
            # Run async verification in event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            adapter = get_adapter_for_field(fact_type.lower())
            claim = VerificationClaim(
                field_name=fact_type.lower(),
                claimed_value=extracted_value,
                entity_name=entity_name,
            )
            
            result = loop.run_until_complete(adapter.verify(claim))
            
            return {
                "fact_type": fact_type,
                "extracted_value": extracted_value,
                "verification_status": result.status.value,
                "api_response_code": result.http_status_code,
                "authority_value": result.authority_value,
                "authority_normalized_value": result.authority_normalized_value,
                "match_result": result.match_result,
                "match_score": result.match_score,
                "verified_at": result.checked_at.isoformat() if result.checked_at else None,
                "evidence": result.evidence,
            }
        except Exception as e:
            logger.error(f"Error verifying fact: {e}")
            return {
                "fact_type": fact_type,
                "extracted_value": extracted_value,
                "verification_status": "ERROR",
                "error": str(e),
            }
    
    @staticmethod
    def get_verification_history(
        db: Session,
        fact_id: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get verification history for a fact or document.
        
        Args:
            db: Database session
            fact_id: Optional fact ID filter
            document_id: Optional document ID filter
            
        Returns:
            List of verification results with details
        """
        query = db.query(VerificationAttempt)
        
        if fact_id:
            fact_id_uuid = uuid.UUID(fact_id) if isinstance(fact_id, str) else fact_id
            query = query.filter(VerificationAttempt.extracted_fact_id == fact_id_uuid)
        
        if document_id:
            doc_id_uuid = uuid.UUID(document_id) if isinstance(document_id, str) else document_id
            query = query.filter(VerificationAttempt.source_document_id == doc_id_uuid)
        
        attempts = query.order_by(VerificationAttempt.created_at.desc()).all()
        
        results = []
        for attempt in attempts:
            result = db.query(VerificationResultNew).filter(
                VerificationResultNew.verification_attempt_id == attempt.id
            ).first()
            
            if result:
                name_match = db.query(VerificationNameMatch).filter(
                    VerificationNameMatch.verification_attempt_id == attempt.id
                ).first()
                
                results.append({
                    "attempt_id": str(attempt.id),
                    "extracted_fact_id": str(attempt.extracted_fact_id),
                    "source_document_id": str(attempt.source_document_id),
                    "verification_provider": attempt.verification_provider,
                    "extracted_value": attempt.extracted_value,
                    "verification_status": result.verification_status,
                    "api_response_code": result.api_response_code,
                    "api_reference_id": result.api_reference_id,
                    "authority_value": result.authority_value,
                    "match_result": name_match.match_result if name_match else None,
                    "match_score": float(name_match.match_score) if name_match else None,
                    "verified_at": result.response_timestamp.isoformat() if result.response_timestamp else None,
                    "fallback_used": result.fallback_used,
                })
        
        return results
    
    @staticmethod
    def _log_verification_batch(
        db: Session,
        bid_id: uuid.UUID,
        fact_count: int,
        actor_id: uuid.UUID,
    ):
        """Log verification batch as audit event."""
        last_event = db.query(AuditEvent).order_by(AuditEvent.created_at.desc()).first()
        prev_hash = last_event.event_hash if last_event else "GENESIS_HASH"
        
        payload = {
            "fact_count": fact_count,
        }
        event_data = f"VERIFICATION_BATCH:verification:{str(bid_id)}:{str(actor_id)}:{str(payload)}:{prev_hash}"
        event_hash = hashlib.sha256(event_data.encode()).hexdigest()
        
        audit_event = AuditEvent(
            id=uuid.uuid4(),
            event_type="VERIFICATION_BATCH",
            entity_type="verification",
            entity_id=bid_id,
            actor_id=actor_id,
            payload=payload,
            prev_hash=prev_hash,
            event_hash=event_hash,
        )
        db.add(audit_event)
