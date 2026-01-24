from typing import List, Dict
from models import ChunkMetadata
import config
import re


class TextChunker:
    """Splits text into chunks for embedding generation."""
    
    def __init__(
        self,
        chunk_size: int = config.CHUNK_SIZE,
        chunk_overlap: int = config.CHUNK_OVERLAP,
        min_chunk_size: int = config.MIN_CHUNK_SIZE
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
    
    def chunk_document(
        self,
        text: str,
        doc_id: str,
        filename: str,
        doc_type: str,
        pages: List[Dict] = None
    ) -> List[ChunkMetadata]:
        """
        Split document text into chunks.
        
        Args:
            text: Full document text
            doc_id: Document ID
            filename: Original filename
            doc_type: Document type
            pages: List of page dictionaries with page_number and text
            
        Returns:
            List of ChunkMetadata objects
        """
        chunks = []
        
        if pages:
            # Chunk by page
            for page_info in pages:
                page_chunks = self._chunk_text(
                    page_info['text'],
                    doc_id,
                    filename,
                    doc_type,
                    page_info['page_number']
                )
                chunks.extend(page_chunks)
        else:
            # Chunk entire text
            chunks = self._chunk_text(text, doc_id, filename, doc_type)
        
        return chunks
    
    def _chunk_text(
        self,
        text: str,
        doc_id: str,
        filename: str,
        doc_type: str,
        page_number: int = None
    ) -> List[ChunkMetadata]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: Text to chunk
            doc_id: Document ID
            filename: Original filename
            doc_type: Document type
            page_number: Page number (optional)
            
        Returns:
            List of ChunkMetadata objects
        """
        # Split into sentences
        sentences = self._split_into_sentences(text)
        
        chunks = []
        current_chunk = []
        current_word_count = 0
        chunk_index = 0
        
        for sentence in sentences:
            words = sentence.split()
            word_count = len(words)
            
            # Check if adding this sentence exceeds chunk size
            if current_word_count + word_count > self.chunk_size and current_chunk:
                # Create chunk
                chunk_text = ' '.join(current_chunk)
                if len(chunk_text.split()) >= self.min_chunk_size:
                    chunks.append(ChunkMetadata(
                        chunk_id=f"{doc_id}_chunk_{chunk_index}",
                        doc_id=doc_id,
                        doc_type=doc_type,
                        filename=filename,
                        page_number=page_number,
                        chunk_index=chunk_index,
                        text=chunk_text
                    ))
                    chunk_index += 1
                
                # Start new chunk with overlap
                overlap_words = int(self.chunk_overlap)
                if overlap_words > 0 and len(current_chunk) > 0:
                    # Keep last N words for overlap
                    all_words = ' '.join(current_chunk).split()
                    overlap_text = ' '.join(all_words[-overlap_words:])
                    current_chunk = [overlap_text, sentence]
                    current_word_count = len(overlap_text.split()) + word_count
                else:
                    current_chunk = [sentence]
                    current_word_count = word_count
            else:
                current_chunk.append(sentence)
                current_word_count += word_count
        
        # Add final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            if len(chunk_text.split()) >= self.min_chunk_size:
                chunks.append(ChunkMetadata(
                    chunk_id=f"{doc_id}_chunk_{chunk_index}",
                    doc_id=doc_id,
                    doc_type=doc_type,
                    filename=filename,
                    page_number=page_number,
                    chunk_index=chunk_index,
                    text=chunk_text
                ))
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.
        
        Args:
            text: Text to split
            
        Returns:
            List of sentences
        """
        # Simple sentence splitting (can be improved with spaCy)
        # Split on period, exclamation, question mark followed by space and capital
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        
        # Clean up sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def get_chunk_context(
        self,
        chunk: ChunkMetadata,
        all_chunks: List[ChunkMetadata],
        context_size: int = 1
    ) -> str:
        """
        Get surrounding context for a chunk.
        
        Args:
            chunk: Target chunk
            all_chunks: All chunks from the document
            context_size: Number of chunks before/after to include
            
        Returns:
            Text with context
        """
        # Find chunks from same document
        doc_chunks = [c for c in all_chunks if c.doc_id == chunk.doc_id]
        doc_chunks.sort(key=lambda x: x.chunk_index)
        
        # Find target chunk index
        try:
            target_idx = next(i for i, c in enumerate(doc_chunks) if c.chunk_id == chunk.chunk_id)
        except StopIteration:
            return chunk.text
        
        # Get context chunks
        start_idx = max(0, target_idx - context_size)
        end_idx = min(len(doc_chunks), target_idx + context_size + 1)
        
        context_chunks = doc_chunks[start_idx:end_idx]
        context_text = ' '.join([c.text for c in context_chunks])
        
        return context_text
