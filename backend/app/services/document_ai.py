"""Provider boundary for OCR over uploaded binary documents.

Text supplied through the officer processing endpoint can still use the
deterministic extraction pipeline. Binary OCR must never fabricate text when
an OCR engine is not installed or configured.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class OCRProviderUnavailable(RuntimeError):
    """Raised when no configured binary OCR provider can process a document."""


@dataclass(frozen=True)
class OCRProviderStatus:
    name: str
    configured: bool
    message: str


class BinaryOCRProvider:
    """Select the configured binary OCR implementation."""

    @staticmethod
    def status() -> OCRProviderStatus:
        try:
            import paddleocr  # type: ignore[import-not-found]
        except ImportError:
            return OCRProviderStatus(
                name="PaddleOCR",
                configured=False,
                message="PaddleOCR is not installed; binary OCR requires explicit provider setup.",
            )

        return OCRProviderStatus(
            name="PaddleOCR",
            configured=True,
            message="PaddleOCR is available for binary document processing.",
        )

    @classmethod
    def extract_text(cls, file_path: Path) -> str:
        status = cls.status()
        if not status.configured:
            raise OCRProviderUnavailable(status.message)

        try:
            from paddleocr import PaddleOCR  # type: ignore[import-not-found]

            engine = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
            result = engine.ocr(str(file_path), cls=True)
        except Exception as exc:
            raise OCRProviderUnavailable(
                f"{status.name} failed to process the document: {exc}"
            ) from exc

        lines = []
        for page in result or []:
            for item in page or []:
                if len(item) >= 2 and item[1]:
                    lines.append(str(item[1][0]))
        text = "\n".join(lines).strip()
        if not text:
            raise OCRProviderUnavailable(
                f"{status.name} returned no readable text for the document."
            )
        return text
