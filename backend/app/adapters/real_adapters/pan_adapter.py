"""
PAN Adapter — Real verification against Income Tax PAN verification service.

API Contract:
- Endpoint: https://incometaxindiaefiling.gov.in/e-filing/services/pan-verification
- Method: POST with JSON body: {pan, name, api_key}
- Response: JSON with status, pan, name, entity_type
- Error Responses: 401 (Invalid API key), 404 (PAN not found), 429 (Rate limited), 503 (Service unavailable)

Status Mapping:
- HTTP 200 + status "valid" + name match → VERIFIED
- HTTP 200 + status "valid" + name mismatch → MISMATCH
- HTTP 200 + status != "valid" → INCONCLUSIVE
- HTTP 401 → ERROR (no retry)
- HTTP 429 → ERROR (no retry)
- HTTP 5xx → UNAVAILABLE (after retries)
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


class PANAdapter(PortalAdapter):
    """Real PAN verification against Income Tax service."""
    
    source_name = "PAN"
    
    def __init__(self):
        """Initialize with PAN_API_KEY from environment."""
        self.api_key = os.getenv("PAN_API_KEY")
        self.enabled = self.api_key is not None
        
        if not self.enabled:
            logger.warning("PANAdapter: credential PAN_API_KEY not found — adapter disabled")
        elif not httpx:
            logger.error("PANAdapter: httpx library not installed, adapter disabled")
            self.enabled = False
        
        # Income Tax PAN Verification Webservice endpoint
        self.base_url = "https://incometaxindiaefiling.gov.in/e-filing/services/pan-verification"
        if httpx:
            self.http_client = httpx.AsyncClient(timeout=5.0)
    
    async def _verify_raw(self, claim: VerificationClaim) -> VerificationResult:
        """
        Verify PAN against Income Tax registry.
        
        Raises AdapterError on any technical failure (timeout, network error,
        malformed response, auth failure). Never returns MISMATCH on error.
        """
        if not self.enabled:
            raise AdapterError("PANAdapter disabled: credential not configured")
        
        if not httpx:
            raise AdapterError("httpx library not available")
        
        claimed_pan = claim.claimed_value.strip().upper()
        
        # Validate PAN format (10 characters)
        if not self._validate_pan_format(claimed_pan):
            return VerificationResult(
                source=self.source_name,
                status=VerificationStatus.MISMATCH,
                checked_at=datetime.now(timezone.utc),
                freshness_seconds=0,
                http_status_code=400,
                error=f"Invalid PAN format: {claimed_pan}",
            )
        
        try:
            headers = {
                "Content-Type": "application/json",
            }
            
            payload = {
                "pan": claimed_pan,
                "name": claim.entity_name or "",
                "api_key": self.api_key,
            }
            
            response = await self.http_client.post(
                self.base_url,
                json=payload,
                headers=headers,
            )
            
            logger.debug(f"PAN API response: {response.status_code}")
            
            if response.status_code != 200:
                if response.status_code == 404:
                    return VerificationResult(
                        source=self.source_name,
                        status=VerificationStatus.INCONCLUSIVE,
                        checked_at=datetime.now(timezone.utc),
                        freshness_seconds=0,
                        http_status_code=404,
                        error="PAN not found in IT registry",
                    )
                elif response.status_code == 401:
                    raise AdapterError("Authentication failed (401): invalid API key")
                elif response.status_code == 429:
                    retry_after = response.headers.get("Retry-After", "60")
                    raise AdapterError(f"Rate limited (429): retry after {retry_after}s")
                else:
                    raise AdapterError(f"API error: {response.status_code}")
            
            data = response.json()
            api_status = data.get("status", "").lower()
            
            if api_status != "valid":
                return VerificationResult(
                    source=self.source_name,
                    status=VerificationStatus.INCONCLUSIVE,
                    checked_at=datetime.now(timezone.utc),
                    freshness_seconds=0,
                    http_status_code=200,
                    error=f"PAN status is '{api_status}', not valid",
                )
            
            it_person_name = data.get("name", "").strip()
            
            # Perform name matching
            match_result = "exact_match"
            match_score = 1.0
            
            if claim.entity_name:
                match_result, match_score = match_names(
                    claim.entity_name,
                    it_person_name,
                    use_fuzzy=True,
                    fuzzy_threshold=0.85
                )
            
            # Determine final status
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
                api_reference_id=claimed_pan,
                authority_value=it_person_name,
                authority_normalized_value=normalize_name(it_person_name),
                document_normalized_value=normalize_name(claim.entity_name or ""),
                match_result=match_result,
                match_score=match_score,
                data={
                    "pan": claimed_pan,
                    "entity_type": data.get("entity_type"),
                },
                evidence=f"IT registry confirms PAN {claimed_pan} for {it_person_name}",
            )
        
        except httpx.TimeoutException:
            raise AdapterError("Request timed out")
        except httpx.ConnectError as e:
            raise AdapterError(f"Connection error: {str(e)}")
        except Exception as e:
            raise AdapterError(f"Unexpected error: {str(e)}")
    
    @staticmethod
    def _validate_pan_format(pan: str) -> bool:
        """Validate PAN format: 10 alphanumeric characters."""
        if not pan:
            return False
        return len(pan) == 10 and pan.isalnum()
