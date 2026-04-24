"""
Vector index management service for FAISS.
Handles creation, storage, and management of vector embeddings.
"""
import heapq
import logging
import pickle
import re
from collections import OrderedDict
from pathlib import Path
from threading import Lock as ThreadLock
from typing import Dict, Optional, Tuple, List
import numpy as np
import faiss
from filelock import FileLock
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

        # Cap how many document indices remain hot in memory.
        self.max_loaded_indices = max(1, int(settings.VECTOR_INDEX_MAX_LOADED_INDICES))
        self.prefilter_min_docs = max(1, int(settings.VECTOR_SEARCH_PREFILTER_MIN_DOCS))
        self.prefilter_multiplier = max(1, int(settings.VECTOR_SEARCH_PREFILTER_MULTIPLIER))
        self.prefilter_min_candidates = max(1, int(settings.VECTOR_SEARCH_PREFILTER_MIN_CANDIDATES))
        
        # Store indices in memory: {document_id: (faiss_index, id_to_chunk_map)}
        self.indices = OrderedDict()
        self.doc_centroids: dict[int, np.ndarray] = {}

        # Per-document write locks: thread-level registry, file-level locking for multi-process safety.
        self._lock_registry: Dict[int, FileLock] = {}
        self._registry_lock = ThreadLock()

        logger.info(f"Vector index manager initialized with directory: {self.index_dir}")

    def _write_lock(self, document_id: int) -> FileLock:
        """Return a per-document FileLock, creating it if needed.

        FileLock uses an OS-level lockfile so multiple processes (Docker replicas,
        multiple Celery workers) block rather than corrupt the FAISS index files.
        """
        with self._registry_lock:
            if document_id not in self._lock_registry:
                lock_path = self.index_dir / f"document_{document_id}.lock"
                self._lock_registry[document_id] = FileLock(str(lock_path), timeout=30)
            return self._lock_registry[document_id]

    def _touch_index(self, document_id: int) -> None:
        """Mark an index as recently used for LRU eviction."""
        if document_id in self.indices:
            self.indices.move_to_end(document_id)

    def _evict_if_needed(self, protected_document_id: int = None) -> None:
        """Evict least recently used in-memory indices to enforce memory cap."""
        while len(self.indices) > self.max_loaded_indices:
            oldest_document_id = next(iter(self.indices))
            if protected_document_id is not None and oldest_document_id == protected_document_id and len(self.indices) > 1:
                self.indices.move_to_end(oldest_document_id)
                oldest_document_id = next(iter(self.indices))

            self.indices.pop(oldest_document_id, None)
            logger.info(
                "Evicted document index %s from memory (max_loaded_indices=%s)",
                oldest_document_id,
                self.max_loaded_indices,
            )

    def _discover_indexed_document_ids(self) -> List[int]:
        """Discover known document IDs from persisted FAISS index files."""
        discovered = set(self.indices.keys())
        pattern = re.compile(r"^document_(\d+)\.index$")
        for file_path in self.index_dir.glob("document_*.index"):
            match = pattern.match(file_path.name)
            if match:
                discovered.add(int(match.group(1)))
        return sorted(discovered)

    @staticmethod
    def _normalize_vector(vector: np.ndarray) -> np.ndarray:
        normalized = np.array(vector, dtype=np.float32)
        norm = np.linalg.norm(normalized)
        if norm > 0:
            normalized = normalized / norm
        return normalized

    def _compute_document_centroid(self, document_id: int) -> Optional[np.ndarray]:
        """Compute a document centroid from vectors currently loaded in memory."""
        if document_id not in self.indices:
            return None

        index = self.indices[document_id]["index"]
        if index.ntotal == 0:
            return None

        try:
            vectors = index.reconstruct_n(0, index.ntotal)
            if vectors.size == 0:
                return None
            return self._normalize_vector(np.mean(vectors, axis=0))
        except Exception as e:
            logger.warning("Failed to reconstruct centroid for document %s: %s", document_id, str(e))
            return None

    def _get_document_centroid(self, document_id: int) -> Optional[np.ndarray]:
        """Return a centroid from cache, in-memory index metadata, or on-disk metadata."""
        centroid = self.doc_centroids.get(document_id)
        if centroid is not None:
            return centroid

        if document_id in self.indices:
            centroid = self.indices[document_id].get("centroid")
            if centroid is None:
                centroid = self._compute_document_centroid(document_id)
                self.indices[document_id]["centroid"] = centroid

            if centroid is not None:
                centroid = self._normalize_vector(centroid)
                self.indices[document_id]["centroid"] = centroid
                self.doc_centroids[document_id] = centroid
                return centroid

        metadata_file = self.index_dir / f"document_{document_id}.pkl"
        if not metadata_file.exists():
            return None

        try:
            with open(metadata_file, "rb") as f:
                metadata = pickle.load(f)
        except Exception as e:
            logger.warning("Failed to load centroid metadata for document %s: %s", document_id, str(e))
            return None

        metadata_centroid = metadata.get("centroid")
        if metadata_centroid is None:
            return None

        centroid = self._normalize_vector(np.array(metadata_centroid, dtype=np.float32))
        self.doc_centroids[document_id] = centroid
        return centroid

    def _prefilter_documents(
        self,
        query_embedding: np.ndarray,
        docs_to_search: List[int],
        k: int,
    ) -> List[int]:
        """Select candidate documents using a global centroid ANN prefilter."""
        if len(docs_to_search) < self.prefilter_min_docs:
            return docs_to_search

        centroid_docs = []
        centroid_vectors = []
        for doc_id in docs_to_search:
            centroid = self._get_document_centroid(doc_id)
            if centroid is not None:
                centroid_docs.append(doc_id)
                centroid_vectors.append(centroid)

        if len(centroid_docs) < self.prefilter_min_docs:
            return docs_to_search

        candidate_count = min(
            len(centroid_docs),
            max(self.prefilter_min_candidates, k * self.prefilter_multiplier),
        )

        centroid_matrix = np.array(centroid_vectors, dtype=np.float32)
        faiss.normalize_L2(centroid_matrix)

        query_row = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_row)

        doc_index = faiss.IndexFlatL2(self.embedding_dim)
        doc_index.add(centroid_matrix)
        _, candidate_indices = doc_index.search(query_row, candidate_count)

        selected = []
        for idx in candidate_indices[0].tolist():
            if 0 <= idx < len(centroid_docs):
                selected.append(centroid_docs[idx])

        return selected if selected else docs_to_search
    
    def create_index(self, document_id: int) -> faiss.IndexFlatL2:
        """
        Create a new FAISS index for a document.
        
        Args:
            document_id: ID of the document
            
        Returns:
            FAISS index object
        """
        try:
            if document_id in self.indices:
                self._touch_index(document_id)
                return self.indices[document_id]['index']

            # Create flat L2 index (Euclidean distance)
            index = faiss.IndexFlatL2(self.embedding_dim)
            
            # Store empty id mapping
            self.indices[document_id] = {
                'index': index,
                'chunk_ids': [],  # Maps index position to chunk_id
                'texts': [],      # Maps index position to original text
                'centroid': None,
            }
            self._touch_index(document_id)
            self._evict_if_needed(protected_document_id=document_id)
            
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
            with self._write_lock(document_id):
                return self._add_vectors_locked(document_id, embeddings, chunk_ids, chunk_texts)
        except Exception as e:
            logger.error(f"Failed to add vectors for document {document_id}: {str(e)}")
            raise

    def _add_vectors_locked(
        self,
        document_id: int,
        embeddings: np.ndarray,
        chunk_ids: List[str],
        chunk_texts: List[str]
    ) -> bool:
        """Inner add_vectors implementation; caller must hold _write_lock(document_id)."""
        try:
            if document_id not in self.indices:
                if not self.load_index(document_id):
                    self.create_index(document_id)
            else:
                self._touch_index(document_id)

            doc_data = self.indices[document_id]
            prior_vector_count = int(doc_data['index'].ntotal)
            prior_centroid = doc_data.get('centroid')
            if prior_vector_count > 0 and prior_centroid is None:
                prior_centroid = self._compute_document_centroid(document_id)
            
            # Ensure embeddings are float32 (FAISS requirement)
            embeddings = np.array(embeddings, dtype=np.float32)
            
            # Normalize embeddings for better L2 distance
            faiss.normalize_L2(embeddings)
            
            # Add to index
            index = doc_data['index']
            index.add(embeddings)
            
            # Track chunk IDs and texts
            doc_data['chunk_ids'].extend(chunk_ids)
            doc_data['texts'].extend(chunk_texts)

            new_centroid = self._normalize_vector(np.mean(embeddings, axis=0))
            if prior_vector_count > 0 and prior_centroid is not None:
                merged = (
                    (prior_centroid * prior_vector_count) +
                    (new_centroid * len(embeddings))
                ) / (prior_vector_count + len(embeddings))
                new_centroid = self._normalize_vector(merged)

            doc_data['centroid'] = new_centroid
            self.doc_centroids[document_id] = new_centroid
            
            logger.info(
                f"Added {len(embeddings)} vectors to document {document_id} index"
            )
            self._touch_index(document_id)
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
                if not self.load_index(document_id):
                    logger.warning(f"No index found for document {document_id}")
                    return [], []
            
            index = self.indices[document_id]['index']
            self._touch_index(document_id)
            
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
            top_results = []

            # Determine which documents to search
            docs_to_search = sorted(set(document_ids)) if document_ids else self._discover_indexed_document_ids()
            if not docs_to_search:
                return []

            candidate_docs = self._prefilter_documents(query_embedding, docs_to_search, k)
            per_document_k = max(10, k)
            
            for doc_id in candidate_docs:
                chunk_ids, distances = self.search(doc_id, query_embedding, k=per_document_k)

                for chunk_id, distance in zip(chunk_ids, distances):
                    # Keep only global top-k using a bounded max-heap by distance.
                    candidate = (-float(distance), doc_id, chunk_id)
                    if len(top_results) < k:
                        heapq.heappush(top_results, candidate)
                    elif candidate[0] > top_results[0][0]:
                        heapq.heapreplace(top_results, candidate)

            ordered = sorted(
                [(-neg_distance, doc_id, chunk_id) for neg_distance, doc_id, chunk_id in top_results],
                key=lambda item: item[0],
            )

            return [(doc_id, chunk_id, distance) for distance, doc_id, chunk_id in ordered]
            
        except Exception as e:
            logger.error(f"Cross-document search failed: {str(e)}")
            return []
    
    def save_index(self, document_id: int) -> bool:
        """
        Save FAISS index to disk for persistence.

        Uses a per-document FileLock so concurrent workers cannot write the
        same index simultaneously and corrupt the files.

        Args:
            document_id: ID of the document

        Returns:
            True if successful
        """
        try:
            with self._write_lock(document_id):
                return self._save_index_locked(document_id)
        except Exception as e:
            logger.error(f"Failed to save index for document {document_id}: {str(e)}")
            return False

    def _save_index_locked(self, document_id: int) -> bool:
        """Inner save_index; caller must hold _write_lock(document_id)."""
        if document_id not in self.indices:
            logger.warning(f"Index not found for document {document_id}")
            return False

        index_file = self.index_dir / f"document_{document_id}.index"
        metadata_file = self.index_dir / f"document_{document_id}.pkl"
        tmp_index = index_file.with_suffix(".index.tmp")
        tmp_meta = metadata_file.with_suffix(".pkl.tmp")

        doc_data = self.indices[document_id]

        try:
            # Write to temp files first, then atomically rename to avoid
            # partial writes being visible to concurrent readers.
            faiss.write_index(doc_data['index'], str(tmp_index))

            metadata = {
                'chunk_ids': doc_data['chunk_ids'],
                'texts': doc_data['texts'],
                'centroid': doc_data['centroid'].tolist() if doc_data.get('centroid') is not None else None,
            }
            with open(tmp_meta, 'wb') as f:
                pickle.dump(metadata, f)

            tmp_index.replace(index_file)
            tmp_meta.replace(metadata_file)

            logger.info(f"Saved FAISS index for document {document_id}")
            return True
        except Exception:
            tmp_index.unlink(missing_ok=True)
            tmp_meta.unlink(missing_ok=True)
            raise
    
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
                'texts': metadata['texts'],
                'centroid': self._normalize_vector(np.array(metadata['centroid'], dtype=np.float32)) if metadata.get('centroid') is not None else None,
            }
            if self.indices[document_id]['centroid'] is not None:
                self.doc_centroids[document_id] = self.indices[document_id]['centroid']
            self._touch_index(document_id)
            self._evict_if_needed(protected_document_id=document_id)
            
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
            with self._write_lock(document_id):
                if document_id in self.indices:
                    del self.indices[document_id]
                self.doc_centroids.pop(document_id, None)

                for suffix in [".index", ".pkl", ".index.tmp", ".pkl.tmp"]:
                    p = self.index_dir / f"document_{document_id}{suffix}"
                    p.unlink(missing_ok=True)

            # Release and drop the lock entry so the lockfile itself can be removed.
            with self._registry_lock:
                self._lock_registry.pop(document_id, None)
            lock_file = self.index_dir / f"document_{document_id}.lock"
            lock_file.unlink(missing_ok=True)

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
