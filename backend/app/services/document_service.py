"""Document management service with versioning, validation, and OCR integration for Phase 3."""
from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from app.models.models import Document, DocumentVersion, AuditEvent, OCRJob
from app.exceptions import ValidationException, DocumentException
import uuid
import hashlib
import mimetypes
import os
from pathlib import Path


class DocumentService:
    """Manage documents with versioning, validation, and OCR integration."""
    
    # Allowed file types for document uploads
    ALLOWED_FILE_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png'}
    ALLOWED_MIME_TYPES = {
        'application/pdf',
        'image/jpeg',
        'image/png',
    }
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    UPLOAD_ROOT = Path(os.getenv("UPLOAD_ROOT", Path(__file__).resolve().parents[2] / "uploads"))
    
    # Magic bytes for file type validation (file signatures)
    MAGIC_BYTES = {
        b'\x25\x50\x44\x46': '.pdf',  # PDF
        b'\xff\xd8\xff': '.jpg',       # JPEG
        b'\x89\x50\x4e\x47': '.png',   # PNG
    }
    
    @staticmethod
    def validate_file_upload(file_bytes: bytes, filename: str) -> Tuple[bool, str]:
        """Validate uploaded file for compliance.
        
        Args:
            file_bytes: Raw file bytes
            filename: Original filename
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check file size
        if len(file_bytes) > DocumentService.MAX_FILE_SIZE:
            return False, f"File size exceeds maximum allowed size of 10MB. Got {len(file_bytes) / 1024 / 1024:.2f}MB"
        
        if len(file_bytes) == 0:
            return False, "File is empty"
        
        # Check file extension
        _, ext = os.path.splitext(filename)
        ext = ext.lower()
        
        if ext not in DocumentService.ALLOWED_FILE_EXTENSIONS:
            return False, f"File type '{ext}' not allowed. Allowed types: {', '.join(DocumentService.ALLOWED_FILE_EXTENSIONS)}"
        
        # Check magic bytes (file signature)
        is_valid_magic = False
        for magic, magic_ext in DocumentService.MAGIC_BYTES.items():
            if file_bytes.startswith(magic):
                is_valid_magic = True
                if magic_ext != ext:
                    return False, f"File extension '{ext}' does not match file signature (detected as '{magic_ext}'). Possible tampering."
                break
        
        if not is_valid_magic:
            return False, "File signature validation failed. File may be corrupted or tampered with."
        
        # Check MIME type
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type and mime_type not in DocumentService.ALLOWED_MIME_TYPES:
            return False, f"MIME type '{mime_type}' not allowed. Allowed types: {', '.join(DocumentService.ALLOWED_MIME_TYPES)}"
        
        return True, ""
    
    @staticmethod
    def compute_file_hash(file_bytes: bytes) -> str:
        """Compute SHA256 hash of file.
        
        Args:
            file_bytes: Raw file bytes
            
        Returns:
            Hex-encoded SHA256 hash
        """
        return hashlib.sha256(file_bytes).hexdigest()

    @staticmethod
    def store_upload(file_bytes: bytes, bid_id: str, doc_type: str, filename: str) -> str:
        """Store validated bytes below the configured private upload root.

        The returned path is an application-relative path, not a user-controlled
        filesystem path. The original filename is used only to preserve a safe
        extension; document identifiers provide the storage name.
        """
        extension = Path(filename).suffix.lower()
        if extension not in DocumentService.ALLOWED_FILE_EXTENSIONS:
            raise ValidationException(f"Unsupported file extension: {extension}")

        safe_doc_type = "".join(
            character if character.isalnum() or character in {"-", "_"} else "_"
            for character in doc_type
        ).strip("_") or "OTHER"
        bid_directory = DocumentService.UPLOAD_ROOT / "bids" / str(uuid.UUID(str(bid_id)))
        bid_directory.mkdir(parents=True, exist_ok=True)
        stored_name = f"{safe_doc_type}_{uuid.uuid4().hex}{extension}"
        destination = bid_directory / stored_name
        destination.write_bytes(file_bytes)
        return str(destination.relative_to(DocumentService.UPLOAD_ROOT))
    
    @staticmethod
    def create_document(
        db: Session,
        bid_id: str,
        file_path: str,
        file_hash: str,
        doc_type: str,
        actor_id: str,
        upload_reason: str = "Initial upload",
    ) -> Document:
        """Create a new document with initial version.
        
        Args:
            db: Database session
            bid_id: Bid ID
            file_path: Path to stored file
            file_hash: SHA256 hash of file
            doc_type: Document type (GST_CERT, PAN, etc.)
            actor_id: User ID uploading
            upload_reason: Reason for upload
            
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
            current_version=1,
        )
        db.add(document)
        db.flush()
        
        # Create first version
        version = DocumentVersion(
            id=uuid.uuid4(),
            document_id=document.id,
            version_number=1,
            file_path=file_path,
            file_hash=file_hash,
            uploaded_by=actor_id_uuid,
            upload_reason=upload_reason,
        )
        db.add(version)
        db.flush()
        
        # Log audit event
        DocumentService._log_audit_event(
            db,
            "DOCUMENT_CREATED",
            str(document.id),
            actor_id_uuid,
            {
                "bid_id": str(bid_id_uuid),
                "doc_type": doc_type,
                "version": 1,
                "file_hash": file_hash,
            },
        )
        db.commit()
        
        return document
    
    @staticmethod
    def upload_new_version(
        db: Session,
        document_id: str,
        file_path: str,
        file_hash: str,
        actor_id: str,
        upload_reason: str = "Updated document",
    ) -> DocumentVersion:
        """Upload a new version of an existing document.
        
        Args:
            db: Database session
            document_id: Document ID
            file_path: Path to new file
            file_hash: SHA256 hash of new file
            actor_id: User ID uploading
            upload_reason: Reason for new version
            
        Returns:
            Created DocumentVersion object
        """
        # Convert string IDs to UUID if needed
        document_id_uuid = uuid.UUID(document_id) if isinstance(document_id, str) else document_id
        actor_id_uuid = uuid.UUID(actor_id) if isinstance(actor_id, str) else actor_id
        
        document = db.query(Document).filter(Document.id == document_id_uuid).first()
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        # Get next version number
        latest_version = db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id_uuid
        ).order_by(DocumentVersion.version_number.desc()).first()
        
        next_version_number = (latest_version.version_number + 1) if latest_version else 1
        
        # Create new version
        new_version = DocumentVersion(
            id=uuid.uuid4(),
            document_id=document_id_uuid,
            version_number=next_version_number,
            file_path=file_path,
            file_hash=file_hash,
            uploaded_by=actor_id_uuid,
            upload_reason=upload_reason,
            supersedes_version_id=latest_version.id if latest_version else None,
        )
        db.add(new_version)
        
        # Update document to point to latest version
        document.current_version = next_version_number
        document.file_path = file_path
        document.file_hash = file_hash
        document.ocr_status = "PENDING"  # Mark for reprocessing
        
        db.flush()
        
        # Log audit event
        DocumentService._log_audit_event(
            db,
            "DOCUMENT_VERSION_CREATED",
            str(document_id),
            actor_id,
            {
                "version_number": next_version_number,
                "upload_reason": upload_reason,
                "file_hash": file_hash,
                "supersedes_version": next_version_number - 1,
            },
        )
        db.commit()
        
        return new_version
    
    @staticmethod
    def get_document(db: Session, document_id: str) -> Optional[Document]:
        """Get document by ID.
        
        Args:
            db: Database session
            document_id: Document ID
            
        Returns:
            Document object or None
        """
        # Convert string ID to UUID if needed
        document_id_uuid = uuid.UUID(document_id) if isinstance(document_id, str) else document_id
        return db.query(Document).filter(Document.id == document_id_uuid).first()
    
    @staticmethod
    def get_version_history(db: Session, document_id: str) -> List[dict]:
        """Get complete version history for a document.
        
        Args:
            db: Database session
            document_id: Document ID
            
        Returns:
            List of version dictionaries
        """
        # Convert string ID to UUID if needed
        document_id_uuid = uuid.UUID(document_id) if isinstance(document_id, str) else document_id
        
        versions = db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id_uuid
        ).order_by(DocumentVersion.version_number).all()
        
        return [
            {
                "version_number": v.version_number,
                "file_hash": v.file_hash,
                "upload_reason": v.upload_reason,
                "uploaded_at": v.created_at.isoformat() if v.created_at else None,
                "uploaded_by": str(v.uploaded_by) if v.uploaded_by else None,
                "supersedes_version": v.supersedes_version_id,
            }
            for v in versions
        ]
    
    @staticmethod
    def get_version(
        db: Session,
        document_id: str,
        version_number: int,
    ) -> Optional[DocumentVersion]:
        """Get specific version of a document.
        
        Args:
            db: Database session
            document_id: Document ID
            version_number: Version number to retrieve
            
        Returns:
            DocumentVersion object or None
        """
        # Convert string ID to UUID if needed
        document_id_uuid = uuid.UUID(document_id) if isinstance(document_id, str) else document_id
        
        return db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id_uuid,
            DocumentVersion.version_number == version_number,
        ).first()
    
    @staticmethod
    def enqueue_ocr_job(
        db: Session,
        document_id: str,
        actor_id: str,
    ) -> OCRJob:
        """Enqueue OCR processing job for a document.
        
        Args:
            db: Database session
            document_id: Document ID to process
            actor_id: User ID requesting OCR
            
        Returns:
            Created OCRJob object
        """
        # Convert string IDs to UUID if needed
        document_id_uuid = uuid.UUID(document_id) if isinstance(document_id, str) else document_id
        actor_id_uuid = uuid.UUID(actor_id) if isinstance(actor_id, str) else actor_id
        
        document = db.query(Document).filter(Document.id == document_id_uuid).first()
        if not document:
            raise DocumentException(f"Document {document_id} not found")
        
        # Check if OCR job already exists for this document version
        existing_job = db.query(OCRJob).filter(
            OCRJob.document_id == document_id_uuid,
            OCRJob.version_number == document.current_version
        ).first()
        
        if existing_job and existing_job.status in ["PENDING", "PROCESSING"]:
            raise ValidationException(f"OCR job already in progress for document version {document.current_version}")
        
        # Create new OCR job
        ocr_job = OCRJob(
            id=uuid.uuid4(),
            document_id=document_id_uuid,
            version_number=document.current_version,
            status="PENDING",
            requested_by=actor_id_uuid,
        )
        db.add(ocr_job)
        db.flush()
        
        # Log audit event
        DocumentService._log_audit_event(
            db,
            "OCR_JOB_ENQUEUED",
            str(document_id_uuid),
            actor_id_uuid,
            {
                "ocr_job_id": str(ocr_job.id),
                "version_number": document.current_version,
            },
        )
        db.commit()
        
        return ocr_job
    
    @staticmethod
    def get_ocr_job_status(db: Session, document_id: str) -> Optional[dict]:
        """Get OCR job status for current document version.
        
        Args:
            db: Database session
            document_id: Document ID
            
        Returns:
            OCR job status dictionary or None
        """
        # Convert string ID to UUID if needed
        document_id_uuid = uuid.UUID(document_id) if isinstance(document_id, str) else document_id
        
        document = db.query(Document).filter(Document.id == document_id_uuid).first()
        if not document:
            raise DocumentException(f"Document {document_id} not found")
        
        job = db.query(OCRJob).filter(
            OCRJob.document_id == document_id_uuid,
            OCRJob.version_number == document.current_version
        ).first()
        
        if not job:
            return None
        
        return {
            "job_id": str(job.id),
            "status": job.status,
            "version_number": job.version_number,
            "requested_at": job.created_at.isoformat() if job.created_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "error_message": job.error_message,
            "extracted_text": job.extracted_text,
        }
    
    @staticmethod
    def _log_audit_event(
        db: Session,
        event_type: str,
        entity_id: str,
        actor_id: str,
        payload: dict,
    ):
        """Log document operation as audit event."""
        last_event = db.query(AuditEvent).order_by(AuditEvent.created_at.desc()).first()
        prev_hash = last_event.event_hash if last_event else "GENESIS_HASH"
        
        event_data = f"{event_type}:document:{entity_id}:{actor_id}:{str(payload)}:{prev_hash}"
        event_hash = hashlib.sha256(event_data.encode()).hexdigest()
        
        # Convert string IDs to UUID if needed
        entity_id_uuid = uuid.UUID(entity_id) if isinstance(entity_id, str) else entity_id
        actor_id_uuid = uuid.UUID(actor_id) if isinstance(actor_id, str) else actor_id
        
        audit_event = AuditEvent(
            id=uuid.uuid4(),
            event_type=event_type,
            entity_type="document",
            entity_id=entity_id_uuid,
            actor_id=actor_id_uuid,
            payload=payload,
            prev_hash=prev_hash,
            event_hash=event_hash,
        )
        db.add(audit_event)
