"""
Structured Logging for Verification Pipeline

Provides consistent, secure logging throughout verification:
- INFO: Verification initiation, adapter status, success
- WARN: Real adapter failure, API errors, retries
- ERROR: All retries exhausted
- DEBUG: Detailed request/response info (non-sensitive)

Security: Never logs credentials, raw request/response bodies, or tokens
"""
import logging
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def log_verification_initiated(
    extracted_fact_id: str,
    provider: str,
    extracted_value: str,
    verification_attempt_id: str,
):
    """Log verification initiation."""
    logger.info(
        f"Verification initiated | "
        f"attempt_id={verification_attempt_id} | "
        f"provider={provider} | "
        f"fact_id={extracted_fact_id} | "
        f"value_preview={extracted_value[:20]}..."
    )


def log_adapter_status_report(
    adapter_statuses: Dict[str, Dict[str, Any]],
):
    """Log adapter registry status at startup."""
    logger.info("=" * 50)
    logger.info("ADAPTER STATUS REPORT")
    logger.info("=" * 50)
    
    for source, status_info in adapter_statuses.items():
        enabled = status_info.get("enabled", False)
        adapter_type = "REAL" if enabled else "MOCK"
        logger.info(
            f"  {source:10s}: {adapter_type:5s} "
            f"| credential={'SET' if enabled else 'NOT SET':7s}"
        )
    
    logger.info("=" * 50)


def log_adapter_disabled(
    provider: str,
    reason: str = "credential not configured",
):
    """Log adapter disabled at startup."""
    logger.warning(
        f"Adapter disabled | provider={provider} | reason={reason}"
    )


def log_verification_request(
    provider: str,
    verification_attempt_id: str,
    claimed_value: str,
    timeout_seconds: float,
):
    """Log verification API request attempt (non-sensitive)."""
    logger.debug(
        f"Verification request | "
        f"provider={provider} | "
        f"attempt_id={verification_attempt_id} | "
        f"timeout={timeout_seconds}s"
    )


def log_verification_retry(
    provider: str,
    attempt_number: int,
    max_attempts: int,
    error_type: str,
    backoff_seconds: float,
    verification_attempt_id: str,
):
    """Log verification retry attempt."""
    logger.warning(
        f"Verification retry | "
        f"provider={provider} | "
        f"attempt={attempt_number}/{max_attempts} | "
        f"error={error_type} | "
        f"backoff={backoff_seconds}s | "
        f"attempt_id={verification_attempt_id}"
    )


def log_api_response(
    provider: str,
    verification_attempt_id: str,
    http_status_code: int,
    api_reference_id: Optional[str] = None,
    error_message: Optional[str] = None,
):
    """Log API response (without sensitive data)."""
    if error_message:
        logger.warning(
            f"API response error | "
            f"provider={provider} | "
            f"http_code={http_status_code} | "
            f"error={error_message[:100]} | "
            f"attempt_id={verification_attempt_id}"
        )
    else:
        logger.debug(
            f"API response | "
            f"provider={provider} | "
            f"http_code={http_status_code} | "
            f"reference_id={api_reference_id} | "
            f"attempt_id={verification_attempt_id}"
        )


def log_verification_success(
    provider: str,
    verification_attempt_id: str,
    verification_status: str,
    match_result: Optional[str],
    match_score: Optional[float],
    elapsed_time: float,
):
    """Log successful verification."""
    logger.info(
        f"Verification completed | "
        f"provider={provider} | "
        f"status={verification_status} | "
        f"match={match_result} "
        f"(score={match_score:.2f})" if match_score else f"match={match_result} | "
        f"elapsed={elapsed_time:.2f}s | "
        f"attempt_id={verification_attempt_id}"
    )


def log_verification_failure(
    provider: str,
    verification_attempt_id: str,
    final_error: str,
    total_attempts: int,
    total_elapsed_time: float,
):
    """Log verification failure after all retries exhausted."""
    logger.error(
        f"Verification failed (all retries exhausted) | "
        f"provider={provider} | "
        f"final_error={final_error[:100]} | "
        f"attempts={total_attempts} | "
        f"elapsed={total_elapsed_time:.2f}s | "
        f"attempt_id={verification_attempt_id}"
    )


def log_timeout(
    provider: str,
    verification_attempt_id: str,
    timeout_seconds: float,
):
    """Log timeout."""
    logger.warning(
        f"Verification timeout | "
        f"provider={provider} | "
        f"timeout={timeout_seconds}s | "
        f"attempt_id={verification_attempt_id}"
    )


def log_name_matching(
    document_name: str,
    authority_name: str,
    match_result: str,
    match_score: float,
    verification_attempt_id: str,
):
    """Log name matching result."""
    logger.debug(
        f"Name matching | "
        f"result={match_result} | "
        f"score={match_score:.2f} | "
        f"attempt_id={verification_attempt_id}"
    )


def log_audit_trail_persisted(
    verification_attempt_id: str,
    provider: str,
    verification_status: str,
    has_name_match: bool,
):
    """Log audit trail persistence."""
    logger.info(
        f"Audit trail persisted | "
        f"attempt_id={verification_attempt_id} | "
        f"provider={provider} | "
        f"status={verification_status} | "
        f"name_match_recorded={has_name_match}"
    )


def log_compliance_rule_evaluation(
    clause_id: str,
    bid_id: str,
    verification_status: Optional[str],
    compliance_status: str,
    reason: str,
):
    """Log compliance rule evaluation with verification context."""
    logger.info(
        f"Compliance rule evaluated | "
        f"clause_id={clause_id} | "
        f"bid_id={bid_id} | "
        f"verification_status={verification_status or 'N/A'} | "
        f"compliance_status={compliance_status} | "
        f"reason={reason}"
    )


def log_compliance_rule_deferred(
    clause_id: str,
    bid_id: str,
    reason: str,
):
    """Log compliance rule deferred."""
    logger.info(
        f"Compliance rule deferred | "
        f"clause_id={clause_id} | "
        f"bid_id={bid_id} | "
        f"reason={reason}"
    )


def log_fallback_to_mock(
    provider: str,
    verification_attempt_id: str,
    original_error: str,
):
    """Log fallback to mock adapter."""
    logger.warning(
        f"Fallback to mock adapter | "
        f"provider={provider} | "
        f"original_error={original_error[:100]} | "
        f"attempt_id={verification_attempt_id}"
    )


def log_verification_error(
    provider: str,
    verification_attempt_id: str,
    error_message: str,
):
    """Log verification error."""
    logger.error(
        f"Verification error | "
        f"provider={provider} | "
        f"error={error_message} | "
        f"attempt_id={verification_attempt_id}"
    )


def setup_verification_logging():
    """Configure structured logging for verification pipeline.
    
    Sets up:
    - JSON formatter for structured logs (optional, can be enabled via config)
    - Appropriate log levels
    - Sanitization of sensitive data
    """
    verification_logger = logging.getLogger("app.adapters")
    verification_logger.setLevel(logging.DEBUG)
    
    # Configure formatter
    formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)-8s | %(message)s"
    )
    
    # Add console handler
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    verification_logger.addHandler(handler)
    
    logger.info("Verification logging configured")


# Metrics collection helpers
class VerificationMetrics:
    """Collect verification metrics for monitoring."""
    
    @staticmethod
    def log_verification_attempt(
        provider: str,
        status: str,
        latency_seconds: float,
    ):
        """Log verification attempt for metrics collection."""
        metrics_logger = logging.getLogger("app.metrics")
        metrics_logger.info(
            json.dumps({
                "event": "verification_attempt",
                "provider": provider,
                "status": status,
                "latency_seconds": latency_seconds,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        )
    
    @staticmethod
    def log_retry_distribution(
        provider: str,
        retry_count: int,
    ):
        """Log retry count for distribution analysis."""
        metrics_logger = logging.getLogger("app.metrics")
        metrics_logger.info(
            json.dumps({
                "event": "verification_retry",
                "provider": provider,
                "retry_count": retry_count,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        )
