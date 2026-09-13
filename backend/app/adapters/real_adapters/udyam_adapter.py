"""
UDYAM Adapter — Real verification against UDYAM registration portal.

Currently a placeholder. Full implementation pending UDYAM API documentation.
"""
import os
import logging
from datetime import datetime, timezone

from app.adapters.base import (
    PortalAdapter, VerificationClaim, VerificationResult,
    VerificationStatus, AdapterError
)

logger = logging.getLogger(__name__)


class UDYAMAdapter(PortalAdapter):
    """Real UDYAM verification (placeholder)."""
    
    source_name = "UDYAM"
    
    def __init__(self):
        """Initialize with UDYAM_API_KEY from environment."""
        self.api_key = os.getenv("UDYAM_API_KEY")
        self.enabled = self.api_key is not None
        
        if not self.enabled:
            logger.warning("UDYAMAdapter: credential UDYAM_API_KEY not found — adapter disabled")
    
    async def _verify_raw(self, claim: VerificationClaim) -> VerificationResult:
        """
        Verify UDYAM number against UDYAM API.
        
        Placeholder: returns UNAVAILABLE until API contract documented.
        """
        if not self.enabled:
            raise AdapterError("UDYAMAdapter disabled: credential not configured")
        
        # TODO: Implement once UDYAM API contract is available
        raise AdapterError("UDYAM API integration not yet implemented")
