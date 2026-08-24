"""
Registry mapping each verifiable field to its ONE designated authoritative
source (claim-level source authority, per locked design — no single portal
is "most trusted for everything").

This module is the entire swap surface: to go from mock to real, only
ADAPTER_REGISTRY changes here. Nothing in the rule engine, risk engine, or
API layer references GSTNMockAdapter directly.
"""
from __future__ import annotations

from app.adapters.base import PortalAdapter
from app.adapters.datagovin_client import DataGovInMCAAdapter
from app.adapters.mock_adapters import (
    BlacklistMockAdapter,
    DigiLockerMockAdapter,
    GSTNMockAdapter,
    NSICMockAdapter,
    UdyamMockAdapter,
)

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
}

# source name -> adapter instance. Swap a value here (e.g. GSTNAdapter())
# to move from mock to real with zero changes anywhere else.
ADAPTER_REGISTRY: dict[str, PortalAdapter] = {
    "GSTN": GSTNMockAdapter(),
    "MCA": DataGovInMCAAdapter(),
    "NSIC": NSICMockAdapter(),
    "UDYAM": UdyamMockAdapter(),
    "DIGILOCKER": DigiLockerMockAdapter(),
    "BLACKLIST": BlacklistMockAdapter(),
}


def get_adapter_for_field(field_name: str) -> PortalAdapter:
    source = CLAIM_AUTHORITY_MAP.get(field_name)
    if source is None:
        raise ValueError(f"No claim-authority mapping defined for field '{field_name}'")
    adapter = ADAPTER_REGISTRY.get(source)
    if adapter is None:
        raise ValueError(f"No adapter registered for source '{source}'")
    return adapter


def get_adapter(source_name: str) -> PortalAdapter:
    adapter = ADAPTER_REGISTRY.get(source_name)
    if adapter is None:
        raise ValueError(f"No adapter registered for source '{source_name}'")
    return adapter
