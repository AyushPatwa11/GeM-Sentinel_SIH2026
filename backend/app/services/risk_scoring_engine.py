"""Risk Scoring Engine for Phase 6 - Signal aggregation with configurable weights."""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class RiskWeightConfig:
    """Configurable risk weights for different signal types."""
    # Document-related signals
    missing_mandatory_doc: float = 8.0
    document_quality_low: float = 4.0
    
    # Verification signals
    verification_failed: float = 9.0
    verification_unavailable: float = 3.0
    name_mismatch: float = 7.0
    
    # Compliance signals
    compliance_violation: float = 8.5
    compliance_waived: float = 2.0
    
    # History signals
    previous_violation: float = 6.0
    debarment_flag: float = 10.0
    
    # External service signals
    blacklist_match: float = 10.0
    sanctions_flag: float = 9.5
    
    # Default weight for unknown signals
    default_weight: float = 5.0
    
    # Normalization factor
    normalization_factor: float = 100.0


class RiskScoringEngine:
    """Aggregates risk signals and computes bid risk score."""
    
    def __init__(self, config: Optional[RiskWeightConfig] = None):
        """Initialize with optional custom configuration.
        
        Args:
            config: RiskWeightConfig with custom weights (uses defaults if None)
        """
        self.config = config or RiskWeightConfig()
    
    def aggregate_signals(
        self,
        signals: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Aggregate multiple risk signals into comprehensive assessment.
        
        Args:
            signals: List of risk signal dictionaries
                [
                    {
                        "signal_type": "missing_mandatory_doc",
                        "weight": 1.0,
                        "severity": 0.8,
                        "source": "compliance_rule",
                        "details": {...},
                    },
                    ...
                ]
        
        Returns:
            Comprehensive risk assessment:
            {
                "total_score": 65.5,  # 0-100
                "risk_level": "HIGH",
                "signal_count": 3,
                "signals_by_type": {...},
                "signal_breakdown": {...},
                "risk_factors": [...],
                "mitigating_factors": [...],
            }
        """
        if not signals:
            return {
                "total_score": 0.0,
                "risk_level": "LOW",
                "signal_count": 0,
                "signals_by_type": {},
                "signal_breakdown": {},
                "risk_factors": [],
                "mitigating_factors": [],
            }
        
        # Group signals by type
        signals_by_type = {}
        for signal in signals:
            signal_type = signal.get("signal_type", "unknown")
            if signal_type not in signals_by_type:
                signals_by_type[signal_type] = []
            signals_by_type[signal_type].append(signal)
        
        # Compute weighted score for each signal type
        type_scores = {}
        for signal_type, type_signals in signals_by_type.items():
            # Get weight from config
            weight = getattr(self.config, signal_type, self.config.default_weight)
            
            # Average severity across signals of this type
            severities = [s.get("severity", 0.5) for s in type_signals]
            avg_severity = sum(severities) / len(severities) if severities else 0.5
            
            # Compute type score: weight * severity
            type_score = weight * avg_severity
            type_scores[signal_type] = {
                "weight": weight,
                "count": len(type_signals),
                "avg_severity": avg_severity,
                "type_score": type_score,
            }
        
        # Aggregate to total score using weighted average
        total_weighted_score = sum(ts["type_score"] for ts in type_scores.values())
        total_signals = len(signals)
        
        # Normalize to 0-100 scale
        # Higher weights and severities → higher risk
        max_possible_score = self.config.normalization_factor
        total_score = min(100.0, (total_weighted_score / len(type_scores)) if type_scores else 0.0)
        
        # Determine risk level
        risk_level = self._compute_risk_level(total_score)
        
        # Identify risk factors and mitigating factors
        risk_factors = self._extract_risk_factors(signals, type_scores)
        mitigating_factors = self._extract_mitigating_factors(signals, type_scores)
        
        return {
            "total_score": round(total_score, 2),
            "risk_level": risk_level,
            "signal_count": total_signals,
            "signals_by_type": type_scores,
            "signal_breakdown": {
                "critical_count": sum(1 for s in signals if s.get("severity", 0.5) >= 0.8),
                "high_count": sum(1 for s in signals if 0.5 <= s.get("severity", 0.5) < 0.8),
                "medium_count": sum(1 for s in signals if 0.3 <= s.get("severity", 0.5) < 0.5),
                "low_count": sum(1 for s in signals if s.get("severity", 0.5) < 0.3),
            },
            "risk_factors": risk_factors,
            "mitigating_factors": mitigating_factors,
        }
    
    def _compute_risk_level(self, score: float) -> str:
        """Map numeric score to risk level.
        
        Args:
            score: Risk score (0-100)
            
        Returns:
            Risk level: LOW, MEDIUM, HIGH, CRITICAL
        """
        if score < 25:
            return "LOW"
        elif score < 50:
            return "MEDIUM"
        elif score < 75:
            return "HIGH"
        else:
            return "CRITICAL"
    
    def _extract_risk_factors(
        self,
        signals: List[Dict[str, Any]],
        type_scores: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Extract high-impact risk factors from signals.
        
        Args:
            signals: List of risk signals
            type_scores: Computed scores by type
            
        Returns:
            List of risk factors ordered by impact
        """
        risk_factors = []
        
        # Critical signals (verification failures, debarment, etc.)
        critical_types = [
            "verification_failed",
            "debarment_flag",
            "blacklist_match",
            "sanctions_flag",
            "compliance_violation",
        ]
        
        for signal_type in critical_types:
            if signal_type in type_scores:
                data = type_scores[signal_type]
                risk_factors.append({
                    "factor": signal_type,
                    "type": "CRITICAL",
                    "impact": data["type_score"],
                    "count": data["count"],
                    "explanation": self._get_risk_explanation(signal_type),
                })
        
        # Sort by impact
        risk_factors.sort(key=lambda x: x["impact"], reverse=True)
        
        return risk_factors[:5]  # Top 5 factors
    
    def _extract_mitigating_factors(
        self,
        signals: List[Dict[str, Any]],
        type_scores: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Extract factors that lower risk assessment.
        
        Args:
            signals: List of risk signals
            type_scores: Computed scores by type
            
        Returns:
            List of mitigating factors
        """
        mitigating_factors = []
        
        # Low-weight signals that passed
        low_impact_types = [
            "document_quality_low",
            "compliance_waived",
            "verification_unavailable",
        ]
        
        for signal_type in low_impact_types:
            if signal_type in type_scores:
                data = type_scores[signal_type]
                if data.get("count", 0) > 0:
                    mitigating_factors.append({
                        "factor": signal_type,
                        "type": "MITIGATING",
                        "impact": -data["type_score"],  # Negative to show mitigation
                        "count": data["count"],
                        "explanation": f"{signal_type} addressed or waived",
                    })
        
        return mitigating_factors
    
    def _get_risk_explanation(self, signal_type: str) -> str:
        """Get human-readable explanation for signal type.
        
        Args:
            signal_type: Type of risk signal
            
        Returns:
            Explanation text
        """
        explanations = {
            "missing_mandatory_doc": "Mandatory compliance document is missing",
            "document_quality_low": "Document quality or OCR extraction is poor",
            "verification_failed": "External verification against government source failed",
            "verification_unavailable": "External verification service unavailable",
            "name_mismatch": "Entity name doesn't match across documents",
            "compliance_violation": "Compliance rule violation detected",
            "compliance_waived": "Compliance waived by authorized officer",
            "previous_violation": "Organization has previous compliance violations",
            "debarment_flag": "Organization flagged for debarment",
            "blacklist_match": "Organization matches blacklist entries",
            "sanctions_flag": "Organization has sanctions flag",
        }
        return explanations.get(signal_type, f"Risk signal: {signal_type}")
    
    def decompose_score(
        self,
        signals: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Decompose risk score into component parts for explainability.
        
        Args:
            signals: List of risk signals
            
        Returns:
            Detailed decomposition with each component's contribution
        """
        # Group by source
        sources = {}
        for signal in signals:
            source = signal.get("source", "unknown")
            if source not in sources:
                sources[source] = []
            sources[source].append(signal)
        
        # Compute contribution by source
        decomposition = []
        total_contribution = 0
        
        for source, source_signals in sources.items():
            # Average severity for source
            severities = [s.get("severity", 0.5) for s in source_signals]
            avg_severity = sum(severities) / len(severities)
            
            contribution = len(source_signals) * avg_severity
            total_contribution += contribution
            
            decomposition.append({
                "source": source,
                "signal_count": len(source_signals),
                "avg_severity": round(avg_severity, 2),
                "contribution": round(contribution, 2),
                "percentage": 0.0,  # Will compute after total
            })
        
        # Compute percentages
        for item in decomposition:
            if total_contribution > 0:
                item["percentage"] = round((item["contribution"] / total_contribution) * 100, 1)
        
        # Sort by contribution
        decomposition.sort(key=lambda x: x["contribution"], reverse=True)
        
        return {
            "total_contribution": round(total_contribution, 2),
            "sources": decomposition,
        }
    
    def recommend_actions(
        self,
        risk_assessment: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Recommend actions based on risk assessment.
        
        Args:
            risk_assessment: Risk assessment result from aggregate_signals()
            
        Returns:
            List of recommended actions ordered by priority
        """
        recommendations = []
        risk_level = risk_assessment.get("risk_level", "MEDIUM")
        risk_factors = risk_assessment.get("risk_factors", [])
        
        # CRITICAL risk: Immediate action
        if risk_level == "CRITICAL":
            recommendations.append({
                "priority": "URGENT",
                "action": "REJECT_BID",
                "reason": "Critical risk factors identified",
                "details": "Multiple high-severity compliance violations detected",
            })
            return recommendations
        
        # HIGH risk: Manual review required
        if risk_level == "HIGH":
            recommendations.append({
                "priority": "HIGH",
                "action": "REQUEST_CLARIFICATION",
                "reason": "High risk factors require clarification",
                "details": f"Top risk factors: {', '.join([rf.get('factor', '') for rf in risk_factors[:3]])}",
            })
            recommendations.append({
                "priority": "HIGH",
                "action": "VERIFY_DOCUMENTS",
                "reason": "Additional document verification recommended",
                "details": "Request officer review of compliance documentation",
            })
        
        # MEDIUM risk: Conditional approval with monitoring
        elif risk_level == "MEDIUM":
            recommendations.append({
                "priority": "MEDIUM",
                "action": "CONDITIONAL_APPROVAL",
                "reason": "Moderate risk can be addressed",
                "details": "Recommend conditions and monitoring period",
            })
        
        # LOW risk: Proceed with normal approval
        else:
            recommendations.append({
                "priority": "LOW",
                "action": "APPROVE",
                "reason": "Low risk assessment",
                "details": "Proceed with standard approval process",
            })
        
        return recommendations
