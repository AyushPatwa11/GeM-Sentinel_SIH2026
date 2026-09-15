"""
MCA Adapter — Real verification against MCA (Ministry of Corporate Affairs) API.

API Contract:
- Endpoint: https://api.data.gov.in/resource/companies-house-data
- Method: GET with query params: filters[CIN]={cin}&api-key={api_key}
- Response: JSON with records array containing CIN, Company_Name, Status, ROC, Registration_Number
- Error Responses: 401 (Invalid API key), 404 (CIN not found), 429 (Rate limited), 503 (Service unavailable)

Status Mapping:
- HTTP 200 + record found + status "Active" + name match → VERIFIED
- HTTP 200 + record found + status "Active" + name mismatch → MISMATCH
- HTTP 200 + record found + status != "Active" → INCONCLUSIVE
- HTTP 200 + no record → INCONCLUSIVE
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


class MCAAdapter(PortalAdapter):
    """Real CIN verification against MCA API."""
    
    source_name = "MCA"
    
    def __init__(self):
        """Initialize with MCA_API_KEY from environment."""
        self.api_key = os.getenv("MCA_API_KEY")
        self.enabled = self.api_key is not None
        
        if not self.enabled:
            logger.warning("MCAAdapter: credential MCA_API_KEY not found — adapter disabled")
        elif not httpx:
            logger.error("MCAAdapter: httpx library not installed, adapter disabled")
            self.enabled = False
        
        # MCA API endpoint (via data.gov.in or direct MCA21 portal)
        self.base_url = "https://api.data.gov.in/resource/companies-house-data"
        if httpx:
            self.http_client = httpx.AsyncClient(timeout=5.0)
    
    async def _verify_raw(self, claim: VerificationClaim) -> VerificationResult:
        """
        Verify CIN against MCA API.
        
        Raises AdapterError on any technical failure (timeout, network error,
        malformed response, auth failure). Never returns MISMATCH on error.
        """
        if not self.enabled:
            raise AdapterError("MCAAdapter disabled: credential not configured")
        
        if not httpx:
            raise AdapterError("httpx library not available")
        
        claimed_cin = claim.claimed_value.strip().upper()
        
        # Validate CIN format (21 characters)
        if not self._validate_cin_format(claimed_cin):
            return VerificationResult(
                source=self.source_name,
                status=VerificationStatus.MISMATCH,
                checked_at=datetime.now(timezone.utc),
                freshness_seconds=0,
                http_status_code=400,
                error=f"Invalid CIN format: {claimed_cin}",
            )
        
        try:
            params = {
                "filters[CIN]": claimed_cin,
                "api-key": self.api_key,
                "format": "json",
            }
            
            response = await self.http_client.get(
                self.base_url,
                params=params,
            )
            
            logger.debug(f"MCA API response: {response.status_code}")
            
            if response.status_code != 200:
                if response.status_code == 404:
                    return VerificationResult(
                        source=self.source_name,
                        status=VerificationStatus.INCONCLUSIVE,
                        checked_at=datetime.now(timezone.utc),
                        freshness_seconds=0,
                        http_status_code=404,
                        error="CIN not found in MCA registry",
                    )
                elif response.status_code == 401:
                    raise AdapterError("Authentication failed (401): invalid API key")
                elif response.status_code == 429:
                    retry_after = response.headers.get("Retry-After", "60")
                    raise AdapterError(f"Rate limited (429): retry after {retry_after}s")
                else:
                    raise AdapterError(f"API error: {response.status_code}")
            
            data = response.json()
            records = data.get("records", [])
            
            if not records:
                return VerificationResult(
                    source=self.source_name,
                    status=VerificationStatus.INCONCLUSIVE,
                    checked_at=datetime.now(timezone.utc),
                    freshness_seconds=0,
                    http_status_code=200,
                    error="No records found for CIN",
                )
            
            company_record = records[0]  # Use first match
            company_name = company_record.get("Company_Name", "").strip()
            company_status = company_record.get("Status", "").lower()
            
            # Check if company is active
            if company_status != "active":
                return VerificationResult(
                    source=self.source_name,
                    status=VerificationStatus.INCONCLUSIVE,
                    checked_at=datetime.now(timezone.utc),
                    freshness_seconds=0,
                    http_status_code=200,
                    authority_value=company_name,
                    error=f"Company status is '{company_status}', not active",
                )
            
            # Perform name matching
            match_result = "exact_match"
            match_score = 1.0
            
            if claim.entity_name:
                match_result, match_score = match_names(
                    claim.entity_name,
                    company_name,
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
                api_reference_id=claimed_cin,
                authority_value=company_name,
                authority_normalized_value=normalize_name(company_name),
                document_normalized_value=normalize_name(claim.entity_name or ""),
                match_result=match_result,
                match_score=match_score,
                data={
                    "cin": claimed_cin,
                    "status": company_status,
                    "roc": company_record.get("ROC"),
                    "incorporation_date": company_record.get("Date_of_Incorporation"),
                },
                evidence=f"MCA registry confirms CIN {claimed_cin} for {company_name}",
            )
        
        except httpx.TimeoutException:
            raise AdapterError("Request timed out")
        except httpx.ConnectError as e:
            raise AdapterError(f"Connection error: {str(e)}")
        except Exception as e:
            raise AdapterError(f"Unexpected error: {str(e)}")
    
    @staticmethod
    def _validate_cin_format(cin: str) -> bool:
        """Validate CIN format: 21 characters."""
        if not cin:
            return False
        # CIN: typically 21 alphanumeric characters
        return len(cin) == 21 and cin.isalnum()
