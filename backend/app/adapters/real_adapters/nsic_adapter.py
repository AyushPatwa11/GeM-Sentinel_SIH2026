"""
NSIC Adapter — Real verification against NSIC verification service.

Currently a placeholder. Full implementation pending NSIC API documentation.
"""
import os
import logging
from datetime import datetime, timezone

from app.adapters.base import (
    PortalAdapter, VerificationClaim, VerificationResult,
    VerificationStatus, AdapterError
)

logger = logging.getLogger(__name__)


class NSICAdapter(PortalAdapter):
    """Real NSIC verification (placeholder)."""
    
    source_name = "NSIC"
    
    def __init__(self):
        """Initialize with NSIC_API_KEY from environment."""
        self.api_key = os.getenv("NSIC_API_KEY")
        self.enabled = self.api_key is not None
        
        if not self.enabled:
            logger.warning("NSICAdapter: credential NSIC_API_KEY not found — adapter disabled")
    
    async def _verify_raw(self, claim: VerificationClaim) -> VerificationResult:
        """
        Verify NSIC number against NSIC API.
        
        Placeholder: returns UNAVAILABLE until API contract documented.
        """
        if not self.enabled:
            raise AdapterError("NSICAdapter disabled: credential not configured")
        
        # TODO: Implement once NSIC API contract is available
        raise AdapterError("NSIC API integration not yet implemented")
