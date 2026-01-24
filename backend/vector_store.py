import faiss
import numpy as np
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from models import ChunkMetadata
import config


class VectorStore:
    """FAISS-based vector database for storing and retrieving document embeddings."""
    
    def __init__(
        self,
        embedding_dim: int = config.EMBEDDING_DIM,
        index_path: Path = config.FAISS_INDEX_PATH,
        metadata_path: Path = config.METADATA_PATH
    ):
        """
        Initialize the vector store.
        
        Args:
            embedding_dim: Dimension of embeddings
            index_path: Path to save/load FAISS index
            metadata_path: Path to save/load metadata
        """
        self.embedding_dim = embedding_dim
        self.index_path = index_path
        self.metadata_path = metadata_path
        
        # Initialize or load FAISS index
        if index_path.exists():
            self.index = faiss.read_index(str(index_path))
            print(f"Loaded existing FAISS index with {self.index.ntotal} vectors")
        else:
            # Create new index (using L2 distance)
            self.index = faiss.IndexFlatL2(embedding_dim)
            print(f"Created new FAISS index with dimension {embedding_dim}")
        
        # Load or initialize metadata
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
            print(f"Loaded metadata for {len(self.metadata)} chunks")
        else:
            self.metadata = []
    
    def add_embeddings(
        self,
        embeddings: np.ndarray,
        chunks: List[ChunkMetadata]
    ):
        """
        Add embeddings and their metadata to the vector store.
        
        Args:
            embeddings: Array of embeddings (shape: [num_chunks, embedding_dim])
            chunks: List of ChunkMetadata objects
        """
        if len(embeddings) != len(chunks):
            raise ValueError("Number of embeddings must match number of chunks")
        
        # Ensure embeddings are float32
        embeddings = embeddings.astype('float32')
        
        # Add to FAISS index
        self.index.add(embeddings)
        
        # Add metadata
        for chunk in chunks:
            self.metadata.append({
                'chunk_id': chunk.chunk_id,
                'doc_id': chunk.doc_id,
                'doc_type': chunk.doc_type,
                'filename': chunk.filename,
                'page_number': chunk.page_number,
                'chunk_index': chunk.chunk_index,
                'text': chunk.text
            })
        
        print(f"Added {len(chunks)} chunks to vector store. Total: {self.index.ntotal}")
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = config.TOP_K_RESULTS,
        doc_ids: Optional[List[str]] = None
    ) -> List[Tuple[Dict, float]]:
        """
        Search for similar chunks.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            doc_ids: Optional list of document IDs to filter by
            
        Returns:
            List of (metadata, similarity_score) tuples
        """
        if self.index.ntotal == 0:
            return []
        
        # Ensure query is 2D and float32
        query_embedding = query_embedding.astype('float32').reshape(1, -1)
        
        # Search in FAISS
        # Get more results if filtering by doc_ids
        search_k = top_k * 10 if doc_ids else top_k
        distances, indices = self.index.search(query_embedding, min(search_k, self.index.ntotal))
        
        # Retrieve metadata and convert distances to similarity scores
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.metadata):
                metadata = self.metadata[idx]
                
                # Filter by doc_ids if specified
                if doc_ids and metadata['doc_id'] not in doc_ids:
                    continue
                
                # Convert L2 distance to similarity score (inverse)
                # Lower distance = higher similarity
                similarity = 1 / (1 + dist)
                
                results.append((metadata, float(similarity)))
                
                if len(results) >= top_k:
                    break
        
        return results
    
    def get_chunks_by_doc_id(self, doc_id: str) -> List[Dict]:
        """
        Get all chunks for a specific document.
        
        Args:
            doc_id: Document ID
            
        Returns:
            List of chunk metadata
        """
        return [m for m in self.metadata if m['doc_id'] == doc_id]
    
    def delete_document(self, doc_id: str):
        """
        Delete all chunks for a document.
        Note: FAISS doesn't support deletion, so we rebuild the index.
        
        Args:
            doc_id: Document ID to delete
        """
        # Get indices to keep
        indices_to_keep = [i for i, m in enumerate(self.metadata) if m['doc_id'] != doc_id]
        
        if len(indices_to_keep) == len(self.metadata):
            print(f"No chunks found for doc_id: {doc_id}")
            return
        
        # Rebuild index with remaining vectors
        if indices_to_keep:
            # Get embeddings for chunks to keep
            old_vectors = np.array([self.index.reconstruct(i) for i in indices_to_keep])
            
            # Create new index
            self.index = faiss.IndexFlatL2(self.embedding_dim)
            self.index.add(old_vectors.astype('float32'))
            
            # Update metadata
            self.metadata = [self.metadata[i] for i in indices_to_keep]
        else:
            # No chunks left, create empty index
            self.index = faiss.IndexFlatL2(self.embedding_dim)
            self.metadata = []
        
        print(f"Deleted chunks for doc_id: {doc_id}. Remaining: {self.index.ntotal}")
    
    def save(self):
        """Save the index and metadata to disk."""
        # Save FAISS index
        faiss.write_index(self.index, str(self.index_path))
        
        # Save metadata
        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        
        print(f"Saved vector store with {self.index.ntotal} vectors")
    
    def get_stats(self) -> Dict:
        """Get statistics about the vector store."""
        doc_ids = set(m['doc_id'] for m in self.metadata)
        
        return {
            'total_chunks': self.index.ntotal,
            'total_documents': len(doc_ids),
            'embedding_dim': self.embedding_dim,
            'index_size_mb': self.index_path.stat().st_size / (1024 * 1024) if self.index_path.exists() else 0
        }
