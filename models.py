"""
Database models for document management service.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, Field
from typing import Optional

# SQLAlchemy ORM Base
Base = declarative_base()


# ============================================================================
# SQLAlchemy ORM Models (Database Tables)
# ============================================================================

class Document(Base):
    """
    SQLAlchemy model for storing document metadata.
    """
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_format = Column(String(10), nullable=False)  # pdf, docx, png, txt
    file_path = Column(String(500), nullable=False, unique=True)
    file_size = Column(Integer, nullable=False)  # in bytes
    upload_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Future extensibility fields
    document_type = Column(String(100), nullable=True)  # real_estate_listing, property_report, etc.
    property_id = Column(String(100), nullable=True)  # Reference to property
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_upload_timestamp', 'upload_timestamp'),
        Index('idx_property_id', 'property_id'),
    )


class ExtractedText(Base):
    """
    SQLAlchemy model for storing extracted text content from documents.
    """
    __tablename__ = "extracted_texts"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, unique=True)
    raw_text = Column(Text, nullable=False)
    extraction_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    extraction_status = Column(String(20), default="success", nullable=False)  # success, failed, partial
    extraction_error = Column(Text, nullable=True)  # Store error message if extraction failed
    
    # Index for fast lookup
    __table_args__ = (
        Index('idx_document_id', 'document_id'),
    )


# ============================================================================
# Pydantic Schema Models (API Request/Response)
# ============================================================================

class DocumentCreate(BaseModel):
    """Schema for creating a document (internal use)."""
    filename: str
    file_format: str
    file_path: str
    file_size: int
    document_type: Optional[str] = None
    property_id: Optional[str] = None


class DocumentResponse(BaseModel):
    """Schema for document response."""
    id: int
    filename: str
    file_format: str
    file_size: int
    upload_timestamp: datetime
    document_type: Optional[str] = None
    property_id: Optional[str] = None
    
    class Config:
        from_attributes = True


class ExtractedTextResponse(BaseModel):
    """Schema for extracted text response."""
    id: int
    document_id: int
    raw_text: str = Field(..., description="Extracted text content")
    extraction_timestamp: datetime
    extraction_status: str
    
    class Config:
        from_attributes = True


class DocumentWithTextResponse(BaseModel):
    """Schema for document with extracted text."""
    document: DocumentResponse
    extracted_text: Optional[ExtractedTextResponse] = None
    
    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    """Schema for upload endpoint response."""
    success: bool
    message: str
    document_id: Optional[int] = None
    filename: Optional[str] = None
    error: Optional[str] = None


# ============================================================================
# Vector Embedding Models (Database Tables)
# ============================================================================

class VectorEmbedding(Base):
    """
    SQLAlchemy model for storing vector embedding metadata.
    Tracks which documents have embeddings and metadata about chunks.
    """
    __tablename__ = "vector_embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, unique=True)
    num_chunks = Column(Integer, nullable=False)  # Number of chunks created
    embedding_model = Column(String(100), nullable=False)  # Model name used for embedding
    chunk_size = Column(Integer, nullable=False, default=512)  # Characters per chunk
    chunk_overlap = Column(Integer, nullable=False, default=50)  # Overlap size
    embedding_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Index for fast lookup
    __table_args__ = (
        Index('idx_document_id_vectors', 'document_id'),
    )


# ============================================================================
# Pydantic Schema Models for Vector Operations
# ============================================================================

class VectorEmbeddingResponse(BaseModel):
    """Schema for vector embedding metadata."""
    id: int
    document_id: int
    num_chunks: int
    embedding_model: str
    chunk_size: int
    chunk_overlap: int
    embedding_timestamp: datetime
    
    class Config:
        from_attributes = True


class SearchResult(BaseModel):
    """Schema for a single search result."""
    rank: int
    document_id: Optional[int] = None  # None for single-document search
    chunk_id: str
    distance: float
    similarity_score: float


class SemanticSearchResponse(BaseModel):
    """Schema for semantic search endpoint response."""
    success: bool
    query: str
    num_results: int
    results: List[SearchResult]
    error: Optional[str] = None
