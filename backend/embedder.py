from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Union
import config


class Embedder:
    """Generates embeddings for text chunks using Sentence Transformers."""
    
    def __init__(self, model_name: str = config.EMBEDDING_MODEL):
        """
        Initialize the embedder.
        
        Args:
            model_name: Name of the sentence transformer model
        """
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = config.EMBEDDING_DIM
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as numpy array
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
            
        Returns:
            Array of embeddings (shape: [num_texts, embedding_dim])
        """
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            show_progress_bar=True
        )
        return embeddings
    
    def get_embedding_dim(self) -> int:
        """Get the dimensionality of embeddings."""
        return self.embedding_dim
