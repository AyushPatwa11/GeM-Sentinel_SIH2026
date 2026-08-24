import pytest

from app.adapters.base import VerificationClaim, VerificationStatus
from app.adapters.mock_adapters import (
    BlacklistMockAdapter,
    FlakyMockAdapter,
    GSTNMockAdapter,
    UdyamMockAdapter,
)
from app.adapters.registry import get_adapter, get_adapter_for_field


@pytest.mark.asyncio
async def test_gstn_verified_for_known_clean_bidder():
    adapter = GSTNMockAdapter()
    result = await adapter.verify(
        VerificationClaim(field_name="gstin", claimed_value="22ABCDE1234F1Z5")
    )
    assert result.status == VerificationStatus.VERIFIED
    assert result.data["legal_name"] == "Northline Engineering Pvt Ltd"


@pytest.mark.asyncio
async def test_gstn_inconclusive_for_unknown_gstin():
    adapter = GSTNMockAdapter()
    result = await adapter.verify(
        VerificationClaim(field_name="gstin", claimed_value="00NOPE00000X0Z0")
    )
    assert result.status == VerificationStatus.INCONCLUSIVE


@pytest.mark.asyncio
async def test_udyam_reveals_contradiction_scenario():
    """Meridian claims MICRO but Udyam registry shows MEDIUM — this is the
    exact cross-source contradiction demo scenario."""
    adapter = UdyamMockAdapter()
    result = await adapter.verify(
        VerificationClaim(field_name="udyam_number", claimed_value="UDYAM-CT-02-0099887")
    )
    assert result.status == VerificationStatus.VERIFIED
    assert result.data["category"] == "MEDIUM"  # contradicts bidder's claimed MICRO


@pytest.mark.asyncio
async def test_blacklist_hit_returns_mismatch():
    adapter = BlacklistMockAdapter()
    result = await adapter.verify(
        VerificationClaim(field_name="debarment_status", claimed_value="27DEBAR9999X1Z1")
    )
    assert result.status == VerificationStatus.MISMATCH


@pytest.mark.asyncio
async def test_blacklist_clean_bidder_verified_not_blacklisted():
    adapter = BlacklistMockAdapter()
    result = await adapter.verify(
        VerificationClaim(field_name="debarment_status", claimed_value="22ABCDE1234F1Z5")
    )
    assert result.status == VerificationStatus.VERIFIED


@pytest.mark.asyncio
async def test_flaky_adapter_never_returns_mismatch_on_outage():
    """The single most important adapter guarantee: a downstream technical
    failure must become UNAVAILABLE, never MISMATCH/FAIL — otherwise an API
    outage would silently disqualify a compliant bidder."""
    adapter = FlakyMockAdapter()
    result = await adapter.verify(
        VerificationClaim(field_name="gstin", claimed_value="anything"),
        timeout_seconds=1.0,
        max_retries=1,
    )
    assert result.status == VerificationStatus.UNAVAILABLE
    assert result.status != VerificationStatus.MISMATCH
    assert result.error is not None


def test_registry_maps_every_claim_authority_field():
    for field_name in ("gstin", "cin", "nsic_number", "udyam_number", "debarment_status"):
        adapter = get_adapter_for_field(field_name)
        assert adapter is not None


def test_registry_unknown_field_raises():
    with pytest.raises(ValueError):
        get_adapter_for_field("not_a_real_field")


def test_get_adapter_by_source_name():
    assert get_adapter("GSTN").source_name == "GSTN"
