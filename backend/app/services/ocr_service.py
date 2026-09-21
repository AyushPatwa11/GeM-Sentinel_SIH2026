"""OCR processing and entity extraction service for Phase 3."""
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.models import OCRJob, Document, AuditEvent
import uuid
import hashlib
import re


class OCRService:
    """Handle OCR processing and entity extraction from documents."""
    
    # Named entity patterns for extraction
    ENTITY_PATTERNS = {
        'GSTIN': r'\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b',
        'PAN': r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b',
        'AADHAR': r'\b[0-9]{4}\s[0-9]{4}\s[0-9]{4}\b',
        'EMAIL': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'PHONE': r'\b[6-9][0-9]{9}\b',
        'DATE': r'\b(?:0[1-9]|[12][0-9]|3[01])[-/](?:0[1-9]|1[0-2])[-/](?:19|20)\d{2}\b',
    }
    
    @staticmethod
    def process_ocr_job(
        db: Session,
        job_id: str,
        file_bytes: bytes,
    ) -> Dict:
        """Process OCR job - extract text and entities from document.
        
        Args:
            db: Database session
            job_id: OCR Job ID
            file_bytes: Raw file bytes
            
        Returns:
            Dictionary with extracted text and entities
        """
        # Convert string ID to UUID if needed
        job_id_uuid = uuid.UUID(job_id) if isinstance(job_id, str) else job_id
        
        job = db.query(OCRJob).filter(OCRJob.id == job_id_uuid).first()
        if not job:
            raise ValueError(f"OCR Job {job_id} not found")
        
        # This compatibility method does not have the stored document path
        # required by a binary OCR provider. Never manufacture extracted text.
        job.status = "FAILED"
        job.error_message = (
            "Binary OCR requires a configured provider and the stored document "
            "path. Process supplied OCR text through the text-processing endpoint."
        )
        document = db.query(Document).filter(Document.id == job.document_id).first()
        if document:
            document.ocr_status = "UNSUPPORTED"

        OCRService._log_audit_event(
            db,
            "OCR_JOB_FAILED",
            str(job.document_id),
            job.requested_by,
            {
                "job_id": str(job_id_uuid),
                "error": job.error_message,
            },
        )
        db.commit()

        return {
            "job_id": str(job_id_uuid),
            "status": "FAILED",
            "error": job.error_message,
        }
    
    @staticmethod
    def _extract_entities(text: str) -> Dict[str, List[str]]:
        """Extract named entities from text using regex patterns.
        
        Args:
            text: Text to extract entities from
            
        Returns:
            Dictionary mapping entity types to list of found values
        """
        entities = {}
        
        for entity_type, pattern in OCRService.ENTITY_PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Deduplicate while preserving order
                entities[entity_type] = list(dict.fromkeys(matches))
        
        return entities
    
    @staticmethod
    def get_job_status(db: Session, job_id: str) -> Dict:
        """Get OCR job status and results.
        
        Args:
            db: Database session
            job_id: OCR Job ID
            
        Returns:
            Job status dictionary
        """
        # Convert string ID to UUID if needed
        job_id_uuid = uuid.UUID(job_id) if isinstance(job_id, str) else job_id
        
        job = db.query(OCRJob).filter(OCRJob.id == job_id_uuid).first()
        if not job:
            raise ValueError(f"OCR Job {job_id} not found")
        
        result = {
            "job_id": str(job.id),
            "document_id": str(job.document_id),
            "status": job.status,
            "version_number": job.version_number,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        }
        
        if job.status == "COMPLETED":
            result["extracted_text"] = job.extracted_text
            result["entities"] = job.extracted_entities or {}
        elif job.status == "FAILED":
            result["error_message"] = job.error_message
        
        return result
    
    @staticmethod
    def _log_audit_event(
        db: Session,
        event_type: str,
        entity_id: str,
        actor_id: str,
        payload: dict,
    ):
        """Log OCR operation as audit event."""
        last_event = db.query(AuditEvent).order_by(AuditEvent.created_at.desc()).first()
        prev_hash = last_event.event_hash if last_event else "GENESIS_HASH"
        
        event_data = f"{event_type}:ocr:{entity_id}:{actor_id}:{str(payload)}:{prev_hash}"
        event_hash = hashlib.sha256(event_data.encode()).hexdigest()
        
        # Convert string IDs to UUID if needed
        entity_id_uuid = uuid.UUID(entity_id) if isinstance(entity_id, str) else entity_id
        actor_id_uuid = uuid.UUID(actor_id) if isinstance(actor_id, str) else actor_id
        
        audit_event = AuditEvent(
            id=uuid.uuid4(),
            event_type=event_type,
            entity_type="ocr",
            entity_id=entity_id_uuid,
            actor_id=actor_id_uuid,
            payload=payload,
            prev_hash=prev_hash,
            event_hash=event_hash,
        )
        db.add(audit_event)
