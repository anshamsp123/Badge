from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import uuid
import shutil
from typing import List, Dict
import json
from datetime import datetime

# Import our modules
import config
from models import (
    DocumentType, ProcessingStatus, DocumentMetadata,
    UploadResponse, StatusResponse, QueryRequest, QueryResponse
)
from ocr_processor import OCRProcessor
from text_cleaner import TextCleaner
from entity_extractor import EntityExtractor
from chunker import TextChunker
from embedder import Embedder
from vector_store import VectorStore
from rag_engine import RAGEngine

# Import new claim processing modules
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends, status

# Import new claim processing modules
from claim_models import ClaimSubmission, ClaimDecision, ClaimRecord
from claim_engine import ClaimDecisionEngine
from xai_explainer import XAIExplainer

# Import auth modules
import auth
from auth import get_current_active_user
from models import User, UserCreate, UserInDB

# Initialize FastAPI app
app = FastAPI(
    title="Insurance Claims Processing System",
    description="End-to-end system for processing insurance claims with RAG-based chatbot",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (frontend)
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

# Initialize components
ocr_processor = OCRProcessor()
text_cleaner = TextCleaner()
entity_extractor = EntityExtractor()
text_chunker = TextChunker()
embedder = Embedder()
vector_store = VectorStore()
rag_engine = RAGEngine(vector_store, embedder)

# Initialize new claim processing components
claim_engine = ClaimDecisionEngine(rag_engine)  # Connected to RAG for policy lookups
xai_explainer = XAIExplainer()

# In-memory storage for document metadata
# Initialize MongoDB
mongo_db = None
claims_db_handler = None
users_db_handler = None
documents_db_handler = None

if config.USE_MONGODB:
    try:
        from database import MongoDB, ClaimsDB, UsersDB, DocumentsDB
        mongo_db = MongoDB(config.MONGODB_URI, config.MONGODB_DATABASE)
        claims_db_handler = ClaimsDB(mongo_db)
        users_db_handler = UsersDB(mongo_db)
        documents_db_handler = DocumentsDB(mongo_db)
        print("[OK] Using MongoDB for all storage")
    except Exception as e:
        print(f"[WARNING] MongoDB connection failed: {e}")
        print("[WARNING] Falling back to in-memory storage")
        claims_db_handler = None
        users_db_handler = None
        documents_db_handler = None
else:
    print("[WARNING] No MongoDB URI configured, using in-memory storage")

# Fallback: In-memory storage if MongoDB not available
if claims_db_handler is None:
    claims_db: Dict[str, Dict] = {}
    documents_db: Dict[str, DocumentMetadata] = {}
    users_db: Dict[str, UserInDB] = {}
    print("Using in-memory storage for all data")

def get_user(username: str):
    if users_db_handler:
        user_data = users_db_handler.get_user(username)
        if user_data:
            return UserInDB(**user_data)
        return None
    
    # Fallback to in-memory
    if username in users_db:
        return users_db[username]
    return None



@app.get("/")
async def root():
    """Redirect to login page."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/login.html", status_code=302)


@app.get("/index.html")
async def index_page():
    """Serve the main application (protected by client-side auth)."""
    index_path = frontend_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    raise HTTPException(status_code=404, detail="Application not found")


@app.get("/login.html")
async def login_page():
    """Serve the login page."""
    login_path = frontend_path / "login.html"
    if login_path.exists():
        return FileResponse(str(login_path))
    raise HTTPException(status_code=404, detail="Login page not found")


@app.post("/api/auth/register")
async def register(user: UserCreate):
    """Register a new user."""
    # Check if user already exists
    existing_user = get_user(user.username)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    
    # Hash password and create user
    hashed_password = auth.get_password_hash(user.password)
    user_in_db = UserInDB(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password
    )
    
    # Save user
    if users_db_handler:
        users_db_handler.create_user(user_in_db.dict())
    else:
        users_db[user.username] = user_in_db
    
    return {"message": "User created successfully", "username": user.username}


@app.post("/api/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login endpoint."""
    user = get_user(form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = auth.timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@app.post("/api/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = "other",
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload a document for processing.
    
    Args:
        file: Uploaded file
        doc_type: Type of document (policy, claim_form, etc.)
        
    Returns:
        UploadResponse with document ID and status
    """
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in config.SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Supported: {config.SUPPORTED_EXTENSIONS}"
        )
    
    # Generate unique document ID
    doc_id = str(uuid.uuid4())
    
    # Save uploaded file
    file_path = config.UPLOAD_DIR / f"{doc_id}{file_ext}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create document metadata
    doc_metadata = DocumentMetadata(
        doc_id=doc_id,
        user_id=current_user.username,  # Associate with user
        filename=file.filename,
        doc_type=DocumentType(doc_type),
        upload_time=datetime.now(),
        status=ProcessingStatus.UPLOADED,
        file_size=file_path.stat().st_size
    )
    
    # Save metadata
    if documents_db_handler:
        documents_db_handler.save_document(doc_metadata.dict())
    else:
        documents_db[doc_id] = doc_metadata
    
    # Start background processing
    background_tasks.add_task(process_document, doc_id, file_path)
    
    return UploadResponse(
        doc_id=doc_id,
        filename=file.filename,
        status="uploaded",
        message="Document uploaded successfully. Processing started."
    )


async def process_document(doc_id: str, file_path: Path):
    """
    Background task to process uploaded document.
    """
    try:
        # Update status
        if documents_db_handler:
            doc = documents_db_handler.get_document(doc_id)
            if doc:
                doc['status'] = ProcessingStatus.PROCESSING
                documents_db_handler.save_document(doc)
        else:
            documents_db[doc_id].status = ProcessingStatus.PROCESSING
        
        # Step 1: OCR and text extraction
        print(f"Processing document {doc_id}: OCR extraction...")
        ocr_result = ocr_processor.extract_text(file_path)
        raw_text = ocr_result['text']
        pages = ocr_result['pages']
        
        if documents_db_handler:
            doc = documents_db_handler.get_document(doc_id)
            doc['page_count'] = ocr_result['metadata']['page_count']
            doc['status'] = ProcessingStatus.OCR_COMPLETE
            documents_db_handler.save_document(doc)
        else:
            documents_db[doc_id].page_count = ocr_result['metadata']['page_count']
            documents_db[doc_id].status = ProcessingStatus.OCR_COMPLETE
        
        # Step 2: Text cleaning
        print(f"Processing document {doc_id}: Text cleaning...")
        cleaned_text = text_cleaner.clean_full_document(raw_text)
        
        # Save processed text
        processed_path = config.PROCESSED_DIR / f"{doc_id}.txt"
        with open(processed_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_text)
        
        # Step 3: Entity extraction
        print(f"Processing document {doc_id}: Entity extraction...")
        entities = entity_extractor.extract_entities(cleaned_text)
        
        if documents_db_handler:
            doc = documents_db_handler.get_document(doc_id)
            doc['extracted_entities'] = entities
            doc['status'] = ProcessingStatus.EXTRACTION_COMPLETE
            documents_db_handler.save_document(doc)
        else:
            documents_db[doc_id].extracted_entities = entities
            documents_db[doc_id].status = ProcessingStatus.EXTRACTION_COMPLETE
        
        # Step 4: Text chunking
        print(f"Processing document {doc_id}: Text chunking...")
        
        # Get filename and doc_type
        if documents_db_handler:
            doc = documents_db_handler.get_document(doc_id)
            filename = doc['filename']
            doc_type = doc['doc_type']
        else:
            filename = documents_db[doc_id].filename
            doc_type = documents_db[doc_id].doc_type.value

        chunks = text_chunker.chunk_document(
            text=cleaned_text,
            doc_id=doc_id,
            filename=filename,
            doc_type=doc_type,
            pages=pages
        )
        
        # Step 5: Generate embeddings
        print(f"Processing document {doc_id}: Generating embeddings...")
        chunk_texts = [chunk.text for chunk in chunks]
        embeddings = embedder.embed_batch(chunk_texts)
        
        # Step 6: Store in vector database
        print(f"Processing document {doc_id}: Storing in vector database...")
        vector_store.add_embeddings(embeddings, chunks)
        vector_store.save()
        
        if documents_db_handler:
            doc = documents_db_handler.get_document(doc_id)
            doc['status'] = ProcessingStatus.COMPLETED
            documents_db_handler.save_document(doc)
        else:
            documents_db[doc_id].status = ProcessingStatus.COMPLETED
            
        print(f"Document {doc_id} processing completed!")
        
    except Exception as e:
        print(f"Error processing document {doc_id}: {e}")
        if documents_db_handler:
            doc = documents_db_handler.get_document(doc_id)
            if doc:
                doc['status'] = ProcessingStatus.FAILED
                documents_db_handler.save_document(doc)
        else:
            documents_db[doc_id].status = ProcessingStatus.FAILED
        raise


@app.get("/api/status/{doc_id}", response_model=StatusResponse)
async def get_status(
    doc_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get processing status of a document."""
    if documents_db_handler:
        doc_data = documents_db_handler.get_document(doc_id)
        if not doc_data:
            raise HTTPException(status_code=404, detail="Document not found")
        doc = DocumentMetadata(**doc_data)
    else:
        if doc_id not in documents_db:
            raise HTTPException(status_code=404, detail="Document not found")
        doc = documents_db[doc_id]
    
    # Check ownership
    if doc.user_id != current_user.username:
        raise HTTPException(status_code=403, detail="Not authorized to access this document")
    
    # Calculate progress percentage
    progress_map = {
        ProcessingStatus.UPLOADED: 10,
        ProcessingStatus.PROCESSING: 30,
        ProcessingStatus.OCR_COMPLETE: 50,
        ProcessingStatus.EXTRACTION_COMPLETE: 70,
        ProcessingStatus.EMBEDDING_COMPLETE: 90,
        ProcessingStatus.COMPLETED: 100,
        ProcessingStatus.FAILED: 0
    }
    
    return StatusResponse(
        doc_id=doc.doc_id,
        filename=doc.filename,
        status=doc.status,
        progress=progress_map.get(doc.status, 0),
        extracted_entities=doc.extracted_entities,
        error=None if doc.status != ProcessingStatus.FAILED else "Processing failed"
    )


@app.post("/api/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Query the chatbot with a question."""
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    # Use RAG engine to answer
    response = rag_engine.query(
        question=request.question,
        doc_ids=request.doc_ids,
        top_k=request.top_k
    )
    
    return response


@app.get("/api/documents")
async def list_documents(current_user: User = Depends(get_current_active_user)):
    """List all uploaded documents."""
    if documents_db_handler:
        docs_data = documents_db_handler.get_user_documents(current_user.username)
        docs = [DocumentMetadata(**d) for d in docs_data]
    else:
        docs = [
            doc for doc in documents_db.values()
            if doc.user_id == current_user.username
        ]

    return {
        "documents": [
            {
                "doc_id": doc.doc_id,
                "filename": doc.filename,
                "doc_type": doc.doc_type.value,
                "status": doc.status.value,
                "upload_time": doc.upload_time.isoformat(),
                "page_count": doc.page_count,
                "entity_count": len(doc.extracted_entities)
            }
            for doc in docs
        ]
    }


@app.get("/api/chunks/{doc_id}")
async def get_document_chunks(
    doc_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get all chunks for a specific document."""
    if documents_db_handler:
        doc_data = documents_db_handler.get_document(doc_id)
        if not doc_data:
            raise HTTPException(status_code=404, detail="Document not found")
        if doc_data['user_id'] != current_user.username:
            raise HTTPException(status_code=403, detail="Not authorized")
    else:
        if doc_id not in documents_db:
            raise HTTPException(status_code=404, detail="Document not found")
        if documents_db[doc_id].user_id != current_user.username:
            raise HTTPException(status_code=403, detail="Not authorized to access this document")
    
    chunks = vector_store.get_chunks_by_doc_id(doc_id)
    return {"doc_id": doc_id, "chunks": chunks}


@app.delete("/api/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Delete a document and its data."""
    if documents_db_handler:
        doc_data = documents_db_handler.get_document(doc_id)
        if not doc_data:
            raise HTTPException(status_code=404, detail="Document not found")
        if doc_data['user_id'] != current_user.username:
            raise HTTPException(status_code=403, detail="Not authorized")
        documents_db_handler.delete_document(doc_id)
    else:
        if doc_id not in documents_db:
            raise HTTPException(status_code=404, detail="Document not found")
        if documents_db[doc_id].user_id != current_user.username:
            raise HTTPException(status_code=403, detail="Not authorized to access this document")
        del documents_db[doc_id]
    
    # Delete from vector store
    vector_store.delete_document(doc_id)
    vector_store.save()
    
    # Delete files
    for ext in config.SUPPORTED_EXTENSIONS:
        file_path = config.UPLOAD_DIR / f"{doc_id}{ext}"
        if file_path.exists():
            file_path.unlink()
    
    processed_path = config.PROCESSED_DIR / f"{doc_id}.txt"
    if processed_path.exists():
        processed_path.unlink()
    
    return {"message": f"Document {doc_id} deleted successfully"}


@app.get("/api/stats")
async def get_stats():
    """Get system statistics."""
    vector_stats = vector_store.get_stats()
    
    if documents_db_handler:
        doc_stats = documents_db_handler.get_stats()
        return {
            **doc_stats,
            "vector_store": vector_stats
        }
    else:
        return {
            "total_documents": len(documents_db),
            "completed_documents": sum(1 for d in documents_db.values() if d.status == ProcessingStatus.COMPLETED),
            "processing_documents": sum(1 for d in documents_db.values() if d.status == ProcessingStatus.PROCESSING),
            "failed_documents": sum(1 for d in documents_db.values() if d.status == ProcessingStatus.FAILED),
            "vector_store": vector_stats
        }


# ============================================================================
# NEW CLAIM PROCESSING ENDPOINTS
# ============================================================================

@app.post("/api/claims/submit", response_model=ClaimDecision)
async def submit_claim(
    claim: ClaimSubmission,
    current_user: User = Depends(get_current_active_user)
):
    """
    Submit a new insurance claim for processing.
    
    This endpoint:
    1. Validates the claim submission
    2. Fetches policy details from RAG system
    3. Applies decision rules
    4. Returns decision with XAI explanation
    """
    try:
        # Process claim through decision engine
        decision = claim_engine.process_claim(claim)
        
        # Store claim in database
        claim_record = ClaimRecord(
            claim_id=decision.claim_id,
            policy_id=decision.policy_id,
            treatment_type=decision.treatment_type,
            claimed_amount=decision.claimed_amount,
            approved_amount=decision.approved_amount,
            decision=decision.decision,
            explanation=decision.explanation.reason,
            relevant_clauses=decision.explanation.relevant_clauses,
            submitted_at=decision.timestamp,
            decided_at=decision.timestamp,
            user_description=claim.description,
            hospital_name=claim.hospital_name,
            treatment_date=claim.treatment_date
        )
        
        # Store claim in database (MongoDB or in-memory)
        if claims_db_handler:
            # Use MongoDB
            claim_dict = claim_record.dict()
            claims_db_handler.insert_claim(claim_dict)
        else:
            # Fallback to in-memory
            claims_db[decision.claim_id] = claim_record.dict()
        
        return decision
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing claim: {str(e)}")


@app.get("/api/claims/{claim_id}")
async def get_claim(claim_id: str):
    """Get details of a specific claim."""
    if claims_db_handler:
        # Use MongoDB
        claim = claims_db_handler.get_claim(claim_id)
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        return claim
    else:
        # In-memory fallback
        if claim_id not in claims_db:
            raise HTTPException(status_code=404, detail="Claim not found")
        return claims_db[claim_id]


@app.get("/api/claims/{claim_id}/explanation")
async def get_claim_explanation(claim_id: str):
    """
    Get detailed XAI explanation for a claim decision.
    
    This provides:
    - Decision summary
    - Detailed reasoning
    - Policy clauses used
    - Calculation breakdown
    - Next steps
    - Audit trail
    """
    # Get claim from database
    if claims_db_handler:
        claim_record_dict = claims_db_handler.get_claim(claim_id)
        if not claim_record_dict:
            raise HTTPException(status_code=404, detail="Claim not found")
    else:
        if claim_id not in claims_db:
            raise HTTPException(status_code=404, detail="Claim not found")
        claim_record_dict = claims_db[claim_id]
    
    # Convert to ClaimRecord object
    claim_record = ClaimRecord(**claim_record_dict)
    
    # Reconstruct decision object for XAI
    from claim_models import DecisionExplanation
    decision = ClaimDecision(
        claim_id=claim_record.claim_id,
        policy_id=claim_record.policy_id,
        treatment_type=claim_record.treatment_type,
        claimed_amount=claim_record.claimed_amount,
        approved_amount=claim_record.approved_amount,
        decision=claim_record.decision,
        explanation=DecisionExplanation(
            decision=claim_record.decision,
            reason=claim_record.explanation,
            relevant_clauses=claim_record.relevant_clauses,
            calculation_details={},
            confidence_score=0.9
        ),
        timestamp=claim_record.decided_at,
        processing_time_ms=0
    )
    
    # Generate detailed explanation
    detailed_explanation = xai_explainer.generate_detailed_explanation(decision)
    
    # Add audit trail
    detailed_explanation["audit_trail"] = xai_explainer.generate_audit_trail(decision)
    
    return detailed_explanation


@app.get("/api/claims/policy/{policy_id}")
async def get_policy_claims(policy_id: str):
    """Get all claims for a specific policy."""
    if claims_db_handler:
        # Use MongoDB
        policy_claims = claims_db_handler.get_claims_by_policy(policy_id)
    else:
        # In-memory fallback
        policy_claims = [
            claim for claim in claims_db.values()
            if claim.get("policy_id") == policy_id
        ]
    
    return {
        "policy_id": policy_id,
        "total_claims": len(policy_claims),
        "claims": policy_claims
    }


@app.get("/api/policy/{policy_id}/summary")
async def get_policy_summary(policy_id: str):
    """
    Get policy summary using RAG system.
    Connects claim module with existing RAG chatbot.
    """
    try:
        summary = claim_engine.get_policy_summary(policy_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching policy summary: {str(e)}")


@app.get("/api/claims/stats")
async def get_claims_stats():
    """Get statistics about all claims."""
    if claims_db_handler:
        # Use MongoDB with aggregation
        return claims_db_handler.get_statistics()
    else:
        # In-memory fallback
        from claim_models import ClaimStatus
        
        total_claims = len(claims_db)
        approved = sum(1 for c in claims_db.values() if c.get("decision") == "approved")
        rejected = sum(1 for c in claims_db.values() if c.get("decision") == "rejected")
        under_review = sum(1 for c in claims_db.values() if c.get("decision") == "under_review")
        
        total_claimed = sum(c.get("claimed_amount", 0) for c in claims_db.values())
        total_approved = sum(c.get("approved_amount", 0) for c in claims_db.values())
        
        return {
            "total_claims": total_claims,
            "approved_claims": approved,
            "rejected_claims": rejected,
            "under_review_claims": under_review,
            "total_amount_claimed": total_claimed,
            "total_amount_approved": total_approved,
            "approval_rate": (approved / total_claims * 100) if total_claims > 0 else 0
        }


if __name__ == "__main__":
    import uvicorn
    # Use 127.0.0.1 instead of 0.0.0.0 so Windows generating clickable links works correctly
    print("Starting server... Access at http://localhost:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)
