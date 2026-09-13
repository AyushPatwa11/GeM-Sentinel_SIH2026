"""Compliance Rule Engine for Phase 4 - Rule definitions and evaluation."""
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass
from enum import Enum
import json


class RuleType(Enum):
    """Types of compliance rules."""
    DOCUMENT_REQUIRED = "document_required"
    ENTITY_VERIFICATION = "entity_verification"
    DATA_CONSISTENCY = "data_consistency"
    BUSINESS_LOGIC = "business_logic"
    EXTERNAL_VERIFICATION = "external_verification"


@dataclass
class ComplianceRule:
    """Represents a single compliance rule."""
    id: str
    name: str
    description: str
    rule_type: RuleType
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    version: str
    applicable_contexts: List[str]  # bidder, officer, tender_type, etc.
    required_evidence: List[str]  # fact types, document types, verification types
    
    # Rule evaluation logic
    evaluator_func: Optional[Callable] = None
    
    # Risk signal configuration
    risk_signal_weight: float = 1.0
    risk_signal_on_fail: bool = True


class ComplianceRuleEngine:
    """Evaluates bids against compliance rules."""
    
    def __init__(self):
        """Initialize rule engine with default rules."""
        self.rules: Dict[str, ComplianceRule] = {}
        self._register_default_rules()
    
    def _register_default_rules(self):
        """Register built-in compliance rules for Phase 4."""
        
        # Rule 1: Mandatory documents check
        self.register_rule(ComplianceRule(
            id="DOC_001",
            name="Mandatory Documents",
            description="Verify all mandatory documents are uploaded and valid",
            rule_type=RuleType.DOCUMENT_REQUIRED,
            severity="CRITICAL",
            version="1.0.0",
            applicable_contexts=["bidder", "tender_evaluation"],
            required_evidence=["document_gstin", "document_pan", "document_mca"],
            risk_signal_weight=5.0,
            risk_signal_on_fail=True,
        ))
        
        # Rule 2: GST registration validity
        self.register_rule(ComplianceRule(
            id="VER_001",
            name="GST Registration Valid",
            description="Verify GST certificate is valid and registered",
            rule_type=RuleType.EXTERNAL_VERIFICATION,
            severity="CRITICAL",
            version="1.0.0",
            applicable_contexts=["bidder", "officer_review"],
            required_evidence=["verification_gstin", "extracted_fact_gstin"],
            risk_signal_weight=4.5,
            risk_signal_on_fail=True,
        ))
        
        # Rule 3: PAN verification
        self.register_rule(ComplianceRule(
            id="VER_002",
            name="PAN Verification",
            description="Verify PAN number is valid and entity matches",
            rule_type=RuleType.EXTERNAL_VERIFICATION,
            severity="CRITICAL",
            version="1.0.0",
            applicable_contexts=["bidder", "officer_review"],
            required_evidence=["verification_pan", "extracted_fact_pan"],
            risk_signal_weight=4.5,
            risk_signal_on_fail=True,
        ))
        
        # Rule 4: Company name consistency
        self.register_rule(ComplianceRule(
            id="CON_001",
            name="Company Name Consistency",
            description="Verify company name is consistent across all documents",
            rule_type=RuleType.DATA_CONSISTENCY,
            severity="HIGH",
            version="1.0.0",
            applicable_contexts=["bidder", "compliance_check"],
            required_evidence=["extracted_fact_company_name", "document_pan", "document_gstin"],
            risk_signal_weight=3.0,
            risk_signal_on_fail=True,
        ))
        
        # Rule 5: Address verification
        self.register_rule(ComplianceRule(
            id="VER_003",
            name="Address Verification",
            description="Verify registered address matches across documents",
            rule_type=RuleType.DATA_CONSISTENCY,
            severity="MEDIUM",
            version="1.0.0",
            applicable_contexts=["bidder", "officer_review"],
            required_evidence=["extracted_fact_address", "document_pan", "document_gstin"],
            risk_signal_weight=2.5,
            risk_signal_on_fail=True,
        ))
        
        # Rule 6: Previous bid history
        self.register_rule(ComplianceRule(
            id="BIZ_001",
            name="Bid History Check",
            description="Check for previous violations or compliance issues",
            rule_type=RuleType.BUSINESS_LOGIC,
            severity="HIGH",
            version="1.0.0",
            applicable_contexts=["officer_review", "compliance_check"],
            required_evidence=["audit_trail"],
            risk_signal_weight=3.5,
            risk_signal_on_fail=True,
        ))
        
        # Rule 7: MSE/MSME status verification
        self.register_rule(ComplianceRule(
            id="VER_004",
            name="MSE/MSME Status",
            description="Verify MSE/MSME registration if claimed",
            rule_type=RuleType.EXTERNAL_VERIFICATION,
            severity="MEDIUM",
            version="1.0.0",
            applicable_contexts=["bidder", "officer_review"],
            required_evidence=["verification_udyam", "extracted_fact_msme"],
            risk_signal_weight=2.0,
            risk_signal_on_fail=False,  # Not critical if not claimed
        ))
        
        # Rule 8: NSIC registration (if applicable)
        self.register_rule(ComplianceRule(
            id="VER_005",
            name="NSIC Registration",
            description="Verify NSIC registration if applicable",
            rule_type=RuleType.EXTERNAL_VERIFICATION,
            severity="LOW",
            version="1.0.0",
            applicable_contexts=["bidder", "officer_review"],
            required_evidence=["verification_nsic", "extracted_fact_nsic"],
            risk_signal_weight=1.0,
            risk_signal_on_fail=False,
        ))
        
        # Rule 9: OCR quality check
        self.register_rule(ComplianceRule(
            id="DOC_002",
            name="Document Quality",
            description="Verify OCR extracted data quality and completeness",
            rule_type=RuleType.DOCUMENT_REQUIRED,
            severity="MEDIUM",
            version="1.0.0",
            applicable_contexts=["compliance_check"],
            required_evidence=["ocr_extraction", "extracted_facts"],
            risk_signal_weight=2.5,
            risk_signal_on_fail=True,
        ))
        
        # Rule 10: Business rules compliance
        self.register_rule(ComplianceRule(
            id="BIZ_002",
            name="Tender Eligibility",
            description="Verify bidder meets tender-specific eligibility criteria",
            rule_type=RuleType.BUSINESS_LOGIC,
            severity="HIGH",
            version="1.0.0",
            applicable_contexts=["tender_evaluation", "bidder"],
            required_evidence=["bid_metadata", "organization_profile"],
            risk_signal_weight=4.0,
            risk_signal_on_fail=True,
        ))
    
    def register_rule(self, rule: ComplianceRule):
        """Register a compliance rule.
        
        Args:
            rule: ComplianceRule instance
        """
        self.rules[rule.id] = rule
    
    def get_rule(self, rule_id: str) -> Optional[ComplianceRule]:
        """Get a rule by ID."""
        return self.rules.get(rule_id)
    
    def list_rules(self, context: Optional[str] = None) -> List[ComplianceRule]:
        """List all rules, optionally filtered by context.
        
        Args:
            context: Optional context filter (bidder, officer, etc.)
            
        Returns:
            List of applicable rules
        """
        if not context:
            return list(self.rules.values())
        
        return [
            rule for rule in self.rules.values()
            if context in rule.applicable_contexts
        ]
    
    def evaluate_rule(
        self,
        rule_id: str,
        bid_data: Dict[str, Any],
        evidence_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Evaluate a single rule against bid data.
        
        Args:
            rule_id: Rule ID to evaluate
            bid_data: Bid information (org, documents, extracted facts, etc.)
            evidence_data: Evidence from verification, extraction, etc.
            
        Returns:
            Evaluation result:
            {
                "rule_id": str,
                "passed": bool,
                "explanation": str,
                "reasoning_chain": List[str],
                "evidence_references": List[str],
                "risk_signal_triggered": bool,
                "severity": str,
            }
        """
        rule = self.get_rule(rule_id)
        if not rule:
            return {
                "rule_id": rule_id,
                "passed": False,
                "explanation": f"Rule {rule_id} not found",
                "reasoning_chain": [],
                "evidence_references": [],
                "risk_signal_triggered": False,
                "severity": "UNKNOWN",
            }
        
        # Evaluate based on rule type
        result = self._evaluate_by_type(rule, bid_data, evidence_data)
        result["rule_id"] = rule_id
        result["severity"] = rule.severity
        result["risk_signal_triggered"] = (not result["passed"]) and rule.risk_signal_on_fail
        
        return result
    
    def _evaluate_by_type(
        self,
        rule: ComplianceRule,
        bid_data: Dict[str, Any],
        evidence_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Evaluate rule based on its type."""
        
        if rule.rule_type == RuleType.DOCUMENT_REQUIRED:
            return self._evaluate_document_rule(rule, bid_data, evidence_data)
        elif rule.rule_type == RuleType.ENTITY_VERIFICATION:
            return self._evaluate_entity_verification(rule, bid_data, evidence_data)
        elif rule.rule_type == RuleType.DATA_CONSISTENCY:
            return self._evaluate_consistency(rule, bid_data, evidence_data)
        elif rule.rule_type == RuleType.BUSINESS_LOGIC:
            return self._evaluate_business_logic(rule, bid_data, evidence_data)
        elif rule.rule_type == RuleType.EXTERNAL_VERIFICATION:
            return self._evaluate_external_verification(rule, bid_data, evidence_data)
        else:
            return {
                "passed": False,
                "explanation": "Unknown rule type",
                "reasoning_chain": [],
                "evidence_references": [],
            }
    
    def _evaluate_document_rule(
        self,
        rule: ComplianceRule,
        bid_data: Dict[str, Any],
        evidence_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Evaluate document requirement rules."""
        documents = bid_data.get("documents", [])
        doc_types = {doc.get("type") for doc in documents}
        
        # Check if all required document types are present
        missing_docs = set(rule.required_evidence) - doc_types
        
        reasoning = [
            f"Checking for {len(rule.required_evidence)} required document types",
            f"Found {len(doc_types)} documents: {doc_types}",
        ]
        
        if missing_docs:
            reasoning.append(f"Missing documents: {missing_docs}")
            return {
                "passed": False,
                "explanation": f"Missing required documents: {', '.join(missing_docs)}",
                "reasoning_chain": reasoning,
                "evidence_references": [d.get("id") for d in documents],
            }
        
        reasoning.append("All required documents present")
        return {
            "passed": True,
            "explanation": "All mandatory documents uploaded and available",
            "reasoning_chain": reasoning,
            "evidence_references": [d.get("id") for d in documents],
        }
    
    def _evaluate_entity_verification(
        self,
        rule: ComplianceRule,
        bid_data: Dict[str, Any],
        evidence_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Evaluate entity verification rules."""
        # Placeholder for entity verification logic
        reasoning = ["Entity verification pending"]
        return {
            "passed": True,
            "explanation": "Entity verified (placeholder)",
            "reasoning_chain": reasoning,
            "evidence_references": evidence_data.get("references", []),
        }
    
    def _evaluate_consistency(
        self,
        rule: ComplianceRule,
        bid_data: Dict[str, Any],
        evidence_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Evaluate data consistency rules."""
        extracted = evidence_data.get("extracted_facts", {})
        
        # Check name consistency across documents
        names = {
            "pan": extracted.get("pan_company_name"),
            "gstin": extracted.get("gstin_company_name"),
            "bid": bid_data.get("organization_name"),
        }
        
        non_null_names = {k: v for k, v in names.items() if v}
        
        reasoning = [
            f"Checking consistency of company name across {len(non_null_names)} sources"
        ]
        
        if len(set(non_null_names.values())) > 1:
            reasoning.append(f"Name mismatch detected: {names}")
            return {
                "passed": False,
                "explanation": "Company name inconsistent across documents",
                "reasoning_chain": reasoning,
                "evidence_references": list(non_null_names.keys()),
            }
        
        reasoning.append("All names are consistent")
        return {
            "passed": True,
            "explanation": "Company name consistent across all documents",
            "reasoning_chain": reasoning,
            "evidence_references": list(non_null_names.keys()),
        }
    
    def _evaluate_business_logic(
        self,
        rule: ComplianceRule,
        bid_data: Dict[str, Any],
        evidence_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Evaluate business logic rules."""
        # Placeholder for business logic evaluation
        reasoning = ["Business logic evaluation pending"]
        return {
            "passed": True,
            "explanation": "Business logic check passed (placeholder)",
            "reasoning_chain": reasoning,
            "evidence_references": evidence_data.get("references", []),
        }
    
    def _evaluate_external_verification(
        self,
        rule: ComplianceRule,
        bid_data: Dict[str, Any],
        evidence_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Evaluate external verification rules (GSTIN, PAN, etc.)."""
        verification_status = evidence_data.get("verification_status", "PENDING")
        
        reasoning = [
            f"Checking external verification status for {rule.name}",
            f"Status: {verification_status}"
        ]
        
        if verification_status in ["VERIFIED", "VERIFIED_WITH_MINOR_ISSUES"]:
            reasoning.append("Verification passed from government source")
            return {
                "passed": True,
                "explanation": f"External verification successful: {verification_status}",
                "reasoning_chain": reasoning,
                "evidence_references": evidence_data.get("references", []),
            }
        elif verification_status in ["PENDING", "IN_PROGRESS"]:
            reasoning.append("Verification still in progress")
            return {
                "passed": False,
                "explanation": f"External verification pending: {verification_status}",
                "reasoning_chain": reasoning,
                "evidence_references": evidence_data.get("references", []),
            }
        else:
            reasoning.append(f"Verification failed: {verification_status}")
            return {
                "passed": False,
                "explanation": f"External verification failed: {verification_status}",
                "reasoning_chain": reasoning,
                "evidence_references": evidence_data.get("references", []),
            }
    
    def evaluate_bid_compliance(
        self,
        bid_data: Dict[str, Any],
        evidence_data: Dict[str, Any],
        rule_ids: Optional[List[str]] = None,
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Evaluate bid against multiple rules.
        
        Args:
            bid_data: Bid information
            evidence_data: Evidence from all sources
            rule_ids: Specific rules to evaluate (if None, use all applicable)
            context: Evaluation context (bidder, officer, etc.)
            
        Returns:
            Comprehensive evaluation result with all rule evaluations
        """
        rules_to_eval = []
        
        if rule_ids:
            rules_to_eval = [self.get_rule(rid) for rid in rule_ids if self.get_rule(rid)]
        elif context:
            rules_to_eval = self.list_rules(context)
        else:
            rules_to_eval = list(self.rules.values())
        
        rule_results = []
        for rule in rules_to_eval:
            result = self.evaluate_rule(rule.id, bid_data, evidence_data)
            rule_results.append(result)
        
        # Aggregate results
        passed_count = sum(1 for r in rule_results if r.get("passed"))
        failed_count = len(rule_results) - passed_count
        risk_signals = [r for r in rule_results if r.get("risk_signal_triggered")]
        
        overall_status = "COMPLIANT" if failed_count == 0 else "NON_COMPLIANT"
        if risk_signals:
            overall_status = "REQUIRES_REVIEW"
        
        return {
            "overall_status": overall_status,
            "passed_count": passed_count,
            "failed_count": failed_count,
            "total_rules": len(rule_results),
            "risk_signals_triggered": len(risk_signals),
            "risk_signal_details": risk_signals,
            "rule_results": rule_results,
            "evaluation_timestamp": __import__('datetime').datetime.utcnow().isoformat(),
        }
