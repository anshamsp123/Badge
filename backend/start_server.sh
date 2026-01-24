#!/bin/bash

echo "========================================"
echo "Insurance Claims Processing System"
echo "========================================"
echo ""

echo "[1/4] Checking Python..."
python3 --version
if [ $? -ne 0 ]; then
    echo "ERROR: Python not found!"
    exit 1
fi
echo ""

echo "[2/4] Installing/Updating dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install fastapi==0.104.1 uvicorn[standard]==0.24.0 python-multipart==0.0.6
python3 -m pip install pytesseract==0.3.10 pdf2image==1.16.3 PyPDF2==3.0.1 Pillow==10.1.0
python3 -m pip install spacy==3.7.2 sentence-transformers==2.2.2
python3 -m pip install faiss-cpu==1.7.4 numpy==1.24.3
python3 -m pip install python-dotenv==1.0.0 pydantic==2.5.0
python3 -m pip install openai requests python-dateutil
echo ""

echo "[3/4] Downloading spaCy model..."
python3 -m spacy download en_core_web_sm
echo ""

echo "[4/4] Starting server..."
echo ""
echo "========================================"
echo "Server will start at: http://localhost:8000"
echo "Press Ctrl+C to stop the server"
echo "========================================"
echo ""

python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
