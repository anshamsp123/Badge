from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    POLICY = "policy"
    CLAIM_FORM = "claim_form"
    HOSPITAL_BILL = "hospital_bill"
    SURVEYOR_REPORT = "surveyor_report"
    DISCHARGE_SUMMARY = "discharge_summary"
    FIR = "fir"
    PHOTO = "photo"
    OTHER = "other"


class ProcessingStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    OCR_COMPLETE = "ocr_complete"
    EXTRACTION_COMPLETE = "extraction_complete"
    EMBEDDING_COMPLETE = "embedding_complete"
    COMPLETED = "completed"
    FAILED = "failed"


class ExtractedEntity(BaseModel):
    entity_type: str
    value: str
    confidence: Optional[float] = None


class DocumentMetadata(BaseModel):
    doc_id: str
    user_id: Optional[str] = None  # Added user_id
    filename: str
    doc_type: DocumentType
    upload_time: datetime
    status: ProcessingStatus
    page_count: Optional[int] = None
    file_size: int
    extracted_entities: List[ExtractedEntity] = []


class ChunkMetadata(BaseModel):
    chunk_id: str
    doc_id: str
    doc_type: str
    filename: str
    page_number: Optional[int] = None
    chunk_index: int
    text: str


class UploadResponse(BaseModel):
    doc_id: str
    filename: str
    status: str
    message: str


class StatusResponse(BaseModel):
    doc_id: str
    filename: str
    status: ProcessingStatus
    progress: int  # 0-100
    extracted_entities: List[ExtractedEntity] = []
    error: Optional[str] = None


class QueryRequest(BaseModel):
    question: str
    doc_ids: Optional[List[str]] = None  # Filter by specific documents
    top_k: int = Field(default=5, ge=1, le=20)


class SourceChunk(BaseModel):
    text: str
    doc_id: str
    filename: str
    doc_type: str
    page_number: Optional[int] = None
    similarity_score: float


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: List[SourceChunk]
    confidence: Optional[float] = None



class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str

class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    full_name: Optional[str] = None
