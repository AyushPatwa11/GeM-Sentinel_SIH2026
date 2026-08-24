"""
PortalAdapter interface — every government-portal integration (real or mock)
must satisfy this exact contract. This is what lets the platform swap a
MockAdapter for a real GSTNAdapter later with zero changes to the rule
engine, risk engine, or API layer — only this file's contract matters.
"""
from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional


class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    MISMATCH = "MISMATCH"
    UNAVAILABLE = "UNAVAILABLE"
    INCONCLUSIVE = "INCONCLUSIVE"
    PENDING = "PENDING"
    NOT_REQUIRED = "NOT_REQUIRED"


@dataclass
class VerificationClaim:
    """What the bidder claims, extracted from their documents."""

    field_name: str  # e.g. "gstin", "cin", "udyam_number"
    claimed_value: str
    organization_id: Optional[str] = None
    extracted_fact_id: Optional[str] = None


@dataclass
class VerificationResult:
    source: str
    status: VerificationStatus
    checked_at: datetime
    freshness_seconds: int
    data: Optional[Dict[str, Any]] = None
    evidence: Optional[str] = None
    error: Optional[str] = None


class AdapterError(Exception):
    """Raised by an adapter implementation on a technical failure
    (timeout, malformed response, connection error). Callers must map
    this to VerificationStatus.UNAVAILABLE, never to MISMATCH/FAILED —
    a technical failure is not evidence the bidder is non-compliant."""


class PortalAdapter(ABC):
    source_name: str

    @abstractmethod
    async def _verify_raw(self, claim: VerificationClaim) -> VerificationResult:
        """Implementations override this. Must raise AdapterError on any
        technical failure rather than returning a fabricated result."""
        raise NotImplementedError

    async def verify(
        self, claim: VerificationClaim, timeout_seconds: float = 5.0, max_retries: int = 2
    ) -> VerificationResult:
        """Public entry point — wraps _verify_raw with timeout + retry-with-backoff.
        Any unresolved technical failure becomes UNAVAILABLE, never MISMATCH."""
        last_error: Optional[str] = None
        for attempt in range(max_retries + 1):
            try:
                return await asyncio.wait_for(
                    self._verify_raw(claim), timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                last_error = f"timeout after {timeout_seconds}s (attempt {attempt + 1})"
            except AdapterError as e:
                last_error = str(e)

            if attempt < max_retries:
                await asyncio.sleep(0.5 * (2 ** attempt))  # exponential backoff

        return VerificationResult(
            source=self.source_name,
            status=VerificationStatus.UNAVAILABLE,
            checked_at=datetime.now(timezone.utc),
            freshness_seconds=0,
            error=last_error,
        )
