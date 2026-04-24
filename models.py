"""
Database models for document management service.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Index, JSON, UniqueConstraint
from sqlalchemy.orm import declarative_base
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List

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
    
    model_config = ConfigDict(from_attributes=True)


class ExtractedTextResponse(BaseModel):
    """Schema for extracted text response."""
    id: int
    document_id: int
    raw_text: str = Field(..., description="Extracted text content")
    extraction_timestamp: datetime
    extraction_status: str
    
    model_config = ConfigDict(from_attributes=True)


class DocumentWithTextResponse(BaseModel):
    """Schema for document with extracted text."""
    document: DocumentResponse
    extracted_text: Optional[ExtractedTextResponse] = None
    
    model_config = ConfigDict(from_attributes=True)


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


class Analysis(Base):
    """
    SQLAlchemy model for tracking asynchronous analysis jobs.
    """
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    status = Column(String(20), nullable=False, default="queued")
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)
    model_version = Column(String(100), nullable=True)

    __table_args__ = (
        Index('idx_analyses_document_id', 'document_id'),
        Index('idx_analyses_status', 'status'),
    )


class AnalysisOutput(Base):
    """
    SQLAlchemy model for analysis outputs per analysis run.
    """
    __tablename__ = "analysis_outputs"

    analysis_id = Column(Integer, ForeignKey("analyses.id"), primary_key=True)
    legal_json = Column(JSON, nullable=True)
    risk_json = Column(JSON, nullable=True)
    valuation_json = Column(JSON, nullable=True)
    final_json = Column(JSON, nullable=True)


class AnalysisModuleOutput(Base):
    """
    Normalized replacement for the wide AnalysisOutput table.

    One row per module per analysis run. Replaces storing four JSON blobs as
    columns on a single row, which prevented partial-completion tracking and
    made schema evolution expensive.

    module_name is one of: 'legal', 'risk', 'valuation', 'final'.
    status is one of: 'completed', 'partial', 'failed'.
    """
    __tablename__ = "analysis_module_outputs"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False)
    module_name = Column(String(50), nullable=False)
    output_json = Column(JSON, nullable=True)
    status = Column(String(20), nullable=False, default="completed")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("analysis_id", "module_name", name="uq_analysis_module"),
        Index("idx_module_outputs_analysis_id", "analysis_id"),
    )


class AnalysisEvent(Base):
    """
    SQLAlchemy model for optional analysis stage events.
    """
    __tablename__ = "analysis_events"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False)
    stage = Column(String(100), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    payload = Column(JSON, nullable=True)

    __table_args__ = (
        Index('idx_analysis_events_analysis_id', 'analysis_id'),
        Index('idx_analysis_events_stage', 'stage'),
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
    
    model_config = ConfigDict(from_attributes=True)


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


class AnalyzeRequest(BaseModel):
    """Schema for creating an analysis task."""
    document_id: int
    model_version: Optional[str] = "v1"


class AnalyzeCreateResponse(BaseModel):
    """Schema for analysis creation response."""
    success: bool
    analysis_id: int
    document_id: int
    status: str
    task_id: Optional[str] = None


class AnalyzePropertyRequest(BaseModel):
    """Schema for creating an analysis task across multiple documents."""
    document_ids: List[int]
    property_name: Optional[str] = None


class AnalyzePropertyCreateResponse(BaseModel):
    """Schema for property-level analysis creation response."""
    success: bool
    analysis_id: int
    document_ids: List[int]
    status: str
    report_url: str


class AnalysisOutputResponse(BaseModel):
    """Schema for analysis output payload.

    Preserves the original four-field API contract regardless of whether the
    underlying storage is the old wide AnalysisOutput row or the new normalized
    AnalysisModuleOutput rows.
    """
    legal_json: Optional[dict] = None
    risk_json: Optional[dict] = None
    valuation_json: Optional[dict] = None
    final_json: Optional[dict] = None


class AnalysisStatusResponse(BaseModel):
    """Schema for analysis status response."""
    analysis_id: int
    document_id: int
    status: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error: Optional[str] = None
    model_version: Optional[str] = None
    outputs: Optional[AnalysisOutputResponse] = None