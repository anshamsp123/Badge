"""
Data models for claim submission and processing.
Separate from existing models to avoid conflicts.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class TreatmentType(str, Enum):
    """Types of medical treatments"""
    APPENDICITIS = "appendicitis"
    CARDIAC = "cardiac"
    ORTHOPEDIC = "orthopedic"
    DENTAL = "dental"
    MATERNITY = "maternity"
    ACCIDENT = "accident"
    GENERAL_SURGERY = "general_surgery"
    HOSPITALIZATION = "hospitalization"
    OTHER = "other"


class ClaimStatus(str, Enum):
    """Claim processing status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    UNDER_REVIEW = "under_review"


class ClaimSubmission(BaseModel):
    """Model for claim submission request"""
    policy_id: str = Field(..., description="Policy number")
    treatment_type: TreatmentType = Field(..., description="Type of treatment")
    claimed_amount: float = Field(..., gt=0, description="Amount claimed in rupees")
    treatment_date: Optional[str] = Field(None, description="Date of treatment (DD/MM/YYYY)")
    hospital_name: Optional[str] = Field(None, description="Name of hospital")
    description: Optional[str] = Field(None, description="Brief description of treatment")


class PolicyRule(BaseModel):
    """Model for policy coverage rules"""
    clause_id: str
    clause_text: str
    coverage_limit: float
    coverage_percentage: Optional[float] = None
    exclusions: List[str] = []
    conditions: List[str] = []


class DecisionExplanation(BaseModel):
    """Model for XAI explanation"""
    decision: ClaimStatus
    reason: str
    relevant_clauses: List[str]
    calculation_details: Dict[str, Any]
    confidence_score: float = Field(..., ge=0, le=1)


class ClaimDecision(BaseModel):
    """Model for claim decision response"""
    claim_id: str
    policy_id: str
    treatment_type: str
    claimed_amount: float
    approved_amount: float
    decision: ClaimStatus
    explanation: DecisionExplanation
    timestamp: str
    processing_time_ms: int


class ClaimRecord(BaseModel):
    """Model for storing claim in database"""
    claim_id: str
    policy_id: str
    treatment_type: str
    claimed_amount: float
    approved_amount: float
    decision: ClaimStatus
    explanation: str
    relevant_clauses: List[str]
    submitted_at: str
    decided_at: str
    user_description: Optional[str] = None
    hospital_name: Optional[str] = None
    treatment_date: Optional[str] = None
