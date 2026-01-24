import pytesseract
from PIL import Image
from pdf2image import convert_from_path
import PyPDF2
from pathlib import Path
from typing import List, Dict, Tuple
import re
import config


class OCRProcessor:
    """Handles OCR and text extraction from PDFs and images."""
    
    def __init__(self):
        # Set Tesseract path (optional - only needed for scanned documents)
        try:
            pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD
            # Test if tesseract is available
            pytesseract.get_tesseract_version()
            self.tesseract_available = True
            print("Tesseract OCR is available")
        except Exception as e:
            self.tesseract_available = False
            print(f"Warning: Tesseract OCR not available. Will only process digital PDFs. Error: {e}")
    
    def extract_text(self, file_path: Path) -> Dict[str, any]:
        """
        Extract text from a document (PDF or image).
        
        Returns:
            Dict with 'text', 'pages', and 'metadata'
        """
        file_ext = file_path.suffix.lower()
        
        if file_ext == '.txt':
            return self._extract_from_text(file_path)
        elif file_ext == '.pdf':
            return self._extract_from_pdf(file_path)
        elif file_ext in {'.png', '.jpg', '.jpeg', '.tiff', '.bmp'}:
            return self._extract_from_image(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
    
    def _extract_from_text(self, text_path: Path) -> Dict[str, any]:
        """Extract text from plain text file."""
        result = {
            'text': '',
            'pages': [],
            'metadata': {
                'page_count': 1,
                'method': 'text'
            }
        }
        
        try:
            with open(text_path, 'r', encoding='utf-8') as file:
                text = file.read()
                result['text'] = text
                result['pages'].append({
                    'page_number': 1,
                    'text': text
                })
        except Exception as e:
            raise Exception(f"Text file reading failed: {e}")
        
        return result
    
    def _extract_from_pdf(self, pdf_path: Path) -> Dict[str, any]:
        """Extract text from PDF using PyPDF2 first, then OCR if needed."""
        result = {
            'text': '',
            'pages': [],
            'metadata': {
                'page_count': 0,
                'method': 'digital'
            }
        }
        
        try:
            # Try digital text extraction first
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                result['metadata']['page_count'] = len(pdf_reader.pages)
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    page_text = page.extract_text()
                    result['pages'].append({
                        'page_number': page_num,
                        'text': page_text
                    })
                    result['text'] += f"\n--- Page {page_num} ---\n{page_text}"
            
            # If very little text extracted, use OCR (if available)
            if len(result['text'].strip()) < 100:
                if self.tesseract_available:
                    print(f"Low text extraction, using OCR for {pdf_path.name}")
                    return self._ocr_pdf(pdf_path)
                else:
                    print(f"Warning: Low text extraction for {pdf_path.name}, but Tesseract not available")
            
        except Exception as e:
            if self.tesseract_available:
                print(f"Digital extraction failed, using OCR: {e}")
                return self._ocr_pdf(pdf_path)
            else:
                print(f"Digital extraction failed and Tesseract not available: {e}")
                raise Exception(f"Cannot process PDF: {e}")
        
        return result
    
    def _ocr_pdf(self, pdf_path: Path) -> Dict[str, any]:
        """Perform OCR on PDF by converting to images."""
        if not self.tesseract_available:
            raise Exception("Tesseract OCR is not available. Please install Tesseract or use PDFs with digital text.")
        
        result = {
            'text': '',
            'pages': [],
            'metadata': {
                'page_count': 0,
                'method': 'ocr'
            }
        }
        
        try:
            # Convert PDF to images
            images = convert_from_path(str(pdf_path), dpi=300)
            result['metadata']['page_count'] = len(images)
            
            for page_num, image in enumerate(images, 1):
                # Perform OCR
                page_text = pytesseract.image_to_string(
                    image,
                    lang=config.OCR_LANG,
                    config='--psm 1'  # Automatic page segmentation with OSD
                )
                
                result['pages'].append({
                    'page_number': page_num,
                    'text': page_text
                })
                result['text'] += f"\n--- Page {page_num} ---\n{page_text}"
        
        except Exception as e:
            raise Exception(f"OCR processing failed: {e}")
        
        return result
    
    def _extract_from_image(self, image_path: Path) -> Dict[str, any]:
        """Extract text from image using OCR."""
        if not self.tesseract_available:
            raise Exception("Tesseract OCR is not available. Please install Tesseract to process images.")
        
        result = {
            'text': '',
            'pages': [],
            'metadata': {
                'page_count': 1,
                'method': 'ocr'
            }
        }
        
        try:
            image = Image.open(image_path)
            
            # Perform OCR
            text = pytesseract.image_to_string(
                image,
                lang=config.OCR_LANG,
                config='--psm 1'
            )
            
            result['text'] = text
            result['pages'].append({
                'page_number': 1,
                'text': text
            })
        
        except Exception as e:
            raise Exception(f"Image OCR failed: {e}")
        
        return result
    
    def extract_tables(self, file_path: Path) -> List[List[str]]:
        """
        Extract tables from documents (basic implementation).
        For production, consider using libraries like camelot-py or tabula-py.
        """
        # This is a placeholder for table extraction
        # In production, you'd use specialized libraries
        return []
