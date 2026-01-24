"""
Explainable AI (XAI) module for generating human-readable explanations.
Provides transparency and traceability for claim decisions.
"""
from typing import Dict, List
from claim_models import DecisionExplanation, ClaimStatus, ClaimDecision


class XAIExplainer:
    """
    Generates human-readable explanations for claim decisions.
    Ensures transparency and builds user trust.
    """
    
    def __init__(self, llm_generator=None):
        """
        Initialize XAI explainer.
        
        Args:
            llm_generator: Optional LLM for generating natural language explanations
        """
        self.llm_generator = llm_generator
    
    def generate_detailed_explanation(self, decision: ClaimDecision) -> Dict:
        """
        Generate a detailed, user-friendly explanation of the decision.
        
        Args:
            decision: ClaimDecision object
            
        Returns:
            Dictionary with detailed explanation components
        """
        explanation = decision.explanation
        
        # Build structured explanation
        detailed_explanation = {
            "decision_summary": self._create_decision_summary(decision),
            "reasoning": self._create_reasoning(decision),
            "policy_clauses": self._format_policy_clauses(explanation.relevant_clauses),
            "calculation_breakdown": self._format_calculations(explanation.calculation_details),
            "next_steps": self._suggest_next_steps(decision),
            "confidence_level": self._interpret_confidence(explanation.confidence_score),
            "visual_breakdown": self._create_visual_data(decision)
        }
        
        # Optionally enhance with LLM
        if self.llm_generator:
            detailed_explanation["natural_language"] = self._generate_llm_explanation(decision)
        
        return detailed_explanation
    
    def _create_decision_summary(self, decision: ClaimDecision) -> str:
        """Create a one-line summary of the decision"""
        if decision.decision == ClaimStatus.APPROVED:
            return f"✅ Your claim of ₹{decision.claimed_amount:,.2f} has been APPROVED. Approved amount: ₹{decision.approved_amount:,.2f}"
        elif decision.decision == ClaimStatus.REJECTED:
            return f"❌ Your claim of ₹{decision.claimed_amount:,.2f} has been REJECTED."
        else:  # UNDER_REVIEW
            return f"⏳ Your claim of ₹{decision.claimed_amount:,.2f} is UNDER REVIEW by our claims team."
    
    def _create_reasoning(self, decision: ClaimDecision) -> Dict:
        """Create detailed reasoning breakdown"""
        explanation = decision.explanation
        
        reasoning = {
            "primary_reason": explanation.reason,
            "decision_factors": []
        }
        
        # Add specific factors based on calculation details
        calc = explanation.calculation_details
        
        if "coverage_limit" in calc:
            reasoning["decision_factors"].append({
                "factor": "Coverage Limit",
                "value": f"₹{calc['coverage_limit']:,.2f}",
                "description": "Maximum amount covered under your policy"
            })
        
        if "percentage_of_limit" in calc:
            percentage = calc["percentage_of_limit"]
            reasoning["decision_factors"].append({
                "factor": "Claim Percentage",
                "value": f"{percentage:.1f}%",
                "description": f"Your claim represents {percentage:.1f}% of your total coverage"
            })
        
        if "threshold_amount" in calc:
            reasoning["decision_factors"].append({
                "factor": "Auto-Approval Threshold",
                "value": f"₹{calc['threshold_amount']:,.2f}",
                "description": "Claims below this amount are automatically approved"
            })
        
        return reasoning
    
    def _format_policy_clauses(self, clauses: List[str]) -> List[Dict]:
        """Format policy clauses for display"""
        formatted_clauses = []
        
        for i, clause in enumerate(clauses, 1):
            formatted_clauses.append({
                "clause_number": f"Clause {i}",
                "text": clause,
                "relevance": "High" if i == 1 else "Medium"
            })
        
        return formatted_clauses
    
    def _format_calculations(self, calculations: Dict) -> List[Dict]:
        """Format calculation details for display"""
        formatted = []
        
        if "claimed_amount" in calculations:
            formatted.append({
                "item": "Claimed Amount",
                "value": f"₹{calculations['claimed_amount']:,.2f}",
                "type": "input"
            })
        
        if "coverage_limit" in calculations:
            formatted.append({
                "item": "Coverage Limit",
                "value": f"₹{calculations['coverage_limit']:,.2f}",
                "type": "policy"
            })
        
        if "threshold_amount" in calculations:
            formatted.append({
                "item": "Approval Threshold (80%)",
                "value": f"₹{calculations['threshold_amount']:,.2f}",
                "type": "threshold"
            })
        
        if "percentage_of_limit" in calculations:
            formatted.append({
                "item": "Percentage of Coverage Used",
                "value": f"{calculations['percentage_of_limit']:.1f}%",
                "type": "calculation"
            })
        
        return formatted
    
    def _suggest_next_steps(self, decision: ClaimDecision) -> List[str]:
        """Suggest next steps based on decision"""
        if decision.decision == ClaimStatus.APPROVED:
            return [
                "Your approved amount will be credited to your account within 5-7 business days",
                "You will receive a confirmation email with payment details",
                "Keep all original bills and receipts for your records",
                f"Claim ID for reference: {decision.claim_id}"
            ]
        elif decision.decision == ClaimStatus.REJECTED:
            return [
                "Review the rejection reason carefully",
                "You can appeal this decision within 30 days",
                "Contact our support team for clarification",
                "Submit additional documentation if available",
                f"Claim ID for reference: {decision.claim_id}"
            ]
        else:  # UNDER_REVIEW
            return [
                "Our claims specialist will review your case within 48 hours",
                "You may be contacted for additional documentation",
                "Check your email for updates",
                f"Track your claim status using ID: {decision.claim_id}"
            ]
    
    def _interpret_confidence(self, confidence_score: float) -> Dict:
        """Interpret confidence score for users"""
        if confidence_score >= 0.9:
            level = "Very High"
            description = "This decision is based on clear policy rules with high certainty"
        elif confidence_score >= 0.8:
            level = "High"
            description = "This decision is well-supported by policy terms"
        elif confidence_score >= 0.7:
            level = "Medium"
            description = "This decision may require additional review"
        else:
            level = "Low"
            description = "This decision has some uncertainty and may be reviewed"
        
        return {
            "level": level,
            "score": f"{confidence_score * 100:.0f}%",
            "description": description
        }
    
    def _create_visual_data(self, decision: ClaimDecision) -> Dict:
        """Create data for visual representation"""
        calc = decision.explanation.calculation_details
        
        coverage_limit = calc.get("coverage_limit", 500000)
        claimed_amount = calc.get("claimed_amount", 0)
        approved_amount = decision.approved_amount
        
        return {
            "coverage_chart": {
                "total_coverage": coverage_limit,
                "claimed": claimed_amount,
                "approved": approved_amount,
                "remaining": max(0, coverage_limit - approved_amount),
                "percentage_used": (approved_amount / coverage_limit * 100) if coverage_limit > 0 else 0
            },
            "status_indicator": {
                "status": decision.decision.value,
                "color": self._get_status_color(decision.decision),
                "icon": self._get_status_icon(decision.decision)
            }
        }
    
    def _get_status_color(self, status: ClaimStatus) -> str:
        """Get color code for status"""
        colors = {
            ClaimStatus.APPROVED: "#10b981",  # Green
            ClaimStatus.REJECTED: "#ef4444",  # Red
            ClaimStatus.UNDER_REVIEW: "#f59e0b",  # Orange
            ClaimStatus.PENDING: "#6b7280"  # Gray
        }
        return colors.get(status, "#6b7280")
    
    def _get_status_icon(self, status: ClaimStatus) -> str:
        """Get icon for status"""
        icons = {
            ClaimStatus.APPROVED: "✅",
            ClaimStatus.REJECTED: "❌",
            ClaimStatus.UNDER_REVIEW: "⏳",
            ClaimStatus.PENDING: "📋"
        }
        return icons.get(status, "📋")
    
    def _generate_llm_explanation(self, decision: ClaimDecision) -> str:
        """Generate natural language explanation using LLM (optional)"""
        if not self.llm_generator:
            return decision.explanation.reason
        
        try:
            prompt = f"""
            Explain this insurance claim decision in simple, friendly language:
            
            Decision: {decision.decision.value}
            Claimed Amount: ₹{decision.claimed_amount:,.2f}
            Approved Amount: ₹{decision.approved_amount:,.2f}
            Reason: {decision.explanation.reason}
            
            Make it conversational and empathetic. Keep it under 100 words.
            """
            
            # Use existing LLM generator if available
            response = self.llm_generator(prompt)
            return response
        except Exception as e:
            print(f"Error generating LLM explanation: {e}")
            return decision.explanation.reason
    
    def generate_audit_trail(self, decision: ClaimDecision) -> Dict:
        """Generate audit trail for compliance and traceability"""
        return {
            "claim_id": decision.claim_id,
            "policy_id": decision.policy_id,
            "timestamp": decision.timestamp,
            "decision": decision.decision.value,
            "decision_maker": "Automated Rule Engine",
            "rules_applied": decision.explanation.relevant_clauses,
            "calculation_details": decision.explanation.calculation_details,
            "confidence_score": decision.explanation.confidence_score,
            "processing_time_ms": decision.processing_time_ms,
            "traceable": True,
            "auditable": True
        }
    
    def compare_with_similar_claims(self, decision: ClaimDecision, historical_claims: List[Dict]) -> Dict:
        """Compare current decision with similar historical claims"""
        # This would query a database of historical claims
        # For now, return a template
        return {
            "similar_claims_found": 0,
            "average_approval_rate": "N/A",
            "consistency_score": "N/A",
            "note": "Historical comparison requires claim database"
        }
