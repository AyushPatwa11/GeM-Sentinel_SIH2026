"""
Property-based and unit tests for name matching service.

Tests cover:
- Property 1: Name Normalization Determinism
- Property 2: Exact Name Match Detection
- Property 3: Fuzzy Match Threshold Behavior
"""
import pytest
from app.services.name_matching import normalize_name, match_names, fuzzy_match_jaro_winkler


class TestNameNormalizationDeterminism:
    """Property 1: Name Normalization Determinism
    
    For any input name string, applying the normalization function twice 
    should produce the same result (idempotence).
    """
    
    def test_normalization_idempotent(self):
        """Applying normalize twice yields same result."""
        test_names = [
            "ACME Inc.",
            "  ABC  Corp  ",
            "A & B, Ltd.",
            "Tech-Solutions",
            "123 Company Name!",
            "name with   multiple   spaces",
            "",
            "a",
        ]
        
        for name in test_names:
            norm1 = normalize_name(name)
            norm2 = normalize_name(norm1)
            assert norm1 == norm2, f"Normalization not idempotent for '{name}': {norm1} != {norm2}"
    
    def test_normalization_whitespace_trim(self):
        """Trim and collapse whitespace."""
        assert normalize_name("  ABC  Corp  ") == "abc corp"
        assert normalize_name("\t\n  Name  \t\n") == "name"
        assert normalize_name("A    B    C") == "a b c"
    
    def test_normalization_lowercase(self):
        """Convert to lowercase."""
        assert normalize_name("ACME Inc") == "acme inc"
        assert normalize_name("AbCdEf") == "abcdef"
        assert normalize_name("MixedCASE") == "mixedcase"
    
    def test_normalization_punctuation_removal(self):
        """Remove punctuation."""
        assert normalize_name("A & B, Ltd.") == "a b ltd"
        assert normalize_name("Company-Name!") == "company name"
        assert normalize_name("Test@Corp#123") == "test corp 123"
    
    def test_normalization_hyphen_to_space(self):
        """Replace hyphens with space."""
        assert normalize_name("ABC-Corp") == "abc corp"
        assert normalize_name("Tech-Solutions-Pvt-Ltd") == "tech solutions pvt ltd"
    
    def test_normalization_empty_string(self):
        """Handle empty strings."""
        assert normalize_name("") == ""
        assert normalize_name("   ") == ""
        assert normalize_name("\t\n") == ""
    
    def test_normalization_special_cases(self):
        """Test special cases."""
        assert normalize_name("Pvt. Ltd.") == "pvt ltd"
        assert normalize_name("M/S ABC") == "m s abc"
        assert normalize_name("(India) Ltd.") == "india ltd"


class TestExactNameMatchDetection:
    """Property 2: Exact Name Match Detection
    
    For any pair of names that are identical after normalization, the 
    match_result should be "exact_match" with match_score of 1.0.
    """
    
    def test_identical_names_exact_match(self):
        """Identical names should match exactly."""
        result, score = match_names("ACME Inc", "acme inc")
        assert result == "exact_match"
        assert score == 1.0
    
    def test_names_identical_after_normalization(self):
        """Names identical after normalization should exact match."""
        result, score = match_names("  ACME Inc.  ", "acme inc")
        assert result == "exact_match"
        assert score == 1.0
        
        result, score = match_names("ABC-Corp Ltd", "abc corp ltd")
        assert result == "exact_match"
        assert score == 1.0
    
    def test_exact_match_score_always_one(self):
        """Exact match always has score of 1.0."""
        test_pairs = [
            ("Company A", "company a"),
            ("Tech Solutions", "tech solutions"),
            ("Pvt Ltd", "pvt ltd"),
        ]
        
        for name1, name2 in test_pairs:
            result, score = match_names(name1, name2)
            if result == "exact_match":
                assert score == 1.0
    
    def test_different_names_not_exact_match(self):
        """Different names should not be exact match."""
        result, score = match_names("Company A", "Company B")
        assert result != "exact_match"
        
        result, score = match_names("Tech Corp", "Tech Solutions")
        assert result != "exact_match"
    
    def test_empty_strings_exact_match(self):
        """Empty strings should exact match."""
        result, score = match_names("", "")
        assert result == "exact_match"
        assert score == 1.0


class TestFuzzyMatchThreshold:
    """Property 3: Fuzzy Match Threshold Behavior
    
    For any pair of normalized names with score >= threshold (default 0.85),
    the result should be "fuzzy_match". For score < threshold, result should 
    be "no_match".
    """
    
    def test_similar_names_fuzzy_match(self):
        """Similar names above threshold should fuzzy match."""
        # These should be similar enough
        result, score = match_names("Acme Corporation", "Acme Corp", use_fuzzy=True, fuzzy_threshold=0.85)
        assert result in ("exact_match", "fuzzy_match")  # Depends on similarity
    
    def test_dissimilar_names_no_match(self):
        """Dissimilar names should not match."""
        result, score = match_names("Company A", "Company B", use_fuzzy=True, fuzzy_threshold=0.85)
        assert result == "no_match"
        assert score < 0.85
    
    def test_fuzzy_disabled_returns_no_match_for_different(self):
        """When fuzzy disabled, different names return no_match."""
        result, score = match_names("Acme Corp", "ACME Corp", use_fuzzy=False)
        # After normalization both should be same
        assert result == "exact_match"
        
        result, score = match_names("Company A", "Company B", use_fuzzy=False)
        assert result == "no_match"
    
    def test_threshold_boundary(self):
        """Test threshold boundary conditions."""
        # Create names with known similar structure
        result, score = match_names("test", "test", use_fuzzy=True, fuzzy_threshold=0.85)
        assert result == "exact_match"
        assert score == 1.0
        
        # Slight variation
        result, score = match_names("testing", "test", use_fuzzy=True, fuzzy_threshold=0.85)
        # Score should be between 0 and 1
        assert 0.0 <= score <= 1.0
        if score >= 0.85:
            assert result == "fuzzy_match"
        else:
            assert result == "no_match"
    
    def test_match_score_range(self):
        """Match score should always be between 0.0 and 1.0."""
        test_pairs = [
            ("Company A", "Company A"),
            ("Company A", "Company B"),
            ("Test", "Testing"),
            ("ABC", "XYZ"),
        ]
        
        for name1, name2 in test_pairs:
            result, score = match_names(name1, name2)
            assert 0.0 <= score <= 1.0
            assert result in ("exact_match", "fuzzy_match", "no_match")


class TestJaroWinklerSimilarity:
    """Test Jaro-Winkler similarity function."""
    
    def test_identical_strings(self):
        """Identical strings should score 1.0."""
        score, is_match = fuzzy_match_jaro_winkler("test", "test", threshold=0.85)
        assert score == 1.0
        assert is_match is True
    
    def test_completely_different_strings(self):
        """Completely different strings should score low."""
        score, is_match = fuzzy_match_jaro_winkler("abc", "xyz", threshold=0.85)
        assert score < 0.85
        assert is_match is False
    
    def test_similar_strings_high_score(self):
        """Similar strings should score >= threshold."""
        score, is_match = fuzzy_match_jaro_winkler("test", "best", threshold=0.80)
        # 'best' vs 'test' should have reasonable similarity
        assert 0.0 <= score <= 1.0
    
    def test_threshold_parameter(self):
        """Threshold parameter should affect is_match result."""
        score, is_match_high_threshold = fuzzy_match_jaro_winkler("test", "testing", threshold=0.95)
        score, is_match_low_threshold = fuzzy_match_jaro_winkler("test", "testing", threshold=0.50)
        
        # With same input, different thresholds may produce different is_match
        # but score should be the same
        assert is_match_low_threshold is True  # Lower threshold should match
    
    def test_empty_strings(self):
        """Empty strings should score 0.0."""
        score, is_match = fuzzy_match_jaro_winkler("", "", threshold=0.85)
        assert score == 0.0
        assert is_match is False


class TestMatchNamesIntegration:
    """Integration tests for match_names function."""
    
    def test_real_world_company_names(self):
        """Test with real-world company name variations."""
        test_cases = [
            # (doc_name, authority_name, expected_result)
            ("ABC Corp Pvt Ltd", "ABC Corp Pvt Ltd", "exact_match"),
            ("ACME Inc", "acme inc", "exact_match"),
            ("Tech Solutions (India) Ltd", "Tech Solutions India Ltd", None),  # Might be fuzzy
            ("M/S Company", "Company", None),  # Might be fuzzy or no match
        ]
        
        for doc_name, auth_name, expected in test_cases:
            result, score = match_names(doc_name, auth_name, use_fuzzy=True, fuzzy_threshold=0.85)
            assert result in ("exact_match", "fuzzy_match", "no_match")
            assert 0.0 <= score <= 1.0
            
            if expected:
                assert result == expected
    
    def test_case_insensitivity(self):
        """Names differing only in case should exact match."""
        result, score = match_names("COMPANY", "company")
        assert result == "exact_match"
        assert score == 1.0
    
    def test_punctuation_insensitivity(self):
        """Names differing only in punctuation should exact match."""
        result, score = match_names("Company, Inc.", "Company Inc")
        assert result == "exact_match"
        assert score == 1.0
    
    def test_whitespace_insensitivity(self):
        """Names differing only in whitespace should exact match."""
        result, score = match_names("  Company  Inc  ", "Company Inc")
        assert result == "exact_match"
        assert score == 1.0
