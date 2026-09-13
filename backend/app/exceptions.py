"""
Custom exception classes for the GeM Compliance Platform.
All exceptions inherit from GemSentinelException for unified error handling.
"""

from typing import Optional, Dict, Any


class GemSentinelException(Exception):
    """Base exception for all system errors."""
    
    def __init__(
        self,
        message: str,
        code: str = None,
        details: Dict[str, Any] = None,
        status_code: int = 500
    ):
        self.message = message
        self.code = code or "INTERNAL_ERROR"
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)


class ValidationError(GemSentinelException):
    """Invalid input or state validation failure."""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details=details,
            status_code=400
        )


class NotFoundError(GemSentinelException):
    """Resource not found."""
    
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"{resource_type} not found",
            code="NOT_FOUND",
            details={"resource_type": resource_type, "resource_id": resource_id},
            status_code=404
        )


class AuthenticationError(GemSentinelException):
    """Authentication failed (invalid credentials or token)."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=401
        )


class AuthorizationError(GemSentinelException):
    """Insufficient permissions (RBAC denial)."""
    
    def __init__(self, required_role: str = None):
        super().__init__(
            message="Insufficient permissions for this operation",
            code="AUTHORIZATION_ERROR",
            details={"required_role": required_role} if required_role else {},
            status_code=403
        )


class ExternalServiceError(GemSentinelException):
    """External API or service error."""
    
    def __init__(self, service_name: str, error: str, retry_count: int = 0):
        super().__init__(
            message=f"{service_name} error: {error}",
            code="EXTERNAL_SERVICE_ERROR",
            details={"service": service_name, "retry_count": retry_count},
            status_code=502
        )


class DocumentProcessingError(GemSentinelException):
    """Document upload/OCR processing error."""
    
    def __init__(self, doc_id: str, error: str):
        super().__init__(
            message=f"Document processing failed: {error}",
            code="DOCUMENT_ERROR",
            details={"document_id": doc_id},
            status_code=400
        )


class StateTransitionError(GemSentinelException):
    """Invalid state transition (bid state machine violation)."""
    
    def __init__(self, current_state: str, requested_state: str):
        super().__init__(
            message=f"Cannot transition from {current_state} to {requested_state}",
            code="STATE_TRANSITION_ERROR",
            details={"current_state": current_state, "requested_state": requested_state},
            status_code=409
        )


class ComplianceEvaluationError(GemSentinelException):
    """Error during compliance rule evaluation."""
    
    def __init__(self, bid_id: str, rule_name: str, error: str):
        super().__init__(
            message=f"Compliance evaluation failed for rule {rule_name}",
            code="COMPLIANCE_ERROR",
            details={"bid_id": bid_id, "rule_name": rule_name, "error": error},
            status_code=400
        )


class DuplicateResourceError(GemSentinelException):
    """Resource already exists (unique constraint violation)."""
    
    def __init__(self, resource_type: str, identifier: str):
        super().__init__(
            message=f"{resource_type} with {identifier} already exists",
            code="DUPLICATE_RESOURCE",
            details={"resource_type": resource_type, "identifier": identifier},
            status_code=409
        )


class DocumentException(GemSentinelException):
    """Document-related operation error."""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            code="DOCUMENT_ERROR",
            details=details,
            status_code=400
        )


class ValidationException(GemSentinelException):
    """Validation failure (generic)."""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details=details,
            status_code=400
        )
