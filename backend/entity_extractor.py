import re
import spacy
from typing import Dict, List, Tuple
from models import ExtractedEntity
import config


class EntityExtractor:
    """Extracts structured information from insurance documents using NLP."""
    
    def __init__(self):
        # Load spaCy model (using base model, can be fine-tuned)
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except:
            print("Downloading spaCy model...")
            import os
            os.system("python -m spacy download en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")
        
        # Add custom entity ruler for insurance-specific patterns
        if "entity_ruler" not in self.nlp.pipe_names:
            ruler = self.nlp.add_pipe("entity_ruler", before="ner")
            patterns = self._create_entity_patterns()
            ruler.add_patterns(patterns)
    
    def extract_entities(self, text: str) -> List[ExtractedEntity]:
        """
        Extract all entities from text.
        
        Args:
            text: Cleaned text
            
        Returns:
            List of extracted entities
        """
        entities = []
        
        # Extract using regex patterns
        entities.extend(self._extract_with_regex(text))
        
        # Extract using spaCy NER
        entities.extend(self._extract_with_spacy(text))
        
        # Deduplicate entities
        entities = self._deduplicate_entities(entities)
        
        return entities
    
    def _extract_with_regex(self, text: str) -> List[ExtractedEntity]:
        """Extract entities using regex patterns."""
        entities = []
        
        # Policy Number
        policy_match = re.search(config.ENTITY_PATTERNS["policy_number"], text, re.IGNORECASE)
        if policy_match:
            entities.append(ExtractedEntity(
                entity_type="POLICY_NUMBER",
                value=policy_match.group(1).strip(),
                confidence=0.9
            ))
        
        # Claim Amount
        claim_match = re.search(config.ENTITY_PATTERNS["claim_amount"], text, re.IGNORECASE)
        if claim_match:
            amount = claim_match.group(1).replace(',', '')
            entities.append(ExtractedEntity(
                entity_type="CLAIM_AMOUNT",
                value=f"₹{amount}",
                confidence=0.85
            ))
        
        # Hospital Name
        hospital_match = re.search(config.ENTITY_PATTERNS["hospital_name"], text, re.IGNORECASE)
        if hospital_match:
            entities.append(ExtractedEntity(
                entity_type="HOSPITAL_NAME",
                value=hospital_match.group(1).strip(),
                confidence=0.8
            ))
        
        # Dates
        date_matches = re.finditer(config.ENTITY_PATTERNS["date"], text)
        for match in date_matches:
            entities.append(ExtractedEntity(
                entity_type="DATE",
                value=match.group(1),
                confidence=0.75
            ))
        
        # Coverage Amount
        coverage_pattern = r"(?:Coverage|Sum\s+Assured|Insured\s+Amount)\s*:?\s*₹?\s*([\d,]+(?:\.\d{2})?)"
        coverage_match = re.search(coverage_pattern, text, re.IGNORECASE)
        if coverage_match:
            amount = coverage_match.group(1).replace(',', '')
            entities.append(ExtractedEntity(
                entity_type="COVERAGE_AMOUNT",
                value=f"₹{amount}",
                confidence=0.85
            ))
        
        # Diagnosis
        diagnosis_pattern = r"(?:Diagnosis|Disease|Condition|Ailment)\s*:?\s*([A-Z][a-zA-Z\s,]+(?:\n|$))"
        diagnosis_match = re.search(diagnosis_pattern, text, re.IGNORECASE)
        if diagnosis_match:
            entities.append(ExtractedEntity(
                entity_type="DIAGNOSIS",
                value=diagnosis_match.group(1).strip(),
                confidence=0.7
            ))
        
        return entities
    
    def _extract_with_spacy(self, text: str) -> List[ExtractedEntity]:
        """Extract entities using spaCy NER."""
        entities = []
        doc = self.nlp(text[:1000000])  # Limit text length for processing
        
        for ent in doc.ents:
            # Map spaCy entities to our custom types
            entity_type = self._map_spacy_entity(ent.label_)
            if entity_type:
                entities.append(ExtractedEntity(
                    entity_type=entity_type,
                    value=ent.text.strip(),
                    confidence=0.7
                ))
        
        return entities
    
    def _map_spacy_entity(self, spacy_label: str) -> str:
        """Map spaCy entity labels to our custom labels."""
        mapping = {
            "PERSON": "POLICY_HOLDER",
            "ORG": "HOSPITAL_NAME",
            "DATE": "DATE",
            "MONEY": "CLAIM_AMOUNT",
            "GPE": "LOCATION",
        }
        return mapping.get(spacy_label, None)
    
    def _create_entity_patterns(self) -> List[Dict]:
        """Create patterns for entity ruler."""
        patterns = [
            # Policy numbers
            {"label": "POLICY_NUMBER", "pattern": [
                {"TEXT": {"REGEX": r"Policy"}},
                {"IS_PUNCT": True, "OP": "?"},
                {"TEXT": {"REGEX": r"[A-Z0-9\-/]+"}}
            ]},
            # Currency amounts
            {"label": "CLAIM_AMOUNT", "pattern": [
                {"TEXT": "₹"},
                {"TEXT": {"REGEX": r"\d+(?:,\d+)*(?:\.\d{2})?"}}
            ]},
        ]
        return patterns
    
    def _deduplicate_entities(self, entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
        """Remove duplicate entities, keeping highest confidence."""
        seen = {}
        
        for entity in entities:
            key = (entity.entity_type, entity.value.lower())
            if key not in seen or (entity.confidence or 0) > (seen[key].confidence or 0):
                seen[key] = entity
        
        return list(seen.values())
    
    def extract_key_fields(self, text: str) -> Dict[str, str]:
        """
        Extract key fields and return as structured dictionary.
        
        Args:
            text: Cleaned text
            
        Returns:
            Dictionary of key fields
        """
        entities = self.extract_entities(text)
        
        # Organize entities by type
        fields = {}
        for entity in entities:
            if entity.entity_type not in fields:
                fields[entity.entity_type] = []
            fields[entity.entity_type].append(entity.value)
        
        # Take first value for each type (or combine if needed)
        key_fields = {}
        for entity_type, values in fields.items():
            if entity_type == "DATE":
                key_fields[entity_type] = values  # Keep all dates
            else:
                key_fields[entity_type] = values[0] if values else None
        
        return key_fields
    
    def generate_summary(self, text: str, max_length: int = 200) -> str:
        """
        Generate a brief summary of the document.
        
        Args:
            text: Full document text
            max_length: Maximum summary length in words
            
        Returns:
            Summary text
        """
        # Simple extractive summary: take first few sentences
        doc = self.nlp(text[:5000])  # Process first 5000 chars
        
        sentences = [sent.text.strip() for sent in doc.sents]
        
        summary = ""
        word_count = 0
        
        for sentence in sentences:
            words = sentence.split()
            if word_count + len(words) <= max_length:
                summary += sentence + " "
                word_count += len(words)
            else:
                break
        
        return summary.strip()
