"""Adapter orchestration service for Phase 4 - coordinates verification across sources."""
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class AdapterStatus(str, Enum):
    """Adapter status constants."""
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"  
    DEGRADED = "DEGRADED"
    MOCK = "MOCK"  # Label for non-live integrations


@dataclass
class AdapterConfig:
    """Configuration for a verification adapter."""
    name: str
    status: AdapterStatus = AdapterStatus.AVAILABLE
    timeout_seconds: int = 30
    retry_count: int = 2
    is_live: bool = False  # True only if real credentials/endpoints verified
    supported_fields: List[str] = None
    label: str = "MOCK"  # MOCK, SANDBOX, SYNTHETIC, UNAVAILABLE, LIVE
    
    def __post_init__(self):
        if self.supported_fields is None:
            self.supported_fields = []


class VerificationResult:
    """Standard verification result format."""
    
    def __init__(
        self,
        adapter_name: str,
        status: str,
        evidence: Optional[str] = None,
        error: Optional[str] = None,
        response_time_ms: int = 0,
        checked_at: Optional[datetime] = None,
    ):
        self.adapter_name = adapter_name
        self.status = status
        self.evidence = evidence
        self.error = error
        self.response_time_ms = response_time_ms
        self.checked_at = checked_at or datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for storage."""
        return {
            "adapter_source": self.adapter_name,
            "status": self.status,
            "evidence": self.evidence,
            "error": self.error,
            "response_time_ms": self.response_time_ms,
            "checked_at": self.checked_at.isoformat(),
        }


class AdapterOrchestrator:
    """Orchestrate verification calls across multiple adapters."""
    
    # Adapter configurations (MOCK by default - change label to LIVE when credentials verified)
    ADAPTERS = {
        "GSTN": AdapterConfig(
            name="GSTN",
            status=AdapterStatus.MOCK,
            timeout_seconds=30,
            supported_fields=["gst_number", "legal_name"],
            label="MOCK",  # Change to LIVE after credential verification
        ),
        "MCA": AdapterConfig(
            name="MCA",
            status=AdapterStatus.MOCK,
            timeout_seconds=30,
            supported_fields=["cin", "director_name", "company_name"],
            label="MOCK",  # Change to LIVE after credential verification
        ),
        "NSIC": AdapterConfig(
            name="NSIC",
            status=AdapterStatus.MOCK,
            timeout_seconds=30,
            supported_fields=["nsic_number"],
            label="MOCK",  # Change to LIVE after credential verification
        ),
        "UDYAM": AdapterConfig(
            name="UDYAM",
            status=AdapterStatus.MOCK,
            timeout_seconds=30,
            supported_fields=["udyam_number"],
            label="MOCK",  # Change to LIVE after credential verification
        ),
        "DIGILOCKER": AdapterConfig(
            name="DIGILOCKER",
            status=AdapterStatus.MOCK,
            timeout_seconds=30,
            supported_fields=["document_hash"],
            label="MOCK",  # Change to LIVE after credential verification
        ),
    }
    
    @staticmethod
    async def verify_field(
        field_name: str,
        field_value: str,
        adapter_name: Optional[str] = None,
    ) -> VerificationResult:
        """Verify a single field value using specified adapter.
        
        Args:
            field_name: Name of field (gst_number, pan, cin, etc.)
            field_value: Value to verify
            adapter_name: Specific adapter to use, or None for auto-select
            
        Returns:
            VerificationResult with status and evidence
        """
        if not adapter_name:
            adapter_name = AdapterOrchestrator._select_adapter_for_field(field_name)
        
        adapter_config = AdapterOrchestrator.ADAPTERS.get(adapter_name)
        if not adapter_config:
            return VerificationResult(
                adapter_name=adapter_name,
                status="UNAVAILABLE",
                error=f"Adapter {adapter_name} not found",
            )
        
        if adapter_config.status == AdapterStatus.UNAVAILABLE:
            return VerificationResult(
                adapter_name=adapter_name,
                status="UNAVAILABLE",
                error=f"Adapter {adapter_name} is {adapter_config.label}",
            )
        
        # Call appropriate adapter with timeout handling
        start_time = datetime.utcnow()
        
        try:
            result = await asyncio.wait_for(
                AdapterOrchestrator._call_adapter(
                    adapter_name,
                    field_name,
                    field_value,
                ),
                timeout=adapter_config.timeout_seconds,
            )
            
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            result.response_time_ms = int(response_time)
            
            return result
            
        except asyncio.TimeoutError:
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return VerificationResult(
                adapter_name=adapter_name,
                status="UNAVAILABLE",
                error=f"Adapter timeout after {adapter_config.timeout_seconds}s",
                response_time_ms=int(response_time),
            )
        except Exception as e:
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return VerificationResult(
                adapter_name=adapter_name,
                status="UNAVAILABLE",
                error=str(e),
                response_time_ms=int(response_time),
            )
    
    @staticmethod
    async def verify_bid_fields(
        bid_data: Dict[str, str],
        priority_adapters: Optional[List[str]] = None,
    ) -> List[VerificationResult]:
        """Verify multiple fields for a bid using appropriate adapters.
        
        Args:
            bid_data: Dict of field_name -> field_value
            priority_adapters: List of adapters to prioritize (optional)
            
        Returns:
            List of VerificationResult objects
        """
        tasks = []
        
        for field_name, field_value in bid_data.items():
            adapter = AdapterOrchestrator._select_adapter_for_field(field_name)
            if priority_adapters and adapter not in priority_adapters:
                adapter = priority_adapters[0] if priority_adapters else adapter
            
            tasks.append(
                AdapterOrchestrator.verify_field(field_name, field_value, adapter)
            )
        
        # Execute verifications in parallel with proper error handling
        results = await asyncio.gather(*tasks, return_exceptions=False)
        
        return [r for r in results if isinstance(r, VerificationResult)]
    
    @staticmethod
    async def _call_adapter(
        adapter_name: str,
        field_name: str,
        field_value: str,
    ) -> VerificationResult:
        """Call specific adapter (mock or live).
        
        Args:
            adapter_name: Adapter to call
            field_name: Field being verified
            field_value: Value to verify
            
        Returns:
            VerificationResult
        """
        adapter_config = AdapterOrchestrator.ADAPTERS.get(adapter_name)
        
        if not adapter_config or adapter_config.label != "LIVE":
            # Return mock result for non-live adapters
            return AdapterOrchestrator._mock_adapter_response(
                adapter_name,
                field_name,
                field_value,
            )
        
        # Real adapter calls would go here
        # For now, all are MOCK
        return AdapterOrchestrator._mock_adapter_response(
            adapter_name,
            field_name,
            field_value,
        )
    
    @staticmethod
    def _mock_adapter_response(
        adapter_name: str,
        field_name: str,
        field_value: str,
    ) -> VerificationResult:
        """Generate mock adapter response for testing."""
        # Simulate realistic responses based on field type
        
        if adapter_name == "GSTN":
            if field_name == "gst_number" and len(field_value) == 15:
                return VerificationResult(
                    adapter_name=adapter_name,
                    status="VERIFIED",
                    evidence=f"GST Registration found: {field_value} - Status: Active",
                )
            else:
                return VerificationResult(
                    adapter_name=adapter_name,
                    status="MISMATCH",
                    evidence="GST number format invalid or not found",
                )
        
        elif adapter_name == "MCA":
            if field_name == "cin":
                return VerificationResult(
                    adapter_name=adapter_name,
                    status="VERIFIED",
                    evidence=f"Company found in MCA register: {field_value}",
                )
            else:
                return VerificationResult(
                    adapter_name=adapter_name,
                    status="INCONCLUSIVE",
                    evidence="Field not directly verifiable via MCA",
                )
        
        elif adapter_name == "UDYAM":
            if field_name == "udyam_number":
                return VerificationResult(
                    adapter_name=adapter_name,
                    status="VERIFIED",
                    evidence=f"Udyam registration found: {field_value}",
                )
            else:
                return VerificationResult(
                    adapter_name=adapter_name,
                    status="INCONCLUSIVE",
                    evidence="Not a Udyam field",
                )
        
        else:
            # Default mock response
            return VerificationResult(
                adapter_name=adapter_name,
                status="NOT_REQUIRED",
                evidence=f"Verification via {adapter_name} not applicable for {field_name}",
            )
    
    @staticmethod
    def _select_adapter_for_field(field_name: str) -> str:
        """Select best adapter for a field.
        
        Args:
            field_name: Field name to verify
            
        Returns:
            Adapter name
        """
        field_lower = field_name.lower()
        
        if "gst" in field_lower:
            return "GSTN"
        elif "pan" in field_lower:
            return "GSTN"  # PAN can be verified via GSTN
        elif "cin" in field_lower or "director" in field_lower:
            return "MCA"
        elif "company" in field_lower:
            return "MCA"
        elif "udyam" in field_lower:
            return "UDYAM"
        elif "nsic" in field_lower:
            return "NSIC"
        elif "document" in field_lower or "hash" in field_lower:
            return "DIGILOCKER"
        else:
            return "GSTN"  # Default
    
    @staticmethod
    def get_adapter_status() -> Dict[str, Dict[str, Any]]:
        """Get status of all adapters.
        
        Returns:
            Dict with status of each adapter
        """
        return {
            name: {
                "status": config.status.value,
                "label": config.label,
                "is_live": config.label == "LIVE",
                "supported_fields": config.supported_fields,
                "timeout_seconds": config.timeout_seconds,
            }
            for name, config in AdapterOrchestrator.ADAPTERS.items()
        }
    
    @staticmethod
    def normalize_verification_result(
        raw_result: Dict[str, Any],
        adapter_name: str,
    ) -> str:
        """Normalize adapter response to standard status.
        
        Args:
            raw_result: Raw adapter response
            adapter_name: Adapter that returned result
            
        Returns:
            Normalized status (VERIFIED, MISMATCH, INCONCLUSIVE, UNAVAILABLE, etc.)
        """
        status = raw_result.get("status", "INCONCLUSIVE")
        
        # Normalize common status values
        status_map = {
            "success": "VERIFIED",
            "found": "VERIFIED",
            "active": "VERIFIED",
            "match": "VERIFIED",
            "verified": "VERIFIED",
            "not_found": "MISMATCH",
            "error": "UNAVAILABLE",
            "timeout": "UNAVAILABLE",
            "invalid": "MISMATCH",
        }
        
        normalized = status_map.get(status.lower(), status)
        
        # Ensure standard statuses
        valid_statuses = {
            "VERIFIED",
            "MISMATCH",
            "INCONCLUSIVE",
            "UNAVAILABLE",
            "PENDING",
            "NOT_REQUIRED",
        }
        
        if normalized not in valid_statuses:
            normalized = "INCONCLUSIVE"
        
        return normalized
