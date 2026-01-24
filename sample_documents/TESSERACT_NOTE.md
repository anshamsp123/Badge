# ⚠️ Tesseract OCR Not Installed

## Issue
The sample PDF documents are failing to process because **Tesseract OCR is not installed** on your system.

## Solutions

### **Option 1: Install Tesseract (Recommended for Full Features)**

#### Windows:
1. Download Tesseract installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer (tesseract-ocr-w64-setup-5.x.x.exe)
3. Install to default location: `C:\Program Files\Tesseract-OCR\`
4. Restart the server

#### Mac:
```bash
brew install tesseract
```

#### Linux:
```bash
sudo apt-get install tesseract-ocr
```

### **Option 2: Use Text Files Instead (Quick Demo)**

I've updated the system to work without Tesseract for PDFs with digital text. However, the ReportLab-generated PDFs might have issues.

Let me create simple text files you can upload instead:

**Files created in:** `sample_documents/text_samples/`

1. `policy.txt` - Health Insurance Policy
2. `claim.txt` - Claim Form  
3. `bill.txt` - Hospital Bill
4. `discharge.txt` - Discharge Summary

These are plain text files that will work perfectly without Tesseract!

---

## Current Status

✅ **System Updated** - Now handles missing Tesseract gracefully
✅ **Digital PDFs** - Will work if they have extractable text
⚠️ **Scanned PDFs/Images** - Require Tesseract installation

---

## Quick Fix for Demo

Use the text files I'm creating now - they'll work immediately without any installation!
