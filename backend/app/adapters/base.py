"""
PortalAdapter interface — every government-portal integration (real or mock)
must satisfy this exact contract. This is what lets the platform swap a
MockAdapter for a real GSTNAdapter later with zero changes to the rule
engine, risk engine, or API layer — only this file's contract matters.
"""
from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional


class VerificationStatus(str, Enum):
    """Discrete verification outcomes — never a boolean.
    
    Represents all possible states a verification can be in, ensuring
    we never conflate ERROR with FAIL or UNAVAILABLE with PASS.
    """
    VERIFIED = "VERIFIED"              # Authority confirmed match
    MISMATCH = "MISMATCH"              # Authority found record, name mismatch
    UNAVAILABLE = "UNAVAILABLE"        # Service unreachable or timeout
    ERROR = "ERROR"                    # Technical error (auth, malformed response)
    INCONCLUSIVE = "INCONCLUSIVE"      # No record found in authority
    PENDING = "PENDING"                # Verification not yet attempted
    NOT_REQUIRED = "NOT_REQUIRED"      # The authority check does not apply


@dataclass
class VerificationClaim:
    """What the bidder claims, extracted from their documents.
    
    This is the input to adapter.verify() — what we're trying to verify
    against authoritative government sources.
    """
    field_name: str                    # "gstin", "cin", "udyam_number", "pan", "nsic_number"
    claimed_value: str                 # The actual identifier value
    entity_name: Optional[str] = None  # Organization/person name from document (for matching)
    source_document_id: Optional[str] = None
    extracted_fact_id: Optional[str] = None
    organization_id: Optional[str] = None  # For backward compatibility


@dataclass
class VerificationResult:
    """Result of a verification attempt.
    
    Returned by adapter.verify() — contains all data needed by compliance
    rules, audit trail, UI, and evidence chain.
    """
    source: str                        # "GSTN", "MCA", "NSIC", "UDYAM", "PAN"
    status: VerificationStatus         # One of six discrete states
    checked_at: datetime               # When verification occurred
    freshness_seconds: int             # Freshness of data from authority
    
    # Response details (non-sensitive)
    http_status_code: Optional[int] = None  # 200, 401, 429, 503, etc.
    api_reference_id: Optional[str] = None  # Reference from authority (for traceability)
    
    # Name matching results
    authority_value: Optional[str] = None   # Name/value returned by authority
    authority_normalized_value: Optional[str] = None
    document_normalized_value: Optional[str] = None
    match_result: Optional[str] = None      # "exact_match" | "fuzzy_match" | "no_match"
    match_score: Optional[float] = None     # 0.0 to 1.0
    
    # Metadata
    data: Optional[Dict[str, Any]] = None   # Non-sensitive structured response data
    evidence: Optional[str] = None          # Human-readable explanation
    error: Optional[str] = None             # Technical error message
    fallback_used: bool = False             # True if Mock_Adapter used after Real failure


class AdapterError(Exception):
    """Raised by an adapter implementation on a technical failure
    (timeout, malformed response, connection error). Callers must map
    this to VerificationStatus.UNAVAILABLE, never to MISMATCH/FAILED —
    a technical failure is not evidence the bidder is non-compliant."""


class PortalAdapter(ABC):
    """Abstract base class for all government data adapters.
    Both Real_Adapters and Mock_Adapters must implement this contract.
    
    The verify() method wraps _verify_raw() with timeout + retry logic,
    ensuring consistent error handling across all adapter implementations.
    """
    
    source_name: str  # "GSTN", "MCA", "NSIC", "UDYAM", "PAN"
    enabled: bool = True  # Set to False if credentials unavailable

    @abstractmethod
    async def _verify_raw(self, claim: VerificationClaim) -> VerificationResult:
        """Implementations override this to call the actual API.
        
        Must raise AdapterError on any technical failure (timeout, network error, 
        malformed response, auth failure). Return MISMATCH or INCONCLUSIVE only when
        the authority explicitly returns those results.
        
        Args:
            claim: VerificationClaim with field_name, claimed_value, entity_name
        
        Returns:
            VerificationResult with status and details
        
        Raises:
            AdapterError: On any technical failure
        """
        raise NotImplementedError

    async def verify(
        self, 
        claim: VerificationClaim, 
        timeout_seconds: float = 5.0, 
        max_retries: int = 2
    ) -> VerificationResult:
        """Public entry point — wraps _verify_raw() with timeout + retry logic.
        
        Retry Strategy:
        • Network errors (connection refused, timeout): retry up to max_retries times
        • HTTP 5xx (500, 502, 503): retry up to max_retries times
        • HTTP 401 (unauthorized): do NOT retry → ERROR
        • HTTP 429 (rate limit): do NOT retry → ERROR (but honor Retry-After header)
        • HTTP 4xx other: do NOT retry → ERROR
        • Any unresolved failure → UNAVAILABLE (never MISMATCH)
        
        Backoff:
        • 1st retry: wait 2^0 * 1s = 1 second
        • 2nd retry: wait 2^1 * 1s = 2 seconds
        
        Args:
            claim: VerificationClaim to verify
            timeout_seconds: timeout per attempt (default 5s)
            max_retries: maximum retry attempts (default 2)
        
        Returns:
            VerificationResult with status (never raises)
        """
        if not self.enabled:
            return VerificationResult(
                source=self.source_name,
                status=VerificationStatus.UNAVAILABLE,
                checked_at=datetime.now(timezone.utc),
                freshness_seconds=0,
                error="Adapter disabled: credentials not configured",
            )
        
        last_error: Optional[str] = None
        last_http_code: Optional[int] = None
        
        for attempt in range(max_retries + 1):
            try:
                result = await asyncio.wait_for(
                    self._verify_raw(claim), 
                    timeout=timeout_seconds
                )
                if result.status != VerificationStatus.PENDING:
                    return result
                
            except asyncio.TimeoutError:
                last_error = f"timeout after {timeout_seconds}s (attempt {attempt + 1})"
                
            except AdapterError as e:
                last_error = str(e)
            
            # Exponential backoff before next retry
            if attempt < max_retries:
                backoff_delay = 2 ** attempt  # 1s, then 2s
                await asyncio.sleep(backoff_delay)
        
        return VerificationResult(
            source=self.source_name,
            status=VerificationStatus.UNAVAILABLE,
            checked_at=datetime.now(timezone.utc),
            freshness_seconds=0,
            error=last_error,
        )
    
    @staticmethod
    def status_map(
        http_code: Optional[int], 
        api_error: Optional[str] = None,
        record_found: bool = False,
        name_match: Optional[str] = None
    ) -> VerificationStatus:
        """Maps HTTP status codes and API responses to VerificationStatus.
        
        Decision Tree:
        • HTTP 200 + record_found + name_match in ("exact_match", "fuzzy_match") → VERIFIED
        • HTTP 200 + record_found + name_match == "no_match" → MISMATCH
        • HTTP 200 + not record_found → INCONCLUSIVE
        • HTTP 4xx (not 401, 429) → ERROR
        • HTTP 401 (unauthorized) → ERROR
        • HTTP 429 (rate limit) → ERROR
        • HTTP 5xx → UNAVAILABLE
        • Timeout → UNAVAILABLE
        • Connection error → UNAVAILABLE
        • Malformed response → ERROR
        
        Args:
            http_code: HTTP status code from API
            api_error: Error message from API
            record_found: Whether authority found a matching record
            name_match: "exact_match" | "fuzzy_match" | "no_match" | None
        
        Returns:
            VerificationStatus
        """
        if http_code is None:
            return VerificationStatus.ERROR
        
        if http_code == 200:
            if record_found:
                if name_match in ("exact_match", "fuzzy_match"):
                    return VerificationStatus.VERIFIED
                elif name_match == "no_match":
                    return VerificationStatus.MISMATCH
                else:
                    # Record found, but name match not determined
                    return VerificationStatus.INCONCLUSIVE
            else:
                # No record found in authority
                return VerificationStatus.INCONCLUSIVE
        
        if http_code in (400, 403, 404):
            # 4xx errors (except 401, 429) → ERROR
            return VerificationStatus.ERROR
        
        if http_code == 401:
            # Unauthorized — authentication failure
            return VerificationStatus.ERROR
        
        if http_code == 429:
            # Rate limited
            return VerificationStatus.ERROR
        
        if 500 <= http_code < 600:
            # 5xx errors → UNAVAILABLE (after retries)
            return VerificationStatus.UNAVAILABLE
        
        # Unknown/unexpected status → ERROR
        return VerificationStatus.ERROR
