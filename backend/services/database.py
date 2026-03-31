"""
Database service module for managing PostgreSQL operations.
Handles document and extracted text persistence.
"""
import logging
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from config import settings
from models import (
    Base,
    Document,
    ExtractedText,
    VectorEmbedding,
    Analysis,
    AnalysisOutput,
    AnalysisEvent,
)

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for managing database operations."""
    
    def __init__(self, database_url: str = settings.DATABASE_URL):
        """
        Initialize database connection.
        
        Args:
            database_url: PostgreSQL connection string
        """
        try:
            self.engine = create_engine(
                database_url,
                echo=settings.DEBUG,
                pool_pre_ping=True,  # Verify connections before using
                pool_recycle=3600,   # Recycle connections every hour
            )
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            logger.info("Database engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database engine: {str(e)}")
            raise
    
    def init_db(self):
        """
        Initialize database tables.
        Creates tables if they don't exist.
        """
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created/verified successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database tables: {str(e)}")
            raise
    
    def get_session(self) -> Session:
        """
        Get a new database session.
        
        Returns:
            SQLAlchemy session object
        """
        return self.SessionLocal()
    
    def save_document(
        self,
        filename: str,
        file_format: str,
        file_path: str,
        file_size: int,
        document_type: str = None,
        property_id: str = None
    ) -> Document:
        """
        Save document metadata to database.
        
        Args:
            filename: Original filename
            file_format: File format (pdf, docx, png, txt)
            file_path: Path where file is stored
            file_size: File size in bytes
            document_type: Optional document type classification
            property_id: Optional property ID reference
            
        Returns:
            Saved Document object
            
        Raises:
            Exception: If database operation fails
        """
        session = self.get_session()
        try:
            document = Document(
                filename=filename,
                file_format=file_format,
                file_path=file_path,
                file_size=file_size,
                document_type=document_type,
                property_id=property_id
            )
            session.add(document)
            session.commit()
            session.refresh(document)
            logger.info(f"Document saved successfully: {filename} (ID: {document.id})")
            return document
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save document: {str(e)}")
            raise
        finally:
            session.close()
    
    def save_extracted_text(
        self,
        document_id: int,
        raw_text: str,
        extraction_status: str = "success",
        extraction_error: str = None
    ) -> ExtractedText:
        """
        Save extracted text content to database.
        
        Args:
            document_id: ID of the document
            raw_text: Extracted text content
            extraction_status: Status of extraction (success, failed, partial)
            extraction_error: Optional error message if extraction failed
            
        Returns:
            Saved ExtractedText object
            
        Raises:
            Exception: If database operation fails
        """
        session = self.get_session()
        try:
            extracted_text = ExtractedText(
                document_id=document_id,
                raw_text=raw_text,
                extraction_status=extraction_status,
                extraction_error=extraction_error
            )
            session.add(extracted_text)
            session.commit()
            session.refresh(extracted_text)
            logger.info(f"Extracted text saved successfully for document ID: {document_id}")
            return extracted_text
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save extracted text: {str(e)}")
            raise
        finally:
            session.close()
    
    def get_document(self, document_id: int) -> Document:
        """
        Retrieve document by ID.
        
        Args:
            document_id: Document ID
            
        Returns:
            Document object or None if not found
        """
        session = self.get_session()
        try:
            document = session.query(Document).filter(
                Document.id == document_id
            ).first()
            return document
        finally:
            session.close()
    
    def get_document_text(self, document_id: int) -> ExtractedText:
        """
        Retrieve extracted text for a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            ExtractedText object or None if not found
        """
        session = self.get_session()
        try:
            extracted_text = session.query(ExtractedText).filter(
                ExtractedText.document_id == document_id
            ).first()
            return extracted_text
        finally:
            session.close()
    
    def get_all_documents(self, limit: int = 100, offset: int = 0) -> list:
        """
        Retrieve all documents with pagination.
        
        Args:
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            
        Returns:
            List of Document objects
        """
        session = self.get_session()
        try:
            documents = session.query(Document).offset(offset).limit(limit).all()
            return documents
        finally:
            session.close()
    
    def save_vector_embedding_metadata(
        self,
        document_id: int,
        num_chunks: int,
        embedding_model: str = "all-MiniLM-L6-v2",
        chunk_size: int = 512,
        chunk_overlap: int = 50
    ) -> VectorEmbedding:
        """
        Save vector embedding metadata to database.
        
        Args:
            document_id: ID of the document
            num_chunks: Number of chunks created for this document
            embedding_model: Name of the embedding model used
            chunk_size: Size of each chunk
            chunk_overlap: Overlap between chunks
            
        Returns:
            Saved VectorEmbedding object
            
        Raises:
            Exception: If database operation fails
        """
        session = self.get_session()
        try:
            # Check if embedding metadata already exists
            existing = session.query(VectorEmbedding).filter(
                VectorEmbedding.document_id == document_id
            ).first()
            
            if existing:
                # Update existing record
                existing.num_chunks = num_chunks
                existing.embedding_model = embedding_model
                existing.chunk_size = chunk_size
                existing.chunk_overlap = chunk_overlap
                session.commit()
                session.refresh(existing)
                logger.info(f"Vector embedding metadata updated for document ID: {document_id}")
                return existing
            else:
                # Create new record
                vector_embedding = VectorEmbedding(
                    document_id=document_id,
                    num_chunks=num_chunks,
                    embedding_model=embedding_model,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap
                )
                session.add(vector_embedding)
                session.commit()
                session.refresh(vector_embedding)
                logger.info(f"Vector embedding metadata saved successfully for document ID: {document_id}")
                return vector_embedding
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save vector embedding metadata: {str(e)}")
            raise
        finally:
            session.close()

    def create_analysis(
        self,
        document_id: int,
        model_version: str = "v1"
    ) -> Analysis:
        """
        Create a queued analysis task record.

        Args:
            document_id: ID of the source document
            model_version: Analysis model/version label

        Returns:
            Saved Analysis object
        """
        session = self.get_session()
        try:
            analysis = Analysis(
                document_id=document_id,
                status="queued",
                model_version=model_version
            )
            session.add(analysis)
            session.commit()
            session.refresh(analysis)
            logger.info(f"Analysis created: ID={analysis.id}, document_id={document_id}")
            return analysis
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create analysis: {str(e)}")
            raise
        finally:
            session.close()

    def get_analysis(self, analysis_id: int) -> Analysis:
        """
        Retrieve analysis by ID.

        Args:
            analysis_id: Analysis ID

        Returns:
            Analysis object or None if not found
        """
        session = self.get_session()
        try:
            return session.query(Analysis).filter(Analysis.id == analysis_id).first()
        finally:
            session.close()

    def update_analysis_status(
        self,
        analysis_id: int,
        status: str,
        error: str = None,
        started_at: datetime = None,
        finished_at: datetime = None
    ) -> Analysis:
        """
        Update analysis status and optional timestamps/error.

        Args:
            analysis_id: Analysis ID
            status: New status (queued, processing, done, failed)
            error: Optional error message
            started_at: Optional start timestamp override
            finished_at: Optional finish timestamp override

        Returns:
            Updated Analysis object
        """
        session = self.get_session()
        try:
            analysis = session.query(Analysis).filter(Analysis.id == analysis_id).first()
            if not analysis:
                raise ValueError(f"Analysis not found: {analysis_id}")

            analysis.status = status
            analysis.error = error

            if started_at:
                analysis.started_at = started_at
            elif status == "processing" and analysis.started_at is None:
                analysis.started_at = datetime.utcnow()

            if finished_at:
                analysis.finished_at = finished_at
            elif status in ("done", "failed"):
                analysis.finished_at = datetime.utcnow()

            session.commit()
            session.refresh(analysis)
            return analysis
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update analysis status: {str(e)}")
            raise
        finally:
            session.close()

    def save_analysis_output(
        self,
        analysis_id: int,
        legal_json: dict = None,
        risk_json: dict = None,
        valuation_json: dict = None,
        final_json: dict = None
    ) -> AnalysisOutput:
        """
        Save or update analysis output payloads.

        Args:
            analysis_id: Analysis ID
            legal_json: Legal module output
            risk_json: Risk module output
            valuation_json: Valuation module output
            final_json: Aggregated final output

        Returns:
            Saved AnalysisOutput object
        """
        session = self.get_session()
        try:
            output = session.query(AnalysisOutput).filter(
                AnalysisOutput.analysis_id == analysis_id
            ).first()

            if output:
                output.legal_json = legal_json
                output.risk_json = risk_json
                output.valuation_json = valuation_json
                output.final_json = final_json
            else:
                output = AnalysisOutput(
                    analysis_id=analysis_id,
                    legal_json=legal_json,
                    risk_json=risk_json,
                    valuation_json=valuation_json,
                    final_json=final_json,
                )
                session.add(output)

            session.commit()
            session.refresh(output)
            return output
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save analysis output: {str(e)}")
            raise
        finally:
            session.close()

    def get_analysis_output(self, analysis_id: int) -> AnalysisOutput:
        """
        Retrieve analysis outputs by analysis ID.

        Args:
            analysis_id: Analysis ID

        Returns:
            AnalysisOutput or None
        """
        session = self.get_session()
        try:
            return session.query(AnalysisOutput).filter(
                AnalysisOutput.analysis_id == analysis_id
            ).first()
        finally:
            session.close()

    def add_analysis_event(
        self,
        analysis_id: int,
        stage: str,
        payload: dict = None
    ) -> AnalysisEvent:
        """
        Add an analysis lifecycle event.

        Args:
            analysis_id: Analysis ID
            stage: Event stage label
            payload: Optional event payload

        Returns:
            Saved AnalysisEvent object
        """
        session = self.get_session()
        try:
            event = AnalysisEvent(
                analysis_id=analysis_id,
                stage=stage,
                payload=payload,
            )
            session.add(event)
            session.commit()
            session.refresh(event)
            return event
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to add analysis event: {str(e)}")
            raise
        finally:
            session.close()


# Global database service instance
db_service = DatabaseService()
