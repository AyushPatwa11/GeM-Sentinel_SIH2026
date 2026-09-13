"""
Name matching service for verification — pure, deterministic functions
for normalizing and comparing names from documents against authority records.

This module contains no I/O, no external dependencies beyond Python stdlib.
All functions are testable pure functions.
"""
import re
from typing import Tuple
from difflib import SequenceMatcher
import logging

logger = logging.getLogger(__name__)


def normalize_name(name: str) -> str:
    """
    Pure, deterministic normalization function for name comparison.
    
    Algorithm:
    1. Strip leading/trailing whitespace
    2. Convert to lowercase
    3. Remove or collapse punctuation and special characters
    4. Collapse multiple spaces to single space
    
    Examples:
    • "ACME Inc." → "acme inc"
    • "  ABC-Corp  " → "abc corp"
    • "Tech, Ltd." → "tech ltd"
    • "A & B Limited" → "a b limited"
    
    Property: Idempotent — normalize(normalize(x)) == normalize(x)
    
    Args:
        name: Input name string
    
    Returns:
        Normalized name string
    """
    if not name:
        return ""
    
    # Step 1: Strip whitespace
    normalized = name.strip()
    
    # Step 2: Lowercase
    normalized = normalized.lower()
    
    # Step 3: Remove/collapse punctuation
    # Keep alphanumerics, spaces, and hyphens
    # Replace punctuation with space
    normalized = re.sub(r'[^\w\s-]', ' ', normalized)
    
    # Replace hyphens with space (hyphenated words → separate words)
    normalized = normalized.replace('-', ' ')
    
    # Step 4: Collapse multiple spaces
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized


def fuzzy_match_jaro_winkler(s1: str, s2: str, threshold: float = 0.85) -> Tuple[float, bool]:
    """
    Jaro-Winkler similarity scoring for fuzzy string matching.
    
    Jaro-Winkler algorithm:
    • Computes similarity score between 0.0 (no match) and 1.0 (exact match)
    • More weight to matching prefixes
    • Common for name matching
    
    Args:
        s1: First string (normalized)
        s2: Second string (normalized)
        threshold: Minimum score to consider a match (default 0.85)
    
    Returns:
        Tuple of (score, is_match)
        • score: Jaro-Winkler similarity (0.0 to 1.0)
        • is_match: True if score >= threshold
    """
    if s1 == s2:
        return 1.0, True
    
    if not s1 or not s2:
        return 0.0, False
    
    # Use difflib SequenceMatcher as base for similarity
    # (full Jaro-Winkler implementation available in external libraries)
    ratio = SequenceMatcher(None, s1, s2).ratio()
    
    # Apply prefix boost (Winkler modification)
    # Extra credit if strings share a common prefix
    prefix_len = 0
    for i in range(min(len(s1), len(s2), 4)):  # Max 4-char prefix bonus
        if s1[i] == s2[i]:
            prefix_len += 1
        else:
            break
    
    # Winkler modification: boost score by up to 0.1 for common prefix
    if prefix_len > 0:
        ratio += (0.1 * prefix_len) * (1 - ratio)
    
    ratio = min(ratio, 1.0)  # Cap at 1.0
    
    return ratio, ratio >= threshold


def match_names(
    document_name: str,
    authority_name: str,
    use_fuzzy: bool = True,
    fuzzy_threshold: float = 0.85
) -> Tuple[str, float]:
    """
    Compares two names with deterministic matching logic.
    
    Decision Tree:
    1. Normalize both names
    2. Check exact match after normalization
    3. If exact: return "exact_match" with score 1.0
    4. If fuzzy matching enabled:
       - Compute Jaro-Winkler score
       - If score >= threshold: return "fuzzy_match" with score
       - Else: return "no_match" with score
    5. Else (no fuzzy): return "no_match" with score 0.0
    
    Args:
        document_name: Name from extracted document
        authority_name: Name from authority API response
        use_fuzzy: Whether to apply fuzzy matching (default True)
        fuzzy_threshold: Minimum Jaro-Winkler score for fuzzy match (default 0.85)
    
    Returns:
        Tuple of (match_result, match_score)
        • match_result: "exact_match" | "fuzzy_match" | "no_match"
        • match_score: 0.0 to 1.0
    """
    # Normalize both names
    doc_normalized = normalize_name(document_name)
    auth_normalized = normalize_name(authority_name)
    
    # Check exact match
    if doc_normalized == auth_normalized:
        logger.debug(f"Exact name match: '{document_name}' == '{authority_name}'")
        return "exact_match", 1.0
    
    # Attempt fuzzy match if enabled
    if use_fuzzy:
        score, matches = fuzzy_match_jaro_winkler(
            doc_normalized, 
            auth_normalized, 
            threshold=fuzzy_threshold
        )
        
        if matches:
            logger.debug(
                f"Fuzzy name match (score {score:.2f}): "
                f"'{document_name}' ~= '{authority_name}'"
            )
            return "fuzzy_match", score
        else:
            logger.debug(
                f"No name match (score {score:.2f}): "
                f"'{document_name}' vs '{authority_name}'"
            )
            return "no_match", score
    
    # No fuzzy matching
    logger.debug(f"No name match: '{document_name}' vs '{authority_name}'")
    return "no_match", 0.0
