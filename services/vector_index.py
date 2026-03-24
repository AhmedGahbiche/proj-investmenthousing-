"""
Vector index management service for FAISS.
Handles creation, storage, and management of vector embeddings.
"""
import logging
import os
import pickle
from pathlib import Path
from typing import Tuple, List
import numpy as np
import faiss
from config import settings

logger = logging.getLogger(__name__)


class VectorIndexManager:
    """Manages FAISS vector index for semantic search."""
    
    def __init__(self, index_dir: str = "./vector_indices"):
        """
        Initialize vector index manager.
        
        Args:
            index_dir: Directory to store FAISS indices
        """
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        # Dimension of embeddings (all-MiniLM-L6-v2 produces 384-dimensional vectors)
        self.embedding_dim = 384
        
        # Store indices in memory: {document_id: (faiss_index, id_to_chunk_map)}
        self.indices = {}
        
        logger.info(f"Vector index manager initialized with directory: {self.index_dir}")
    
    def create_index(self, document_id: int) -> faiss.IndexFlatL2:
        """
        Create a new FAISS index for a document.
        
        Args:
            document_id: ID of the document
            
        Returns:
            FAISS index object
        """
        try:
            # Create flat L2 index (Euclidean distance)
            index = faiss.IndexFlatL2(self.embedding_dim)
            
            # Store empty id mapping
            self.indices[document_id] = {
                'index': index,
                'chunk_ids': [],  # Maps index position to chunk_id
                'texts': []       # Maps index position to original text
            }
            
            logger.info(f"Created FAISS index for document {document_id}")
            return index
            
        except Exception as e:
            logger.error(f"Failed to create index for document {document_id}: {str(e)}")
            raise
    
    def add_vectors(
        self,
        document_id: int,
        embeddings: np.ndarray,
        chunk_ids: List[str],
        chunk_texts: List[str]
    ) -> bool:
        """
        Add embedding vectors to a document's index.
        
        Args:
            document_id: ID of the document
            embeddings: Array of shape (N, 384) with N embedding vectors
            chunk_ids: List of chunk IDs (must match embeddings length)
            chunk_texts: List of original texts (must match embeddings length)
            
        Returns:
            True if successful
        """
        try:
            if document_id not in self.indices:
                self.create_index(document_id)
            
            # Ensure embeddings are float32 (FAISS requirement)
            embeddings = np.array(embeddings, dtype=np.float32)
            
            # Normalize embeddings for better L2 distance
            faiss.normalize_L2(embeddings)
            
            # Add to index
            index = self.indices[document_id]['index']
            index.add(embeddings)
            
            # Track chunk IDs and texts
            self.indices[document_id]['chunk_ids'].extend(chunk_ids)
            self.indices[document_id]['texts'].extend(chunk_texts)
            
            logger.info(
                f"Added {len(embeddings)} vectors to document {document_id} index"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to add vectors for document {document_id}: {str(e)}")
            raise
    
    def search(
        self,
        document_id: int,
        query_embedding: np.ndarray,
        k: int = 5
    ) -> Tuple[List[str], List[float]]:
        """
        Search for similar chunks in a document.
        
        Args:
            document_id: ID of the document to search
            query_embedding: Query embedding vector (384-dimensional)
            k: Number of results to return
            
        Returns:
            Tuple of (chunk_ids, distances)
        """
        try:
            if document_id not in self.indices:
                logger.warning(f"No index found for document {document_id}")
                return [], []
            
            index = self.indices[document_id]['index']
            
            if index.ntotal == 0:
                logger.warning(f"Index for document {document_id} is empty")
                return [], []
            
            # Ensure query is float32
            query_embedding = np.array([query_embedding], dtype=np.float32)
            faiss.normalize_L2(query_embedding)
            
            # Search
            distances, indices = index.search(query_embedding, min(k, index.ntotal))
            
            # Get chunk info
            chunk_ids = self.indices[document_id]['chunk_ids']
            distances = distances[0].tolist()
            indices = indices[0]
            
            results = []
            result_distances = []
            
            for idx, distance in zip(indices, distances):
                if 0 <= idx < len(chunk_ids):
                    results.append(chunk_ids[idx])
                    result_distances.append(float(distance))
            
            logger.info(
                f"Search in document {document_id}: found {len(results)} results"
            )
            return results, result_distances
            
        except Exception as e:
            logger.error(f"Search failed for document {document_id}: {str(e)}")
            return [], []
    
    def search_across_documents(
        self,
        query_embedding: np.ndarray,
        k: int = 5,
        document_ids: List[int] = None
    ) -> List[Tuple[int, str, float]]:
        """
        Search across documents (optionally filtered by document_ids).
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return total
            document_ids: Optional list of document IDs to search (None = all)
            
        Returns:
            List of (document_id, chunk_id, distance) tuples, sorted by distance
        """
        try:
            all_results = []
            
            # Determine which documents to search
            docs_to_search = document_ids if document_ids else list(self.indices.keys())
            
            for doc_id in docs_to_search:
                if doc_id not in self.indices:
                    logger.warning(f"Document {doc_id} not found in indices")
                    continue
                
                chunk_ids, distances = self.search(doc_id, query_embedding, k=10)  # Get more per doc
                
                for chunk_id, distance in zip(chunk_ids, distances):
                    all_results.append((doc_id, chunk_id, distance))
            
            # Sort by distance (lower is better) and return top k
            all_results.sort(key=lambda x: x[2])
            
            return all_results[:k]
            
        except Exception as e:
            logger.error(f"Cross-document search failed: {str(e)}")
            return []
    
    def save_index(self, document_id: int) -> bool:
        """
        Save FAISS index to disk for persistence.
        
        Args:
            document_id: ID of the document
            
        Returns:
            True if successful
        """
        try:
            if document_id not in self.indices:
                logger.warning(f"Index not found for document {document_id}")
                return False
            
            index_file = self.index_dir / f"document_{document_id}.index"
            metadata_file = self.index_dir / f"document_{document_id}.pkl"
            
            doc_data = self.indices[document_id]
            
            # Save FAISS index
            faiss.write_index(doc_data['index'], str(index_file))
            
            # Save metadata (chunk IDs and texts)
            metadata = {
                'chunk_ids': doc_data['chunk_ids'],
                'texts': doc_data['texts']
            }
            with open(metadata_file, 'wb') as f:
                pickle.dump(metadata, f)
            
            logger.info(f"Saved FAISS index for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save index for document {document_id}: {str(e)}")
            return False
    
    def load_index(self, document_id: int) -> bool:
        """
        Load FAISS index from disk.
        
        Args:
            document_id: ID of the document
            
        Returns:
            True if successful, False if not found
        """
        try:
            index_file = self.index_dir / f"document_{document_id}.index"
            metadata_file = self.index_dir / f"document_{document_id}.pkl"
            
            if not index_file.exists() or not metadata_file.exists():
                logger.warning(f"Index files not found for document {document_id}")
                return False
            
            # Load FAISS index
            index = faiss.read_index(str(index_file))
            
            # Load metadata
            with open(metadata_file, 'rb') as f:
                metadata = pickle.load(f)
            
            self.indices[document_id] = {
                'index': index,
                'chunk_ids': metadata['chunk_ids'],
                'texts': metadata['texts']
            }
            
            logger.info(f"Loaded FAISS index for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load index for document {document_id}: {str(e)}")
            return False
    
    def delete_index(self, document_id: int) -> bool:
        """
        Delete FAISS index for a document.
        
        Args:
            document_id: ID of the document
            
        Returns:
            True if successful
        """
        try:
            # Remove from memory
            if document_id in self.indices:
                del self.indices[document_id]
            
            # Remove from disk
            index_file = self.index_dir / f"document_{document_id}.index"
            metadata_file = self.index_dir / f"document_{document_id}.pkl"
            
            for file_path in [index_file, metadata_file]:
                if file_path.exists():
                    file_path.unlink()
            
            logger.info(f"Deleted FAISS index for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete index for document {document_id}: {str(e)}")
            return False
    
    def get_index_stats(self, document_id: int) -> dict:
        """
        Get statistics about a document's index.
        
        Args:
            document_id: ID of the document
            
        Returns:
            Dictionary with index statistics
        """
        if document_id not in self.indices:
            return {'exists': False}
        
        index = self.indices[document_id]['index']
        return {
            'exists': True,
            'num_vectors': index.ntotal,
            'embedding_dim': self.embedding_dim,
            'num_chunks': len(self.indices[document_id]['chunk_ids'])
        }


# Global vector index manager instance
vector_index_manager = VectorIndexManager()
