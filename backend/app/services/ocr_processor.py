"""OCR processor with field extraction and classification for Phase 3."""
import re
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ExtractedField:
    """Represents a single extracted field."""
    field_name: str
    field_value: str
    confidence: float
    evidence_span: str
    source_page: Optional[int] = None


class FieldPattern:
    """Pattern definition for field extraction."""
    
    def __init__(
        self,
        field_name: str,
        patterns: List[str],
        confidence_boost: float = 0.0,
        required: bool = False,
    ):
        self.field_name = field_name
        self.patterns = [re.compile(p, re.IGNORECASE) for p in patterns]
        self.confidence_boost = confidence_boost
        self.required = required


class DocumentClassifier:
    """Classify document type and extract relevant fields."""
    
    # GST Certificate patterns
    GST_PATTERNS = [
        FieldPattern(
            "gst_number",
            [
                r"(?:GSTIN?[:\s]*)?(\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z0-9]{1}[Z]{1}[A-Z0-9]{1})",
                r"GST[:\s]*([0-9A-Z]{15})",
            ],
            confidence_boost=0.15,
            required=True,
        ),
        FieldPattern(
            "legal_name",
            [
                r"(?:Legal\s+Name|Business\s+Name|Organization)[:\s]*([A-Za-z\s&,'-]{5,})",
            ],
            confidence_boost=0.1,
        ),
        FieldPattern(
            "registration_date",
            [
                r"(?:Date\s+of\s+Registration|Registration\s+Date)[:\s]*(\d{2}[-/]\d{2}[-/]\d{4})",
            ],
            confidence_boost=0.1,
        ),
    ]
    
    # PAN patterns
    PAN_PATTERNS = [
        FieldPattern(
            "pan_number",
            [
                r"(?:PAN[:\s]*)?([A-Z]{5}[0-9]{4}[A-Z]{1})",
            ],
            confidence_boost=0.2,
            required=True,
        ),
        FieldPattern(
            "name",
            [
                r"(?:Name\s+of\s+(?:Individual|Assessee))[:\s]*([A-Za-z\s'-]{3,})",
            ],
            confidence_boost=0.1,
        ),
    ]
    
    # Company documents patterns
    COMPANY_PATTERNS = [
        FieldPattern(
            "company_name",
            [
                r"(?:Company|Business)[:\s]*([A-Za-z\s&,'-]{5,})",
            ],
            confidence_boost=0.1,
        ),
        FieldPattern(
            "director_name",
            [
                r"(?:Director|MD)[:\s]*([A-Za-z\s'-]{3,})",
            ],
            confidence_boost=0.08,
        ),
        FieldPattern(
            "registration_number",
            [
                r"(?:CIN|Company Reg\.?)[:\s]*([A-Z0-9]{21})",
            ],
            confidence_boost=0.15,
        ),
    ]
    
    DOC_TYPE_PATTERNS = {
        "GST_CERT": [
            r"(?:GST|Goods?\s+and\s+Services?\s+Tax)",
            r"(?:Registration|Certificate)",
            r"(?:GSTIN|GST Number)",
        ],
        "PAN": [
            r"(?:PAN|Permanent\s+Account\s+Number)",
            r"(?:Income\s+Tax|Department)",
        ],
        "COMPANY_REG": [
            r"(?:Certificate\s+of\s+Incorporation|MCA)",
            r"(?:CIN|Company\s+Registration)",
        ],
        "BANK_STATEMENT": [
            r"(?:Bank|Account\s+Statement)",
            r"(?:Current\s+A/C|Savings\s+A/C)",
        ],
        "BUSINESS_LICENSE": [
            r"(?:Trade\s+License|Business\s+License)",
            r"(?:Municipal|Local\s+Authority)",
        ],
    }
    
    @staticmethod
    def classify_document(text: str) -> Tuple[str, float]:
        """Classify document type from OCR text.
        
        Args:
            text: OCR extracted text
            
        Returns:
            Tuple of (doc_type, confidence)
        """
        if not text:
            return "UNKNOWN", 0.0
        
        text_lower = text.lower()
        scores = {}
        
        for doc_type, patterns in DocumentClassifier.DOC_TYPE_PATTERNS.items():
            matches = sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))
            confidence = min(1.0, matches * 0.3)  # 0.3 per pattern match
            scores[doc_type] = confidence
        
        if not scores or max(scores.values()) == 0:
            return "UNKNOWN", 0.0
        
        best_type = max(scores, key=scores.get)
        return best_type, scores[best_type]
    
    @staticmethod
    def extract_fields(
        text: str,
        doc_type: str,
    ) -> List[ExtractedField]:
        """Extract structured fields from OCR text.
        
        Args:
            text: OCR extracted text
            doc_type: Document type (GST_CERT, PAN, etc.)
            
        Returns:
            List of ExtractedField objects
        """
        fields = []
        
        # Select pattern set based on document type
        if doc_type == "GST_CERT":
            patterns = DocumentClassifier.GST_PATTERNS
        elif doc_type == "PAN":
            patterns = DocumentClassifier.PAN_PATTERNS
        else:
            patterns = DocumentClassifier.COMPANY_PATTERNS
        
        # Extract fields
        for pattern in patterns:
            for compiled_pattern in pattern.patterns:
                matches = compiled_pattern.finditer(text)
                
                for match in matches:
                    try:
                        value = match.group(1) if match.groups() else match.group(0)
                        
                        # Calculate confidence
                        base_confidence = 0.7  # Base for pattern match
                        confidence = min(1.0, base_confidence + pattern.confidence_boost)
                        
                        # Extract context (evidence span)
                        start = max(0, match.start() - 20)
                        end = min(len(text), match.end() + 20)
                        evidence_span = text[start:end].strip()
                        
                        field = ExtractedField(
                            field_name=pattern.field_name,
                            field_value=value.strip(),
                            confidence=confidence,
                            evidence_span=evidence_span,
                        )
                        
                        # Avoid duplicates
                        if not any(
                            f.field_name == field.field_name and f.field_value == field.field_value
                            for f in fields
                        ):
                            fields.append(field)
                    except Exception:
                        pass
        
        return fields


class OCRProcessor:
    """Main OCR processor coordinating extraction and field classification."""
    
    @staticmethod
    async def process_document(
        document_text: str,
        document_id: str,
        doc_type_hint: Optional[str] = None,
        language: str = "eng",
    ) -> Dict[str, Any]:
        """Process document with OCR and field extraction.
        
        Args:
            document_text: Raw OCR text from document
            document_id: ID of document being processed
            doc_type_hint: Optional hint for document type
            language: Language for OCR (default: English)
            
        Returns:
            Dict with classification and extracted fields
        """
        result = {
            "document_id": document_id,
            "status": "PROCESSING",
            "timestamp": datetime.utcnow().isoformat(),
            "text_length": len(document_text),
        }
        
        try:
            # Preprocess text
            text = OCRProcessor._preprocess_text(document_text)
            result["text_preprocessed"] = text
            
            # Classify document
            if doc_type_hint:
                doc_type = doc_type_hint
                confidence = 1.0
            else:
                doc_type, confidence = DocumentClassifier.classify_document(text)
            
            result["document_type"] = doc_type
            result["type_confidence"] = confidence
            
            # Extract fields
            fields = DocumentClassifier.extract_fields(text, doc_type)
            
            result["extracted_fields"] = [
                {
                    "field_name": f.field_name,
                    "field_value": f.field_value,
                    "confidence": f.confidence,
                    "evidence_span": f.evidence_span,
                }
                for f in fields
            ]
            
            # Quality assessment
            result["quality_score"] = OCRProcessor._assess_quality(text, fields)
            result["status"] = "COMPLETED"
            
        except Exception as e:
            result["status"] = "FAILED"
            result["error"] = str(e)
        
        return result
    
    @staticmethod
    def _preprocess_text(text: str) -> str:
        """Clean and normalize OCR text.
        
        Args:
            text: Raw OCR text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove common OCR artifacts
        text = re.sub(r'[|]{2,}', '', text)
        text = re.sub(r'[_]{3,}', '', text)

        # Normalize all whitespace after removing artifacts.
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    @staticmethod
    def _assess_quality(text: str, fields: List[ExtractedField]) -> float:
        """Assess OCR quality and extraction success.
        
        Args:
            text: Preprocessed text
            fields: Extracted fields
            
        Returns:
            Quality score 0-1
        """
        scores = []
        
        # Text length quality (prefer 100-5000 chars)
        text_len = len(text)
        if 100 < text_len < 5000:
            scores.append(1.0)
        elif text_len < 50:
            scores.append(0.2)
        elif text_len > 10000:
            scores.append(0.7)
        else:
            scores.append(0.8)
        
        # Field extraction quality
        if fields:
            avg_confidence = sum(f.confidence for f in fields) / len(fields)
            scores.append(avg_confidence)
        else:
            scores.append(0.2)
        
        # Required field presence
        required_fields = {"gst_number", "pan_number", "legal_name"}
        found_required = any(
            f.field_name in required_fields for f in fields
        )
        if found_required:
            scores.append(0.9)
        else:
            scores.append(0.5)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    @staticmethod
    def batch_process_documents(
        documents: List[Tuple[str, str]],
        batch_size: int = 5,
    ) -> List[Dict[str, Any]]:
        """Process multiple documents in batches.
        
        Args:
            documents: List of (text, doc_id) tuples
            batch_size: Number of concurrent processes
            
        Returns:
            List of processing results
        """
        import concurrent.futures
        
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
            futures = []
            
            for text, doc_id in documents:
                future = executor.submit(
                    OCRProcessor._process_sync,
                    text,
                    doc_id,
                )
                futures.append(future)
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({
                        "status": "FAILED",
                        "error": str(e),
                    })
        
        return results
    
    @staticmethod
    def _process_sync(text: str, doc_id: str) -> Dict[str, Any]:
        """Synchronous wrapper for async processor."""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(
                OCRProcessor.process_document(text, doc_id)
            )
        finally:
            loop.close()
