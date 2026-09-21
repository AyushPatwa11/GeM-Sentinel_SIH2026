"""
Registry mapping each verifiable field to its ONE designated authoritative
source (claim-level source authority, per locked design — no single portal
is "most trusted for everything").

This module is the entire swap surface: to go from mock to real, only
environment variables and ADAPTER_REGISTRY changes here. Nothing in the rule engine, 
risk engine, or API layer references adapters directly.

Credential Injection Pattern:
- Real adapters enabled only if corresponding environment variable is set
- Missing credential → adapter.enabled = False → returns UNAVAILABLE immediately
- No adapter instantiation unless credential available
- Fallback to Mock_Adapter on Real adapter failure (AdapterError)
"""
from __future__ import annotations

import os
import logging
from typing import Dict, Optional

from app.adapters.base import AdapterError, PortalAdapter, VerificationClaim
from app.adapters.datagovin_client import DataGovInMCAAdapter
from app.adapters.mock_adapters import (
    BlacklistMockAdapter,
    DigiLockerMockAdapter,
    GSTNMockAdapter,
    NSICMockAdapter,
    UdyamMockAdapter,
)

logger = logging.getLogger(__name__)


class UnavailableAdapter(PortalAdapter):
    """Explicit provider boundary for modes that are not configured."""

    def __init__(self, source_name: str, mode: str, reason: str):
        self.source_name = source_name
        self.integration_mode = mode
        self.unavailable_reason = reason
        self.enabled = False

    async def _verify_raw(self, claim: VerificationClaim):
        raise AdapterError(self.unavailable_reason)

# field_name -> authoritative source name
CLAIM_AUTHORITY_MAP = {
    "gstin": "GSTN",
    "gst_return_status": "GSTN",
    "cin": "MCA",
    "incorporation_status": "MCA",
    "nsic_number": "NSIC",
    "udyam_number": "UDYAM",
    "debarment_status": "BLACKLIST",
    "document_authenticity": "DIGILOCKER",
    "pan": "PAN",
}


class RegistryManager:
    """
    Central registry for all adapter implementations.
    This is the ONLY location where Real/Mock adapters are selected.
    
    Singleton pattern: One instance per application lifetime.
    Initialized at startup based on environment variables.
    """
    
    _instance: Optional['RegistryManager'] = None
    _adapter_registry: Dict[str, PortalAdapter] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize adapters at startup based on environment variables."""
        
        logger.info("Initializing adapter registry...")
        
        # Try to import Real_Adapters (may not be available yet if not created)
        try:
            from app.adapters.real_adapters.gstin_adapter import GSTINAdapter
            from app.adapters.real_adapters.mca_adapter import MCAAdapter
            from app.adapters.real_adapters.pan_adapter import PANAdapter
            from app.adapters.real_adapters.nsic_adapter import NSICAdapter
            from app.adapters.real_adapters.udyam_adapter import UDYAMAdapter
        except ImportError:
            logger.warning("Real adapters not available, using mock adapters only")
            GSTINAdapter = None
            MCAAdapter = None
            PANAdapter = None
            NSICAdapter = None
            UDYAMAdapter = None
        
        # Initialize GSTN adapter
        self._adapter_registry["GSTN"] = self._select_adapter(
            "GSTN", 
            GSTINAdapter if GSTINAdapter else None, 
            GSTNMockAdapter(), 
            "GSTIN_API_KEY"
        )
        
        # Initialize MCA adapter
        self._adapter_registry["MCA"] = self._select_adapter(
            "MCA", 
            MCAAdapter if MCAAdapter else None, 
            DataGovInMCAAdapter(), 
            "MCA_API_KEY"
        )
        
        # Initialize NSIC adapter
        self._adapter_registry["NSIC"] = self._select_adapter(
            "NSIC", 
            NSICAdapter if NSICAdapter else None, 
            NSICMockAdapter(), 
            "NSIC_API_KEY"
        )
        
        # Initialize UDYAM adapter
        self._adapter_registry["UDYAM"] = self._select_adapter(
            "UDYAM", 
            UDYAMAdapter if UDYAMAdapter else None, 
            UdyamMockAdapter(), 
            "UDYAM_API_KEY"
        )
        
        # Initialize PAN adapter
        self._adapter_registry["PAN"] = self._select_adapter(
            "PAN", 
            PANAdapter if PANAdapter else None, 
            GSTNMockAdapter(),  # Fallback to mock for now
            "PAN_API_KEY"
        )
        
        # Initialize non-credential-gated adapters
        self._adapter_registry["DIGILOCKER"] = DigiLockerMockAdapter()
        self._adapter_registry["DIGILOCKER"].integration_mode = "MOCK"
        self._adapter_registry["BLACKLIST"] = BlacklistMockAdapter()
        self._adapter_registry["BLACKLIST"].integration_mode = "MOCK"
        
        logger.info("Adapter registry initialized")
        self._log_adapter_status()
    
    @staticmethod
    def _select_adapter(
        source_name: str,
        real_adapter_class,
        mock_adapter_instance,
        env_var_name: str
    ) -> PortalAdapter:
        """
        Select between Real and Mock adapter based on credential availability.
        
        Logic:
        • If env var is set → use Real_Adapter (if class available)
        • If env var is not set → use Mock_Adapter (fallback)
        """
        
        configured_mode = os.getenv("VERIFICATION_ADAPTER_MODE", "MOCK").strip().upper()
        if configured_mode not in {"LIVE", "SANDBOX", "MOCK", "UNAVAILABLE"}:
            raise ValueError(
                "VERIFICATION_ADAPTER_MODE must be one of LIVE, SANDBOX, MOCK, or UNAVAILABLE"
            )

        if configured_mode == "UNAVAILABLE":
            return UnavailableAdapter(
                source_name,
                configured_mode,
                "Provider explicitly disabled by VERIFICATION_ADAPTER_MODE",
            )

        if configured_mode in {"SANDBOX", "LIVE"} and not os.getenv(env_var_name):
            return UnavailableAdapter(
                source_name,
                configured_mode,
                f"{configured_mode} provider is unavailable: {env_var_name} is not configured",
            )

        if configured_mode == "MOCK":
            mock_adapter_instance.integration_mode = "MOCK"
            mock_adapter_instance.status_note = "Synthetic fixture data; not an authority response"
            return mock_adapter_instance

        if os.getenv(env_var_name):
            if real_adapter_class:
                try:
                    adapter = real_adapter_class()
                    logger.info(f"[{source_name:8s}] ENABLED (Real adapter, credential found)")
                    adapter.integration_mode = "LIVE"
                    return adapter
                except Exception as e:
                    logger.error(f"[{source_name:8s}] Failed to init Real adapter: {e}")
                    return UnavailableAdapter(
                        source_name,
                        configured_mode,
                        f"Live provider initialization failed: {e}",
                    )
            else:
                return UnavailableAdapter(
                    source_name,
                    configured_mode,
                    "Live provider implementation is not installed",
                )
        else:
            return UnavailableAdapter(
                source_name,
                configured_mode,
                f"{configured_mode} provider is unavailable: {env_var_name} is not configured",
            )
    
    @staticmethod
    def _log_adapter_status():
        """Log which adapters are enabled/disabled at startup."""
        logger.info("=== ADAPTER STATUS REPORT ===")
        registry = RegistryManager()
        for source, adapter in registry._adapter_registry.items():
            if hasattr(adapter, 'enabled'):
                status = "ENABLED (REAL)" if adapter.enabled else "MOCK (FALLBACK)"
            else:
                status = "ACTIVE"
            logger.info(f"  {source:10s}: {status}")
        logger.info("=" * 30)
    
    def get_adapter(self, source_name: str) -> PortalAdapter:
        """Get adapter for a specific government source."""
        if source_name not in self._adapter_registry:
            raise ValueError(f"No adapter registered for source '{source_name}'")
        return self._adapter_registry[source_name]
    
    def get_adapter_for_field(self, field_name: str) -> PortalAdapter:
        """Get adapter for an extracted field name."""
        source = CLAIM_AUTHORITY_MAP.get(field_name)
        if source is None:
            raise ValueError(f"No authority mapping defined for field '{field_name}'")
        return self.get_adapter(source)


# Global registry instance
_registry = RegistryManager()


def get_adapter(source_name: str) -> PortalAdapter:
    """Get adapter by source name."""
    return _registry.get_adapter(source_name)


def get_adapter_for_field(field_name: str) -> PortalAdapter:
    """Get adapter by extracted field name."""
    return _registry.get_adapter_for_field(field_name)


# Legacy direct registry access for backward compatibility
ADAPTER_REGISTRY: dict[str, PortalAdapter] = _registry._adapter_registry
