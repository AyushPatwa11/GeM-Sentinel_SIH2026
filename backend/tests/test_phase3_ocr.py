"""Tests for Phase 3: OCR and field extraction."""
import pytest
import asyncio
from app.services.ocr_processor import (
    OCRProcessor, DocumentClassifier, FieldPattern
)


class TestPhase3OCRClassification:
    """Phase 3: Document classification."""
    
    def test_classify_gst_document(self):
        """Test classifying GST certificate."""
        text = """
        GSTIN: 27AAFCU5055K1Z5
        Legal Name: Test Company Pvt Ltd
        Date of Registration: 15-07-2020
        State: Maharashtra
        """
        
        doc_type, confidence = DocumentClassifier.classify_document(text)
        
        assert doc_type == "GST_CERT"
        assert confidence > 0.5
    
    def test_classify_pan_document(self):
        """Test classifying PAN certificate."""
        text = """
        PAN: AAAPA5055K
        Name of Individual: John Doe
        Date of Issue: 20-01-2018
        Income Tax Department
        """
        
        doc_type, confidence = DocumentClassifier.classify_document(text)
        
        assert doc_type == "PAN"
        assert confidence > 0.5
    
    def test_classify_company_registration(self):
        """Test classifying company registration."""
        text = """
        Certificate of Incorporation
        CIN: U72900MH2015PTC265160
        Company: Test Ltd
        MCA Registration
        """
        
        doc_type, confidence = DocumentClassifier.classify_document(text)
        
        assert doc_type == "COMPANY_REG"
        assert confidence > 0.3


class TestPhase3FieldExtraction:
    """Phase 3: Field extraction from documents."""
    
    def test_extract_gst_number(self):
        """Test extracting GST number."""
        text = "GSTIN: 27AAFCU5055K1Z5 is the tax identification"
        
        fields = DocumentClassifier.extract_fields(text, "GST_CERT")
        
        gst_fields = [f for f in fields if f.field_name == "gst_number"]
        assert len(gst_fields) > 0
        assert "27AAFCU5055K1Z5" in gst_fields[0].field_value
        assert gst_fields[0].confidence > 0.7
    
    def test_extract_pan_number(self):
        """Test extracting PAN number."""
        text = "Your PAN is AAAPA5055K for income tax purposes"
        
        fields = DocumentClassifier.extract_fields(text, "PAN")
        
        pan_fields = [f for f in fields if f.field_name == "pan_number"]
        assert len(pan_fields) > 0
        assert "AAAPA5055K" in pan_fields[0].field_value
    
    def test_extract_multiple_fields(self):
        """Test extracting multiple fields from GST document."""
        text = """
        Goods and Services Tax Registration
        GSTIN: 27AAFCU5055K1Z5
        Legal Name: Test Company Pvt Ltd
        Date of Registration: 15-07-2020
        """
        
        fields = DocumentClassifier.extract_fields(text, "GST_CERT")
        
        field_names = [f.field_name for f in fields]
        assert "gst_number" in field_names
        assert len(fields) >= 2  # At least GST and company name or date
    
    def test_field_confidence_scoring(self):
        """Test that field confidence scores are reasonable."""
        text = "GSTIN: 27AAFCU5055K1Z5"
        
        fields = DocumentClassifier.extract_fields(text, "GST_CERT")
        
        for field in fields:
            assert 0 <= field.confidence <= 1.0
            assert field.confidence > 0.5  # Reasonable confidence
    
    def test_evidence_span_extraction(self):
        """Test that evidence span is captured."""
        text = "The document shows GSTIN: 27AAFCU5055K1Z5 clearly"
        
        fields = DocumentClassifier.extract_fields(text, "GST_CERT")
        
        gst_fields = [f for f in fields if f.field_name == "gst_number"]
        assert len(gst_fields) > 0
        assert len(gst_fields[0].evidence_span) > 0


class TestPhase3OCRProcessor:
    """Phase 3: Main OCR processor."""
    
    @pytest.mark.asyncio
    async def test_process_document_complete(self):
        """Test complete document processing pipeline."""
        text = """
        GST Certificate
        GSTIN: 27AAFCU5055K1Z5
        Legal Name: Test Company Pvt Ltd
        Registration Date: 15-07-2020
        """
        
        result = await OCRProcessor.process_document(
            text,
            "doc_123",
            doc_type_hint="GST_CERT",
        )
        
        assert result["status"] == "COMPLETED"
        assert result["document_type"] == "GST_CERT"
        assert result["quality_score"] > 0.5
        assert len(result["extracted_fields"]) > 0
    
    @pytest.mark.asyncio
    async def test_process_document_with_classification(self):
        """Test processing with automatic document classification."""
        text = """
        Goods and Services Tax Registration Certificate
        GSTIN: 27AAFCU5055K1Z5
        """
        
        result = await OCRProcessor.process_document(
            text,
            "doc_456",
        )
        
        assert result["status"] == "COMPLETED"
        assert result["document_type"] in ["GST_CERT", "UNKNOWN"]
        assert "extracted_fields" in result
    
    def test_text_preprocessing(self):
        """Test text cleaning and normalization."""
        dirty_text = """
        Line1   with    extra    spaces
        
        
        Line2 with |||| artifacts ____
        """
        
        clean = OCRProcessor._preprocess_text(dirty_text)
        
        assert "  " not in clean  # No double spaces
        assert "||||" not in clean
        assert "____" not in clean
    
    def test_quality_assessment(self):
        """Test OCR quality scoring."""
        from app.services.ocr_processor import ExtractedField
        
        # Good text with fields
        good_text = "A" * 1000
        good_fields = [
            ExtractedField("test", "value", 0.9, "evidence"),
        ]
        quality = OCRProcessor._assess_quality(good_text, good_fields)
        assert quality > 0.6
        
        # Poor text with no fields
        poor_text = "short"
        poor_fields = []
        quality = OCRProcessor._assess_quality(poor_text, poor_fields)
        assert quality < 0.5
    
    def test_batch_processing(self):
        """Test batch processing multiple documents."""
        documents = [
            ("GSTIN: 27AAFCU5055K1Z5", "doc_1"),
            ("PAN: AAAPA5055K", "doc_2"),
            ("CIN: U72900MH2015PTC265160", "doc_3"),
        ]
        
        results = OCRProcessor.batch_process_documents(documents, batch_size=3)
        
        assert len(results) == 3
        for result in results:
            assert "status" in result
            assert result["status"] in ["COMPLETED", "FAILED"]


class TestPhase3FieldPatterns:
    """Phase 3: Field extraction patterns."""
    
    def test_gst_pattern_variations(self):
        """Test GST number extraction with format variations."""
        variations = [
            "GSTIN: 27AAFCU5055K1Z5",
            "GSTIN 27AAFCU5055K1Z5",
            "GST Number: 27AAFCU5055K1Z5",
            "27AAFCU5055K1Z5",
        ]
        
        for text in variations:
            fields = DocumentClassifier.extract_fields(text, "GST_CERT")
            gst_fields = [f for f in fields if f.field_name == "gst_number"]
            assert len(gst_fields) > 0, f"Failed to extract from: {text}"
    
    def test_pan_pattern_variations(self):
        """Test PAN number extraction with format variations."""
        variations = [
            "PAN: AAAPA5055K",
            "PAN AAAPA5055K",
            "Permanent Account Number: AAAPA5055K",
            "AAAPA5055K",
        ]
        
        for text in variations:
            fields = DocumentClassifier.extract_fields(text, "PAN")
            pan_fields = [f for f in fields if f.field_name == "pan_number"]
            assert len(pan_fields) > 0, f"Failed to extract from: {text}"
    
    def test_date_extraction(self):
        """Test date field extraction."""
        text = "Date of Registration: 15-07-2020 is official"
        
        fields = DocumentClassifier.extract_fields(text, "GST_CERT")
        
        date_fields = [f for f in fields if f.field_name == "registration_date"]
        assert len(date_fields) > 0
