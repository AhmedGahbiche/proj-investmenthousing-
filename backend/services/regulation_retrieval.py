"""
Dedicated FAISS retrieval service for regulation corpus.
Maintains a separate index space from document-level embeddings.
"""
import logging
from typing import List, Dict
from services.vector_index import VectorIndexManager
from services.vector_service import vector_service

logger = logging.getLogger(__name__)


class RegulationRetrievalService:
    """Retrieval service for regulation corpus semantic context."""

    def __init__(self, index_dir: str = "./regulation_indices"):
        self.regulation_index = VectorIndexManager(index_dir=index_dir)

    def _get_chunk_text(self, regulation_id: int, chunk_id: str) -> str:
        """
        Resolve chunk text from in-memory or persisted regulation index metadata.
        """
        if regulation_id not in self.regulation_index.indices:
            self.regulation_index.load_index(regulation_id)

        data = self.regulation_index.indices.get(regulation_id)
        if not data:
            return ""

        try:
            idx = data['chunk_ids'].index(chunk_id)
            return data['texts'][idx]
        except (ValueError, IndexError, KeyError):
            return ""

    def index_regulation_text(
        self,
        regulation_id: int,
        text: str,
        chunk_size: int = 512,
        overlap: int = 50,
    ) -> int:
        """
        Chunk and index regulation text in dedicated FAISS storage.

        Returns:
            Number of indexed chunks.
        """
        chunks = vector_service.chunk_text(text, chunk_size=chunk_size, overlap=overlap)
        if not chunks:
            return 0

        chunk_ids = [chunk_id for chunk_id, _ in chunks]
        chunk_texts = [chunk_text for _, chunk_text in chunks]
        embeddings = vector_service.generate_embeddings(chunk_texts)

        self.regulation_index.add_vectors(
            regulation_id,
            embeddings,
            chunk_ids,
            chunk_texts,
        )
        self.regulation_index.save_index(regulation_id)
        return len(chunks)

    def retrieve_context(
        self,
        query: str,
        k: int = 5,
        regulation_ids: List[int] = None,
    ) -> List[Dict]:
        """
        Retrieve top-k semantic context from regulation corpus indices.

        Returns:
            List of context dictionaries sorted by similarity.
        """
        if not query or not query.strip():
            return []

        query_embedding = vector_service.get_embedding_for_text(query)
        result_rows = self.regulation_index.search_across_documents(
            query_embedding=query_embedding,
            k=k,
            document_ids=regulation_ids,
        )

        contexts: List[Dict] = []
        for rank, (regulation_id, chunk_id, distance) in enumerate(result_rows, start=1):
            contexts.append(
                {
                    "rank": rank,
                    "regulation_id": regulation_id,
                    "chunk_id": chunk_id,
                    "text": self._get_chunk_text(regulation_id, chunk_id),
                    "distance": float(distance),
                    "similarity_score": 1 / (1 + float(distance)),
                }
            )

        logger.info("Regulation retrieval returned %d context chunks", len(contexts))
        return contexts


regulation_retrieval_service = RegulationRetrievalService()
