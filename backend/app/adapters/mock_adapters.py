"""
Mock adapters. Each satisfies the exact same PortalAdapter contract that a
real GSTNAdapter/MCAAdapter/DigiLockerAdapter/NSICAdapter would — swapping
mock for real later is a config change (see registry.py), not an
architecture change.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.adapters.base import (
    AdapterError,
    PortalAdapter,
    VerificationClaim,
    VerificationResult,
    VerificationStatus,
)
from app.adapters.seed_data import (
    BLACKLIST_RECORDS,
    GSTN_RECORDS,
    MCA_RECORDS,
    NSIC_RECORDS,
    UDYAM_RECORDS,
)


def _now():
    return datetime.now(timezone.utc)


class GSTNMockAdapter(PortalAdapter):
    source_name = "GSTN"

    async def _verify_raw(self, claim: VerificationClaim) -> VerificationResult:
        record = GSTN_RECORDS.get(claim.claimed_value)
        if record is None:
            return VerificationResult(
                source=self.source_name,
                status=VerificationStatus.INCONCLUSIVE,
                checked_at=_now(),
                freshness_seconds=0,
                error="GSTIN not found in registry",
            )
        return VerificationResult(
            source=self.source_name,
            status=VerificationStatus.VERIFIED,
            checked_at=_now(),
            freshness_seconds=0,
            data=record,
            evidence=f"GSTN registry record for {claim.claimed_value}",
        )


class MCAMockAdapter(PortalAdapter):
    source_name = "MCA"

    async def _verify_raw(self, claim: VerificationClaim) -> VerificationResult:
        record = MCA_RECORDS.get(claim.claimed_value)
        if record is None:
            return VerificationResult(
                source=self.source_name,
                status=VerificationStatus.INCONCLUSIVE,
                checked_at=_now(),
                freshness_seconds=0,
                error="CIN not found in MCA21 registry",
            )
        return VerificationResult(
            source=self.source_name,
            status=VerificationStatus.VERIFIED,
            checked_at=_now(),
            freshness_seconds=0,
            data=record,
            evidence=f"MCA21 record for {claim.claimed_value}",
        )


class NSICMockAdapter(PortalAdapter):
    source_name = "NSIC"

    async def _verify_raw(self, claim: VerificationClaim) -> VerificationResult:
        record = NSIC_RECORDS.get(claim.claimed_value)
        if record is None:
            return VerificationResult(
                source=self.source_name,
                status=VerificationStatus.NOT_REQUIRED,
                checked_at=_now(),
                freshness_seconds=0,
                error="No NSIC registration found — not required unless claimed",
            )
        return VerificationResult(
            source=self.source_name,
            status=VerificationStatus.VERIFIED,
            checked_at=_now(),
            freshness_seconds=0,
            data=record,
            evidence=f"NSIC record for {claim.claimed_value}",
        )


class UdyamMockAdapter(PortalAdapter):
    """Udyam isn't in the PS's confirmed-access list but is central to the
    MSME/EMD-exemption scenario, so it ships as a named mock like the rest."""

    source_name = "UDYAM"

    async def _verify_raw(self, claim: VerificationClaim) -> VerificationResult:
        record = UDYAM_RECORDS.get(claim.claimed_value)
        if record is None:
            return VerificationResult(
                source=self.source_name,
                status=VerificationStatus.INCONCLUSIVE,
                checked_at=_now(),
                freshness_seconds=0,
                error="Udyam number not found",
            )
        return VerificationResult(
            source=self.source_name,
            status=VerificationStatus.VERIFIED,
            checked_at=_now(),
            freshness_seconds=0,
            data=record,
            evidence=f"Udyam record for {claim.claimed_value}",
        )


class DigiLockerMockAdapter(PortalAdapter):
    """Document-authenticity flow is mocked as a pass-through existence
    check only — actual signature/authenticity verification is explicitly
    out of MVP scope (see plan Section 13)."""

    source_name = "DIGILOCKER"

    async def _verify_raw(self, claim: VerificationClaim) -> VerificationResult:
        return VerificationResult(
            source=self.source_name,
            status=VerificationStatus.NOT_REQUIRED,
            checked_at=_now(),
            freshness_seconds=0,
            evidence="DigiLocker existence-check mock — signature verification out of scope for MVP",
        )


class BlacklistMockAdapter(PortalAdapter):
    source_name = "BLACKLIST"

    async def _verify_raw(self, claim: VerificationClaim) -> VerificationResult:
        record = BLACKLIST_RECORDS.get(claim.claimed_value)
        if record is not None:
            return VerificationResult(
                source=self.source_name,
                status=VerificationStatus.MISMATCH,  # presence on blacklist = a genuine compliance fact
                checked_at=_now(),
                freshness_seconds=0,
                data=record,
                evidence=f"Debarment record found for {claim.claimed_value}",
            )
        return VerificationResult(
            source=self.source_name,
            status=VerificationStatus.VERIFIED,  # verified NOT blacklisted
            checked_at=_now(),
            freshness_seconds=0,
            evidence="No debarment record found",
        )


class FlakyMockAdapter(PortalAdapter):
    """Deliberately simulates a portal that is down — used to demo that
    API unavailability never becomes an automatic bidder failure."""

    source_name = "FLAKY_DEMO_SOURCE"

    async def _verify_raw(self, claim: VerificationClaim) -> VerificationResult:
        raise AdapterError("simulated portal outage for demo purposes")
