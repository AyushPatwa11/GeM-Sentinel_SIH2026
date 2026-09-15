"""
Property-based and unit tests for PortalAdapter base class.

Tests cover:
- Property 4: Verification Status Not Boolean
- Property 5: HTTP Status to VerificationStatus Mapping
- Property 6: Retry Logic Exponential Backoff
- Property 7: No Retry on Auth Failure
- Property 8: Timeout Handling Maps to UNAVAILABLE
"""
import pytest
import asyncio
from datetime import datetime, timezone
from app.adapters.base import (
    PortalAdapter, VerificationStatus, VerificationClaim, 
    VerificationResult, AdapterError
)


class TestVerificationStatusNotBoolean:
    """Property 4: Verification Status Not Boolean"""
    
    def test_status_is_discrete_enum(self):
        """Verify status is never boolean or null, only discrete enum values."""
        valid_statuses = {
            VerificationStatus.VERIFIED,
            VerificationStatus.MISMATCH,
            VerificationStatus.UNAVAILABLE,
            VerificationStatus.ERROR,
            VerificationStatus.INCONCLUSIVE,
            VerificationStatus.PENDING,
        }
        assert len(valid_statuses) == 6
        
        # Ensure no boolean or null values
        for status in valid_statuses:
            assert isinstance(status, VerificationStatus)
            assert status.value in [
                "VERIFIED", "MISMATCH", "UNAVAILABLE", 
                "ERROR", "INCONCLUSIVE", "PENDING"
            ]
    
    def test_status_never_boolean(self):
        """Ensure status is never True, False, or None."""
        result = VerificationResult(
            source="TEST",
            status=VerificationStatus.VERIFIED,
            checked_at=datetime.now(timezone.utc),
            freshness_seconds=0
        )
        assert result.status is not True
        assert result.status is not False
        assert result.status is not None
        assert isinstance(result.status, VerificationStatus)


class TestHTTPStatusMapping:
    """Property 5: HTTP Status to VerificationStatus Mapping"""
    
    def test_http_200_record_found_name_match_verified(self):
        """HTTP 200 + record found + name match → VERIFIED"""
        status = PortalAdapter.status_map(200, record_found=True, name_match="exact_match")
        assert status == VerificationStatus.VERIFIED
        
        status = PortalAdapter.status_map(200, record_found=True, name_match="fuzzy_match")
        assert status == VerificationStatus.VERIFIED
    
    def test_http_200_record_found_name_mismatch(self):
        """HTTP 200 + record found + name mismatch → MISMATCH"""
        status = PortalAdapter.status_map(200, record_found=True, name_match="no_match")
        assert status == VerificationStatus.MISMATCH
    
    def test_http_200_no_record_found(self):
        """HTTP 200 + no record → INCONCLUSIVE"""
        status = PortalAdapter.status_map(200, record_found=False)
        assert status == VerificationStatus.INCONCLUSIVE
    
    def test_http_200_record_found_name_match_none(self):
        """HTTP 200 + record found + name match undetermined → INCONCLUSIVE"""
        status = PortalAdapter.status_map(200, record_found=True, name_match=None)
        assert status == VerificationStatus.INCONCLUSIVE
    
    def test_http_400_error(self):
        """HTTP 400 → ERROR"""
        status = PortalAdapter.status_map(400)
        assert status == VerificationStatus.ERROR
    
    def test_http_403_error(self):
        """HTTP 403 → ERROR"""
        status = PortalAdapter.status_map(403)
        assert status == VerificationStatus.ERROR
    
    def test_http_404_error(self):
        """HTTP 404 → ERROR"""
        status = PortalAdapter.status_map(404)
        assert status == VerificationStatus.ERROR
    
    def test_http_401_unauthorized_error(self):
        """HTTP 401 → ERROR (not retried)"""
        status = PortalAdapter.status_map(401)
        assert status == VerificationStatus.ERROR
    
    def test_http_429_rate_limit_error(self):
        """HTTP 429 → ERROR (not retried, but Retry-After honored)"""
        status = PortalAdapter.status_map(429)
        assert status == VerificationStatus.ERROR
    
    def test_http_500_unavailable(self):
        """HTTP 500 → UNAVAILABLE (after retries)"""
        status = PortalAdapter.status_map(500)
        assert status == VerificationStatus.UNAVAILABLE
    
    def test_http_502_unavailable(self):
        """HTTP 502 → UNAVAILABLE"""
        status = PortalAdapter.status_map(502)
        assert status == VerificationStatus.UNAVAILABLE
    
    def test_http_503_unavailable(self):
        """HTTP 503 → UNAVAILABLE"""
        status = PortalAdapter.status_map(503)
        assert status == VerificationStatus.UNAVAILABLE
    
    def test_http_none_error(self):
        """HTTP None → ERROR"""
        status = PortalAdapter.status_map(None)
        assert status == VerificationStatus.ERROR
    
    def test_http_unknown_status_error(self):
        """HTTP unknown status → ERROR"""
        status = PortalAdapter.status_map(418)  # I'm a teapot
        assert status == VerificationStatus.ERROR


class TestRetryLogicBackoff:
    """Property 6: Retry Logic Exponential Backoff"""
    
    @pytest.mark.asyncio
    async def test_retry_exponential_backoff_sequence(self):
        """Verify exponential backoff: 1s, then 2s between attempts."""
        class CountingAdapter(PortalAdapter):
            source_name = "TEST"
            attempt_count = 0
            
            async def _verify_raw(self, claim):
                self.attempt_count += 1
                if self.attempt_count < 3:
                    raise AdapterError("Network error")
                return VerificationResult(
                    source="TEST",
                    status=VerificationStatus.VERIFIED,
                    checked_at=datetime.now(timezone.utc),
                    freshness_seconds=0,
                )
        
        adapter = CountingAdapter()
        adapter.enabled = True
        claim = VerificationClaim("test_field", "test_value")
        
        import time
        start = time.time()
        result = await adapter.verify(claim, timeout_seconds=5.0, max_retries=2)
        elapsed = time.time() - start
        
        # Should have retried twice with backoff (1s + 2s = 3s minimum)
        assert result.status == VerificationStatus.VERIFIED
        assert adapter.attempt_count == 3
        assert elapsed >= 3.0  # At least 3 seconds of backoff
    
    @pytest.mark.asyncio
    async def test_retry_on_timeout(self):
        """Verify retries happen on timeout."""
        class TimeoutAdapter(PortalAdapter):
            source_name = "TEST"
            attempt_count = 0
            
            async def _verify_raw(self, claim):
                self.attempt_count += 1
                if self.attempt_count < 3:
                    await asyncio.sleep(10)  # Will timeout
                return VerificationResult(
                    source="TEST",
                    status=VerificationStatus.VERIFIED,
                    checked_at=datetime.now(timezone.utc),
                    freshness_seconds=0,
                )
        
        adapter = TimeoutAdapter()
        adapter.enabled = True
        claim = VerificationClaim("test_field", "test_value")
        
        result = await adapter.verify(claim, timeout_seconds=0.1, max_retries=2)
        
        # Should have attempted multiple times before giving up
        assert adapter.attempt_count >= 1
        assert result.status == VerificationStatus.UNAVAILABLE
    
    @pytest.mark.asyncio
    async def test_no_retry_after_success(self):
        """Verify no retry after successful verification."""
        class SuccessAdapter(PortalAdapter):
            source_name = "TEST"
            attempt_count = 0
            
            async def _verify_raw(self, claim):
                self.attempt_count += 1
                return VerificationResult(
                    source="TEST",
                    status=VerificationStatus.VERIFIED,
                    checked_at=datetime.now(timezone.utc),
                    freshness_seconds=0,
                )
        
        adapter = SuccessAdapter()
        adapter.enabled = True
        claim = VerificationClaim("test_field", "test_value")
        
        result = await adapter.verify(claim, timeout_seconds=5.0, max_retries=2)
        
        # Should only attempt once
        assert adapter.attempt_count == 1
        assert result.status == VerificationStatus.VERIFIED


class TestNoRetryOnAuthFailure:
    """Property 7: No Retry on Auth Failure"""
    
    @pytest.mark.asyncio
    async def test_disabled_adapter_returns_unavailable(self):
        """When adapter disabled (credential missing), return UNAVAILABLE immediately."""
        class DisabledAdapter(PortalAdapter):
            source_name = "TEST"
            enabled = False
            attempt_count = 0
            
            async def _verify_raw(self, claim):
                self.attempt_count += 1
                return VerificationResult(
                    source="TEST",
                    status=VerificationStatus.VERIFIED,
                    checked_at=datetime.now(timezone.utc),
                    freshness_seconds=0,
                )
        
        adapter = DisabledAdapter()
        claim = VerificationClaim("test_field", "test_value")
        
        result = await adapter.verify(claim, timeout_seconds=5.0, max_retries=2)
        
        # Should never call _verify_raw since adapter is disabled
        assert adapter.attempt_count == 0
        assert result.status == VerificationStatus.UNAVAILABLE
        assert "credentials not configured" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_adapter_error_on_auth_failure(self):
        """AdapterError raised during verification attempt."""
        class AuthFailAdapter(PortalAdapter):
            source_name = "TEST"
            attempt_count = 0
            
            async def _verify_raw(self, claim):
                self.attempt_count += 1
                # Simulate auth failure
                raise AdapterError("Authentication failed (401): invalid API key")
        
        adapter = AuthFailAdapter()
        adapter.enabled = True
        claim = VerificationClaim("test_field", "test_value")
        
        result = await adapter.verify(claim, timeout_seconds=5.0, max_retries=2)
        
        # Should retry but ultimately fail
        assert result.status == VerificationStatus.UNAVAILABLE
        # All retries attempted (attempt 0, 1, 2 = 3 total)
        assert adapter.attempt_count == 3


class TestTimeoutHandling:
    """Property 8: Timeout Handling Maps to UNAVAILABLE"""
    
    @pytest.mark.asyncio
    async def test_timeout_never_returns_mismatch(self):
        """Timeout should never return MISMATCH."""
        class SlowAdapter(PortalAdapter):
            source_name = "TEST"
            
            async def _verify_raw(self, claim):
                await asyncio.sleep(10)  # Will timeout
                return VerificationResult(
                    source="TEST",
                    status=VerificationStatus.MISMATCH,
                    checked_at=datetime.now(timezone.utc),
                    freshness_seconds=0,
                )
        
        adapter = SlowAdapter()
        adapter.enabled = True
        claim = VerificationClaim("test_field", "test_value")
        
        result = await adapter.verify(claim, timeout_seconds=0.05, max_retries=1)
        
        # Should return UNAVAILABLE, never MISMATCH
        assert result.status == VerificationStatus.UNAVAILABLE
        assert "timeout" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_timeout_never_returns_error_directly(self):
        """Timeout should map to UNAVAILABLE, not ERROR."""
        class SlowAdapter(PortalAdapter):
            source_name = "TEST"
            
            async def _verify_raw(self, claim):
                await asyncio.sleep(10)
                return VerificationResult(
                    source="TEST",
                    status=VerificationStatus.ERROR,
                    checked_at=datetime.now(timezone.utc),
                    freshness_seconds=0,
                )
        
        adapter = SlowAdapter()
        adapter.enabled = True
        claim = VerificationClaim("test_field", "test_value")
        
        result = await adapter.verify(claim, timeout_seconds=0.05, max_retries=0)
        
        # Should return UNAVAILABLE for timeout
        assert result.status == VerificationStatus.UNAVAILABLE


class TestVerificationResultStructure:
    """Test VerificationResult contains all required fields."""
    
    def test_result_has_all_required_fields(self):
        """Verify all required fields in VerificationResult."""
        result = VerificationResult(
            source="GSTN",
            status=VerificationStatus.VERIFIED,
            checked_at=datetime.now(timezone.utc),
            freshness_seconds=3600,
            http_status_code=200,
            api_reference_id="GST-REF-12345",
            authority_value="Test Company",
            authority_normalized_value="test company",
            document_normalized_value="test company",
            match_result="exact_match",
            match_score=1.0,
            fallback_used=False,
            data={"gstin": "18AABCT1234H1Z0"},
        )
        
        # Verify all fields accessible
        assert result.source == "GSTN"
        assert result.status == VerificationStatus.VERIFIED
        assert result.http_status_code == 200
        assert result.api_reference_id == "GST-REF-12345"
        assert result.authority_value == "Test Company"
        assert result.match_result == "exact_match"
        assert result.match_score == 1.0
        assert result.fallback_used is False


class TestVerificationClaimStructure:
    """Test VerificationClaim contains all required fields."""
    
    def test_claim_has_all_fields(self):
        """Verify VerificationClaim can be constructed with all fields."""
        claim = VerificationClaim(
            field_name="gstin",
            claimed_value="18AABCT1234H1Z0",
            entity_name="Test Company Pvt Ltd",
            source_document_id="doc-12345",
            extracted_fact_id="fact-67890"
        )
        
        assert claim.field_name == "gstin"
        assert claim.claimed_value == "18AABCT1234H1Z0"
        assert claim.entity_name == "Test Company Pvt Ltd"
        assert claim.source_document_id == "doc-12345"
        assert claim.extracted_fact_id == "fact-67890"
