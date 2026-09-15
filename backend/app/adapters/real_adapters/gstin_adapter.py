"""
GSTIN Adapter — Real verification against GSTN (Goods and Services Tax Network) API.

API Contract:
- Endpoint: https://api.gst.gov.in/gst/returns/gstr1/{gstin}
- Method: GET
- Headers: Authorization: Bearer {api_key}
- Response: JSON with status, name, state, business_type
- Error Responses: 401 (Invalid API key), 404 (GSTIN not found), 429 (Rate limited), 503 (Service unavailable)

Status Mapping:
- HTTP 200 + status "active" + name match → VERIFIED
- HTTP 200 + status "active" + name mismatch → MISMATCH
- HTTP 200 + status != "active" → INCONCLUSIVE
- HTTP 401 → ERROR (no retry)
- HTTP 429 → ERROR (honor Retry-After, no retry)
- HTTP 5xx → UNAVAILABLE (after retries)
- Timeout → UNAVAILABLE (after retries)
"""
import os
import logging
from datetime import datetime, timezone
from typing import Optional

try:
    import httpx
except ImportError:
    httpx = None

from app.adapters.base import (
    PortalAdapter, VerificationClaim, VerificationResult,
    VerificationStatus, AdapterError
)
from app.services.name_matching import normalize_name, match_names

logger = logging.getLogger(__name__)


class GSTINAdapter(PortalAdapter):
    """Real GSTIN verification against GSTN API."""
    
    source_name = "GSTN"
    
    def __init__(self):
        """Initialize with GSTIN_API_KEY from environment."""
        self.api_key = os.getenv("GSTIN_API_KEY")
        self.enabled = self.api_key is not None
        
        if not self.enabled:
            logger.warning("GSTINAdapter: credential GSTIN_API_KEY not found — adapter disabled")
        elif not httpx:
            logger.error("GSTINAdapter: httpx library not installed, adapter disabled")
            self.enabled = False
        
        # GSTN API endpoint (production)
        self.base_url = "https://api.gst.gov.in/gst/returns"
        if httpx:
            self.http_client = httpx.AsyncClient(timeout=5.0)
    
    async def _verify_raw(self, claim: VerificationClaim) -> VerificationResult:
        """
        Verify GSTIN against GSTN API.
        
        Raises AdapterError on any technical failure (timeout, network error,
        malformed response, auth failure). Never returns MISMATCH on error.
        """
        if not self.enabled:
            raise AdapterError("GSTINAdapter disabled: credential not configured")
        
        if not httpx:
            raise AdapterError("httpx library not available")
        
        claimed_gstin = claim.claimed_value.strip().upper()
        
        # Validate GSTIN format (15 digits, alphanumeric)
        if not self._validate_gstin_format(claimed_gstin):
            return VerificationResult(
                source=self.source_name,
                status=VerificationStatus.MISMATCH,
                checked_at=datetime.now(timezone.utc),
                freshness_seconds=0,
                http_status_code=400,
                error=f"Invalid GSTIN format: {claimed_gstin}",
            )
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            
            response = await self.http_client.get(
                f"{self.base_url}/{claimed_gstin}",
                headers=headers,
            )
            
            logger.debug(f"GSTN API response: {response.status_code}")
            
            # Handle non-200 responses
            if response.status_code != 200:
                if response.status_code == 404:
                    # GSTIN not found in registry
                    return VerificationResult(
                        source=self.source_name,
                        status=VerificationStatus.INCONCLUSIVE,
                        checked_at=datetime.now(timezone.utc),
                        freshness_seconds=0,
                        http_status_code=404,
                        error="GSTIN not found in registry",
                    )
                elif response.status_code == 401:
                    raise AdapterError("Authentication failed (401): invalid API key")
                elif response.status_code == 429:
                    retry_after = response.headers.get("Retry-After", "60")
                    raise AdapterError(f"Rate limited (429): retry after {retry_after}s")
                else:
                    raise AdapterError(f"API error: {response.status_code}")
            
            # Parse successful response
            data = response.json()
            authority_name = data.get("name", "").strip()
            status_from_authority = data.get("status", "").lower()
            
            # Determine if record is valid (active status)
            if status_from_authority != "active":
                return VerificationResult(
                    source=self.source_name,
                    status=VerificationStatus.INCONCLUSIVE,
                    checked_at=datetime.now(timezone.utc),
                    freshness_seconds=0,
                    http_status_code=200,
                    authority_value=authority_name,
                    error=f"GSTIN status is '{status_from_authority}', not active",
                )
            
            # Perform name matching if entity_name provided
            match_result = "exact_match"
            match_score = 1.0
            
            if claim.entity_name:
                match_result, match_score = match_names(
                    claim.entity_name,
                    authority_name,
                    use_fuzzy=True,
                    fuzzy_threshold=0.85
                )
            
            # Determine final status based on name match
            if match_result in ("exact_match", "fuzzy_match"):
                status = VerificationStatus.VERIFIED
            else:
                status = VerificationStatus.MISMATCH
            
            return VerificationResult(
                source=self.source_name,
                status=status,
                checked_at=datetime.now(timezone.utc),
                freshness_seconds=3600,
                http_status_code=200,
                api_reference_id=claimed_gstin,
                authority_value=authority_name,
                authority_normalized_value=normalize_name(authority_name),
                document_normalized_value=normalize_name(claim.entity_name or ""),
                match_result=match_result,
                match_score=match_score,
                data={
                    "gstin": claimed_gstin,
                    "status": status_from_authority,
                    "state": data.get("state"),
                    "business_type": data.get("business_type"),
                },
                evidence=f"GSTN registry confirms GSTIN {claimed_gstin} is {status_from_authority}",
            )
        
        except httpx.TimeoutException:
            raise AdapterError("Request timed out")
        except httpx.ConnectError as e:
            raise AdapterError(f"Connection error: {str(e)}")
        except Exception as e:
            raise AdapterError(f"Unexpected error: {str(e)}")
    
    @staticmethod
    def _validate_gstin_format(gstin: str) -> bool:
        """Validate GSTIN format: 15 characters, alphanumeric."""
        if not gstin:
            return False
        # GSTIN: 2-digit state + 10-digit PAN + Z + 1-digit check digit = 15 chars
        if len(gstin) != 15:
            return False
        return gstin.isalnum()
