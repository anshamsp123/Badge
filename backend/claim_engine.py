"""
Rule-based decision engine for insurance claim processing.
Uses policy information from RAG system to make decisions.
"""
import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from claim_models import (
    ClaimSubmission, ClaimDecision, ClaimStatus, 
    DecisionExplanation, PolicyRule
)


from fraud_detector import fraud_detector

class ClaimDecisionEngine:
    """
    Rule-based engine for processing insurance claims.
    Integrates with RAG system to fetch policy details.
    """
    
    def __init__(self, rag_engine=None):
        """
        Initialize decision engine.
        
        Args:
            rag_engine: Optional RAG engine for policy lookups
        """
        self.rag_engine = rag_engine
        self.fraud_detector = fraud_detector

        
        # Default coverage rules (can be overridden by policy)
        self.default_rules = {
            "max_coverage": 500000,  # ₹5,00,000
            "approval_threshold": 0.80,  # 80% of coverage limit
            "excluded_treatments": ["cosmetic", "dental_routine", "maternity"],
            "waiting_period_days": 30
        }
    
    def process_claim(self, claim: ClaimSubmission) -> ClaimDecision:
        """
        Process a claim and return decision with explanation.
        
        Args:
            claim: ClaimSubmission object
            
        Returns:
            ClaimDecision with approval/rejection and explanation
        """
        start_time = datetime.now()
        
        # Step 1: Fetch policy details from RAG system
        policy_info = self._fetch_policy_info(claim.policy_id)
        
        # Step 2: Extract coverage rules
        coverage_limit = self._extract_coverage_limit(policy_info)
        exclusions = self._extract_exclusions(policy_info)
        
        # Step 2.5: Fraud Detection
        fraud_score, risk_level = self.fraud_detector.predict_fraud({
            "claimed_amount": claim.claimed_amount,
            "hospital_tier": "Tier 2", # Default for now, could be extracted
            "past_claims": 0           # Placeholder
        })
        
        # Step 3: Apply decision rules
        decision, explanation = self._apply_rules(
            claim, coverage_limit, exclusions, policy_info, fraud_score, risk_level
        )
        
        # Step 4: Calculate approved amount
        approved_amount = self._calculate_approved_amount(
            claim.claimed_amount, coverage_limit, decision
        )
        
        # Step 5: Generate claim ID
        claim_id = self._generate_claim_id(claim.policy_id)
        
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return ClaimDecision(
            claim_id=claim_id,
            policy_id=claim.policy_id,
            treatment_type=claim.treatment_type.value,
            claimed_amount=claim.claimed_amount,
            approved_amount=approved_amount,
            decision=decision,
            explanation=explanation,
            timestamp=datetime.now().isoformat(),
            processing_time_ms=processing_time
        )
    
    def _fetch_policy_info(self, policy_id: str) -> Dict:
        """Fetch policy information using RAG system"""
        if not self.rag_engine:
            print("No RAG engine available, using defaults")
            return {"policy_id": policy_id, "coverage_limit": 500000}
        
        try:
            print(f"Fetching policy info for {policy_id}...")
            # Query RAG for policy details
            query = f"What is the coverage limit and exclusions for policy {policy_id}?"
            
            # Add a timeout/fallback mechanism here if possible, but for now just try-except
            response = self.rag_engine.query(query, top_k=3)
            
            return {
                "policy_id": policy_id,
                "rag_response": response.answer,
                "sources": [s.text for s in response.sources],
                "confidence": response.confidence
            }
        except Exception as e:
            print(f"Error fetching policy info (using defaults): {e}")
            # FALLBACK: Return default info so the claim can still be processed
            return {
                "policy_id": policy_id, 
                "coverage_limit": 500000,
                "rag_response": "Could not fetch specific policy details due to system load. Using standard policy terms.",
                "sources": [],
                "confidence": 0.5
            }
    
    def _extract_coverage_limit(self, policy_info: Dict) -> float:
        """Extract coverage limit from policy information"""
        # Try to extract from RAG response
        if "rag_response" in policy_info:
            text = policy_info["rag_response"]
            # Look for patterns like "₹5,00,000" or "500000"
            match = re.search(r'₹?\s*([\d,]+(?:\.\d{2})?)', text)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    return float(amount_str)
                except:
                    pass
        
        # Check sources
        if "sources" in policy_info:
            for source in policy_info["sources"]:
                match = re.search(r'Sum\s*Assured[:\s]*₹?\s*([\d,]+)', source, re.IGNORECASE)
                if match:
                    amount_str = match.group(1).replace(',', '')
                    try:
                        return float(amount_str)
                    except:
                        pass
        
        # Default
        return self.default_rules["max_coverage"]
    
    def _extract_exclusions(self, policy_info: Dict) -> List[str]:
        """Extract exclusions from policy information"""
        exclusions = []
        
        if "rag_response" in policy_info:
            text = policy_info["rag_response"].lower()
            if "cosmetic" in text or "plastic surgery" in text:
                exclusions.append("cosmetic")
            if "dental" in text:
                exclusions.append("dental")
            if "maternity" in text:
                exclusions.append("maternity")
        
        if "sources" in policy_info:
            for source in policy_info["sources"]:
                if "EXCLUSIONS" in source.upper():
                    # Extract exclusion items
                    lines = source.split('\n')
                    for line in lines:
                        if any(word in line.lower() for word in ["cosmetic", "dental", "maternity"]):
                            exclusions.append(line.strip())
        
        return exclusions if exclusions else self.default_rules["excluded_treatments"]
    

    def _apply_rules(
        self, 
        claim: ClaimSubmission, 
        coverage_limit: float,
        exclusions: List[str],
        policy_info: Dict,
        fraud_score: float,
        risk_level: str
    ) -> Tuple[ClaimStatus, DecisionExplanation]:
        """Apply decision rules and generate explanation"""
        
        relevant_clauses = []
        calculation_details = {
            "coverage_limit": coverage_limit,
            "claimed_amount": claim.claimed_amount,
            "threshold_amount": coverage_limit * self.default_rules["approval_threshold"],
            "percentage_of_limit": (claim.claimed_amount / coverage_limit * 100) if coverage_limit > 0 else 0,
            "fraud_risk_score": f"{fraud_score:.2f}",
            "fraud_risk_level": risk_level
        }
        
        # Rule 0: Fraud Check
        if risk_level == "High":
             return (
                ClaimStatus.REJECTED,
                DecisionExplanation(
                    decision=ClaimStatus.REJECTED,
                    reason=f"Claim rejected due to High Fraud Risk detected (Score: {fraud_score:.2f}). Anomalous patterns found in claim details.",
                    relevant_clauses=["Fraud Detection Protocol: Automatic rejection for high-risk anomalies"],
                    calculation_details=calculation_details,
                    confidence_score=0.99
                )
            )
        
        # Rule 1: Check if treatment is excluded
        treatment_name = claim.treatment_type.value.lower()
        for exclusion in exclusions:
            if exclusion.lower() in treatment_name or treatment_name in exclusion.lower():
                return (
                    ClaimStatus.REJECTED,
                    DecisionExplanation(
                        decision=ClaimStatus.REJECTED,
                        reason=f"Claim rejected because {claim.treatment_type.value} is listed in policy exclusions.",
                        relevant_clauses=[f"Exclusion: {exclusion}"],
                        calculation_details=calculation_details,
                        confidence_score=0.95
                    )
                )
        
        # Rule 2: Check if amount exceeds coverage limit
        if claim.claimed_amount > coverage_limit:
            relevant_clauses.append(f"Coverage Limit: ₹{coverage_limit:,.2f}")
            return (
                ClaimStatus.REJECTED,
                DecisionExplanation(
                    decision=ClaimStatus.REJECTED,
                    reason=f"Claim rejected because claimed amount (₹{claim.claimed_amount:,.2f}) exceeds the coverage limit (₹{coverage_limit:,.2f}).",
                    relevant_clauses=relevant_clauses,
                    calculation_details=calculation_details,
                    confidence_score=0.98
                )
            )
        
        # Rule 3: Check if amount is within approval threshold (80%)
        threshold = coverage_limit * self.default_rules["approval_threshold"]
        
        if claim.claimed_amount <= threshold:
            relevant_clauses.append(f"Coverage Limit: ₹{coverage_limit:,.2f}")
            relevant_clauses.append(f"Automatic Approval Threshold: 80% of coverage limit")
            
            percentage = (claim.claimed_amount / coverage_limit) * 100
            
            return (
                ClaimStatus.APPROVED,
                DecisionExplanation(
                    decision=ClaimStatus.APPROVED,
                    reason=f"Claim approved because claimed amount (₹{claim.claimed_amount:,.2f}) is within the coverage limit (₹{coverage_limit:,.2f}). The claim represents {percentage:.1f}% of your total coverage, which is within the automatic approval threshold of 80%.",
                    relevant_clauses=relevant_clauses,
                    calculation_details=calculation_details,
                    confidence_score=0.92
                )
            )
        
        # Rule 4: Amount between 80-100% requires review
        else:
            relevant_clauses.append(f"Coverage Limit: ₹{coverage_limit:,.2f}")
            relevant_clauses.append(f"High-value claim review policy")
            
            return (
                ClaimStatus.UNDER_REVIEW,
                DecisionExplanation(
                    decision=ClaimStatus.UNDER_REVIEW,
                    reason=f"Claim requires manual review because claimed amount (₹{claim.claimed_amount:,.2f}) is between 80-100% of coverage limit (₹{coverage_limit:,.2f}). A claims specialist will review your case within 48 hours.",
                    relevant_clauses=relevant_clauses,
                    calculation_details=calculation_details,
                    confidence_score=0.85
                )
            )
    
    def _calculate_approved_amount(
        self, 
        claimed_amount: float, 
        coverage_limit: float,
        decision: ClaimStatus
    ) -> float:
        """Calculate approved amount based on decision"""
        if decision == ClaimStatus.APPROVED:
            return min(claimed_amount, coverage_limit)
        elif decision == ClaimStatus.UNDER_REVIEW:
            return 0.0  # Will be determined after review
        else:  # REJECTED
            return 0.0
    
    def _generate_claim_id(self, policy_id: str) -> str:
        """Generate unique claim ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"CLM-{timestamp}-{policy_id[:8]}"
    
    def get_policy_summary(self, policy_id: str) -> Dict:
        """Get summary of policy coverage using RAG"""
        if not self.rag_engine:
            return {
                "policy_id": policy_id,
                "coverage_limit": "₹5,00,000",
                "status": "Active"
            }
        
        try:
            query = f"Summarize the coverage details for policy {policy_id}"
            response = self.rag_engine.query(query, top_k=3)
            
            return {
                "policy_id": policy_id,
                "summary": response.answer,
                "confidence": response.confidence,
                "sources": len(response.sources)
            }
        except Exception as e:
            print(f"Error getting policy summary: {e}")
            return {
                "policy_id": policy_id,
                "error": str(e)
            }
