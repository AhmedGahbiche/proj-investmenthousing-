"""
Vector embedding service for generating and managing text embeddings.
Handles text chunking and embedding generation using sentence-transformers.
"""
import logging
from threading import Lock
from typing import List, Tuple
from typing import Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from services.vector_index import vector_index_manager

logger = logging.getLogger(__name__)


_vector_service_instance: Optional["VectorService"] = None
_vector_service_lock = Lock()


class VectorService:
    """Service for generating embeddings and managing semantic search."""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize vector service with embedding model.
        
        Args:
            model_name: Name of sentence-transformers model
        """
        self.model_name = model_name
        self.embedding_dim = 384  # all-MiniLM-L6-v2 produces 384-dim vectors
        self.vector_index = vector_index_manager  # Expose index manager for direct access
        self.model: Optional[SentenceTransformer] = None
        logger.info("Vector service initialized. Embedding model will be lazy-loaded on first use")

    def _get_model(self) -> SentenceTransformer:
        """Load and cache the embedding model on first use."""
        if self.model is None:
            try:
                logger.info(f"Loading embedding model: {self.model_name}")
                self.model = SentenceTransformer(self.model_name)
                logger.info("Embedding model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {str(e)}")
                raise
        return self.model
    
    def chunk_text(
        self,
        text: str,
        chunk_size: int = 512,
        overlap: int = 50
    ) -> List[Tuple[str, str]]:
        """
        Split text into overlapping chunks for embedding.
        
        Args:
            text: Text to chunk
            chunk_size: Number of characters per chunk
            overlap: Number of characters to overlap between chunks
            
        Returns:
            List of (chunk_id, chunk_text) tuples
        """
        if not text or not text.strip():
            return []
        
        chunks = []
        start = 0
        chunk_num = 0
        
        while start < len(text):
            # Extract chunk
            end = min(start + chunk_size, len(text))
            chunk_text = text[start:end].strip()
            
            if chunk_text:  # Only include non-empty chunks
                chunk_id = f"chunk_{chunk_num:04d}"
                chunks.append((chunk_id, chunk_text))
                chunk_num += 1
            
            # Move start position (with overlap)
            start = end - overlap
            
            # Prevent infinite loop on very short overlaps
            if end == len(text):
                break
        
        logger.info(f"Chunked text into {len(chunks)} chunks")
        return chunks
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for list of texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            Numpy array of shape (N, 384)
        """
        try:
            if not texts:
                logger.warning("Empty text list provided for embedding")
                return np.array([], dtype=np.float32).reshape(0, self.embedding_dim)
            
            logger.info(f"Generating embeddings for {len(texts)} texts")
            embeddings = self._get_model().encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=False
            )
            
            logger.info(f"Generated embeddings with shape: {embeddings.shape}")
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {str(e)}")
            raise
    
    def embed_document(
        self,
        document_id: int,
        text: str,
        chunk_size: int = 512,
        overlap: int = 50
    ) -> Tuple[int, int, List[str]]:
        """
        Process document: chunk -> embed -> store in FAISS index.
        
        Args:
            document_id: ID of the document
            text: Full extracted text
            chunk_size: Size of text chunks
            overlap: Overlap between chunks
            
        Returns:
            Tuple of (document_id, num_chunks, chunk_ids)
        """
        try:
            logger.info(f"Starting embedding process for document {document_id}")
            
            # Step 1: Chunk text
            chunks = self.chunk_text(text, chunk_size, overlap)
            
            if not chunks:
                logger.warning(f"No chunks created for document {document_id}")
                return document_id, 0, []
            
            logger.info(f"Created {len(chunks)} chunks for document {document_id}")
            
            # Step 2: Extract chunk texts
            chunk_ids = [cid for cid, _ in chunks]
            chunk_texts = [ctext for _, ctext in chunks]
            
            # Step 3: Generate embeddings
            embeddings = self.generate_embeddings(chunk_texts)
            
            # Step 4: Add to FAISS index
            vector_index_manager.add_vectors(
                document_id,
                embeddings,
                chunk_ids,
                chunk_texts
            )
            
            # Step 5: Save index to disk
            vector_index_manager.save_index(document_id)
            
            logger.info(
                f"Successfully embedded document {document_id} with {len(chunks)} chunks"
            )
            return document_id, len(chunks), chunk_ids
            
        except Exception as e:
            logger.error(f"Failed to embed document {document_id}: {str(e)}")
            raise
    
    def search_document(
        self,
        document_id: int,
        query: str,
        k: int = 5
    ) -> List[dict]:
        """
        Search for similar content in a single document.
        
        Args:
            document_id: ID of the document
            query: Search query text
            k: Number of results to return
            
        Returns:
            List of result dictionaries with chunk info
        """
        try:
            # Generate query embedding
            query_embedding = self.generate_embeddings([query])[0]
            
            # Search in document index
            chunk_ids, distances = vector_index_manager.search(
                document_id,
                query_embedding,
                k
            )
            
            # Build results with metadata
            results = []
            for i, (chunk_id, distance) in enumerate(zip(chunk_ids, distances)):
                results.append({
                    'rank': i + 1,
                    'chunk_id': chunk_id,
                    'distance': float(distance),
                    'similarity_score': 1 / (1 + float(distance))  # Convert distance to similarity
                })
            
            logger.info(f"Found {len(results)} results for query in document {document_id}")
            return results
            
        except Exception as e:
            logger.error(f"Search failed for document {document_id}: {str(e)}")
            return []
    
    def search_all_documents(
        self,
        query: str,
        k: int = 5,
        document_ids: List[int] = None
    ) -> List[dict]:
        """
        Search across multiple documents.
        
        Args:
            query: Search query text
            k: Number of results to return
            document_ids: List of document IDs to search (None = all)
            
        Returns:
            List of result dictionaries with document and chunk info
        """
        try:
            # Generate query embedding
            query_embedding = self.generate_embeddings([query])[0]
            
            # Search across documents
            results_data = vector_index_manager.search_across_documents(
                query_embedding,
                k,
                document_ids
            )
            
            # Build results with metadata
            results = []
            for i, (doc_id, chunk_id, distance) in enumerate(results_data):
                results.append({
                    'rank': i + 1,
                    'document_id': doc_id,
                    'chunk_id': chunk_id,
                    'distance': float(distance),
                    'similarity_score': 1 / (1 + float(distance))
                })
            
            logger.info(f"Found {len(results)} results across documents")
            return results
            
        except Exception as e:
            logger.error(f"Cross-document search failed: {str(e)}")
            return []
    
    def get_embedding_for_text(self, text: str) -> np.ndarray:
        """
        Get embedding for a single text (for searching).
        
        Args:
            text: Text to embed
            
        Returns:
            Numpy array of shape (384,)
        """
        try:
            embedding = self._get_model().encode(text, convert_to_numpy=True)
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            raise


def get_vector_service() -> "VectorService":
    """Return a lazily initialized singleton vector service instance."""
    global _vector_service_instance
    if _vector_service_instance is None:
        with _vector_service_lock:
            if _vector_service_instance is None:
                _vector_service_instance = VectorService()
    return _vector_service_instance


class _LazyVectorServiceProxy:
    """Compatibility proxy to keep existing `vector_service.*` call sites unchanged."""

    def __getattr__(self, name):
        return getattr(get_vector_service(), name)


# Lazy vector service proxy (keeps import API stable)
vector_service = _LazyVectorServiceProxy()
