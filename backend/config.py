import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
PROCESSED_DIR = DATA_DIR / "processed"
VECTOR_DB_DIR = DATA_DIR / "vector_db"

# Create directories if they don't exist
for directory in [UPLOAD_DIR, PROCESSED_DIR, VECTOR_DB_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# OCR settings
TESSERACT_CMD = os.getenv("TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
OCR_LANG = "eng"

# MongoDB settings
MONGODB_URI = os.getenv("MONGODB_URI", "")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "insurance_claims")
USE_MONGODB = bool(MONGODB_URI)


# Text processing settings
CHUNK_SIZE = 250  # words
CHUNK_OVERLAP = 50  # words
MIN_CHUNK_SIZE = 100  # words

# Embedding settings
EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"
EMBEDDING_DIM = 768

# Vector database settings
FAISS_INDEX_PATH = VECTOR_DB_DIR / "faiss_index.bin"
METADATA_PATH = VECTOR_DB_DIR / "metadata.json"
TOP_K_RESULTS = 5

# LLM settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
USE_OPENAI = bool(OPENAI_API_KEY)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")
LLM_TEMPERATURE = 0.1
LLM_MAX_TOKENS = 500

# Document types
SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".txt"}

# Entity extraction patterns
ENTITY_PATTERNS = {
    "policy_number": r"Policy\s*(?:No|Number|#)?\s*:?\s*([A-Z0-9\-/]+)",
    "claim_amount": r"(?:Claim\s*Amount|Amount\s*Claimed)\s*:?\s*₹?\s*([\d,]+(?:\.\d{2})?)",
    "date": r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
    "hospital_name": r"Hospital\s*(?:Name)?\s*:?\s*([A-Z][a-zA-Z\s&]+(?:Hospital|Medical|Clinic|Centre))",
}

# NER labels for spaCy
NER_LABELS = [
    "POLICY_NUMBER",
    "CLAIM_AMOUNT",
    "COVERAGE_AMOUNT",
    "HOSPITAL_NAME",
    "DIAGNOSIS",
    "DOCTOR_NAME",
    "POLICY_HOLDER",
    "ACCIDENT_DATE",
    "CLAIM_DATE",
]
