import re
from datetime import datetime
from typing import Dict, List
from dateutil import parser


class TextCleaner:
    """Cleans and normalizes extracted text."""
    
    def __init__(self):
        self.date_formats = [
            "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y",
            "%d/%m/%y", "%d-%m-%y",
            "%Y-%m-%d", "%Y/%m/%d",
            "%d %B %Y", "%d %b %Y",
            "%B %d, %Y", "%b %d, %Y"
        ]
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep important punctuation
        text = re.sub(r'[^\w\s\.,;:!?\-₹$/()\[\]@#%&*+=]', '', text)
        
        # Fix common OCR errors
        text = self._fix_ocr_errors(text)
        
        # Normalize whitespace around punctuation
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)
        text = re.sub(r'([.,;:!?])(\w)', r'\1 \2', text)
        
        # Remove multiple consecutive punctuation
        text = re.sub(r'([.,;:!?]){2,}', r'\1', text)
        
        return text.strip()
    
    def normalize_dates(self, text: str) -> str:
        """
        Normalize dates to DD/MM/YYYY format.
        
        Args:
            text: Text containing dates
            
        Returns:
            Text with normalized dates
        """
        # Find potential dates
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            r'\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}\b',
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{2,4}\b',
        ]
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                date_str = match.group()
                normalized = self._normalize_single_date(date_str)
                if normalized:
                    text = text.replace(date_str, normalized)
        
        return text
    
    def _normalize_single_date(self, date_str: str) -> str:
        """Normalize a single date string to DD/MM/YYYY."""
        try:
            # Try parsing with dateutil
            dt = parser.parse(date_str, dayfirst=True)
            return dt.strftime("%d/%m/%Y")
        except:
            # Try manual formats
            for fmt in self.date_formats:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime("%d/%m/%Y")
                except:
                    continue
        return date_str  # Return original if parsing fails
    
    def normalize_currency(self, text: str) -> str:
        """
        Normalize currency amounts to ₹ format.
        
        Args:
            text: Text containing currency amounts
            
        Returns:
            Text with normalized currency
        """
        # Patterns for currency
        patterns = [
            (r'Rs\.?\s*(\d+(?:,\d+)*(?:\.\d{2})?)', r'₹\1'),
            (r'INR\s*(\d+(?:,\d+)*(?:\.\d{2})?)', r'₹\1'),
            (r'Rupees\s*(\d+(?:,\d+)*(?:\.\d{2})?)', r'₹\1'),
        ]
        
        for pattern, replacement in patterns:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        # Ensure proper comma formatting for Indian numbering
        def format_indian_number(match):
            num_str = match.group(1).replace(',', '')
            try:
                num = float(num_str)
                # Format with Indian numbering system
                s = f"{num:,.2f}"
                return f"₹{s}"
            except:
                return match.group(0)
        
        text = re.sub(r'₹(\d+(?:\.\d{2})?)', format_indian_number, text)
        
        return text
    
    def normalize_names(self, text: str) -> str:
        """
        Normalize person and place names (title case).
        
        Args:
            text: Text containing names
            
        Returns:
            Text with normalized names
        """
        # This is a simplified version
        # In production, you'd use NER to identify names first
        
        # Capitalize after common titles
        titles = ['Mr', 'Mrs', 'Ms', 'Dr', 'Prof']
        for title in titles:
            pattern = rf'\b({title})\.?\s+([a-z]+)'
            text = re.sub(pattern, lambda m: f"{m.group(1)}. {m.group(2).title()}", text, flags=re.IGNORECASE)
        
        return text
    
    def normalize_policy_numbers(self, text: str) -> str:
        """
        Normalize policy numbers to standard format.
        
        Args:
            text: Text containing policy numbers
            
        Returns:
            Text with normalized policy numbers
        """
        # Remove spaces in policy numbers
        pattern = r'Policy\s*(?:No|Number|#)?\s*:?\s*([A-Z0-9\s\-/]+)'
        
        def normalize_policy(match):
            policy_num = match.group(1).replace(' ', '').upper()
            return f"Policy Number: {policy_num}"
        
        text = re.sub(pattern, normalize_policy, text, flags=re.IGNORECASE)
        
        return text
    
    def _fix_ocr_errors(self, text: str) -> str:
        """Fix common OCR errors."""
        # Common OCR mistakes
        replacements = {
            r'\b0(?=\D)': 'O',  # 0 to O in words
            r'(?<=\D)0(?=\D)': 'O',
            r'\bl(?=\d)': '1',  # l to 1 in numbers
            r'(?<=\d)l(?=\d)': '1',
            r'\bS(?=\d)': '5',  # S to 5 in numbers
        }
        
        for pattern, replacement in replacements.items():
            text = re.sub(pattern, replacement, text)
        
        return text
    
    def clean_full_document(self, text: str) -> str:
        """
        Apply all cleaning and normalization steps.
        
        Args:
            text: Raw text
            
        Returns:
            Fully cleaned and normalized text
        """
        text = self.clean_text(text)
        text = self.normalize_dates(text)
        text = self.normalize_currency(text)
        text = self.normalize_names(text)
        text = self.normalize_policy_numbers(text)
        
        return text
