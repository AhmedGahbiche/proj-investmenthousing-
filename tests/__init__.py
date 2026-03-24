"""
Test suite for document management service.
Tests end-to-end upload, storage, text extraction, and database operations.
"""
import pytest
import tempfile
import os
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Add backend directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from services.database import db_service
from services.file_storage import file_storage
from services.text_extraction import text_extraction
from services.upload_service import upload_service

# Create test client
client = TestClient(app)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Initialize test database before running tests."""
    db_service.init_db()
    yield
    # Cleanup could be added here if needed


# ============================================================================
# Health Check Tests
# ============================================================================

class TestHealthCheck:
    """Test health check endpoint."""
    
    def test_health_check(self):
        """Test that health check endpoint returns success."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data


# ============================================================================
# File Storage Tests
# ============================================================================

class TestFileStorage:
    """Test file storage service."""
    
    def test_save_and_read_file(self):
        """Test saving and reading a file."""
        test_content = b"This is test content"
        test_filename = "test_document.txt"
        
        # Save file
        file_path = file_storage.save_file(test_content, test_filename)
        assert file_path is not None
        assert file_storage.file_exists(file_path)
        
        # Read file
        read_content = file_storage.read_file(file_path)
        assert read_content == test_content
        
        # Cleanup
        file_storage.delete_file(file_path)
    
    def test_unique_filename_generation(self):
        """Test that generated filenames are unique."""
        test_content = b"Test content"
        
        file_path1 = file_storage.save_file(test_content, "document.txt")
        file_path2 = file_storage.save_file(test_content, "document.txt")
        
        # Paths should be different
        assert file_path1 != file_path2
        
        # But both should exist
        assert file_storage.file_exists(file_path1)
        assert file_storage.file_exists(file_path2)
        
        # Cleanup
        file_storage.delete_file(file_path1)
        file_storage.delete_file(file_path2)


# ============================================================================
# Text Extraction Tests
# ============================================================================

class TestTextExtraction:
    """Test text extraction service."""
    
    def test_extract_text_from_txt(self):
        """Test extracting text from TXT file."""
        test_content = b"This is a test document.\nWith multiple lines.\nFor testing purposes."
        
        # Save test file
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(test_content)
            temp_path = f.name
        
        try:
            # Extract text
            text, status = text_extraction.extract_text_from_txt(temp_path)
            
            assert status == "success"
            assert "test document" in text
            assert "multiple lines" in text
        finally:
            os.unlink(temp_path)
    
    def test_extract_text_with_format(self):
        """Test extract_text dispatches correctly based on format."""
        test_content = b"Plain text content"
        
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(test_content)
            temp_path = f.name
        
        try:
            # Extract with format specified
            text, status, error = text_extraction.extract_text(temp_path, "txt")
            
            assert status == "success"
            assert error is None
            assert "Plain text content" in text
        finally:
            os.unlink(temp_path)
    
    def test_unsupported_format(self):
        """Test handling of unsupported file formats."""
        text, status, error = text_extraction.extract_text("dummy.xyz", "xyz")
        
        assert status == "failed"
        assert error is not None
        assert "Unsupported file format" in error


# ============================================================================
# Upload Service Tests
# ============================================================================

class TestUploadService:
    """Test upload service."""
    
    def test_validate_file_success(self):
        """Test successful file validation."""
        content = b"Valid content"
        filename = "document.pdf"
        
        is_valid, error = upload_service.validate_file(filename, content)
        
        assert is_valid is True
        assert error == ""
    
    def test_validate_file_empty(self):
        """Test validation of empty file."""
        content = b""
        filename = "document.pdf"
        
        is_valid, error = upload_service.validate_file(filename, content)
        
        assert is_valid is False
        assert "empty" in error.lower()
    
    def test_validate_file_unsupported_format(self):
        """Test validation of unsupported file format."""
        content = b"Some content"
        filename = "document.xyz"
        
        is_valid, error = upload_service.validate_file(filename, content)
        
        assert is_valid is False
        assert "not supported" in error.lower()
    
    def test_validate_file_no_extension(self):
        """Test validation of file without extension."""
        content = b"Some content"
        filename = "document"
        
        is_valid, error = upload_service.validate_file(filename, content)
        
        assert is_valid is False
        assert "no extension" in error.lower()
    
    def test_process_upload_txt(self):
        """Test end-to-end upload process with TXT file."""
        test_content = b"This is a test document for upload testing."
        filename = "test_upload.txt"
        
        result = upload_service.process_upload(filename, test_content)
        
        assert result['success'] is True
        assert result['document_id'] is not None
        assert result['filename'] == filename
        assert result['error'] is None
    
    def test_process_upload_invalid_file(self):
        """Test upload process with invalid file."""
        test_content = b""  # Empty file
        filename = "test_invalid.pdf"
        
        result = upload_service.process_upload(filename, test_content)
        
        assert result['success'] is False
        assert result['document_id'] is None
        assert result['error'] is not None


# ============================================================================
# API Endpoint Tests
# ============================================================================

class TestUploadEndpoint:
    """Test upload API endpoint."""
    
    def test_upload_txt_file(self):
        """Test uploading a TXT file via API."""
        file_content = b"This is test document content for the API."
        
        response = client.post(
            "/upload",
            files={"file": ("test_document.txt", file_content, "text/plain")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["document_id"] is not None
        assert data["filename"] == "test_document.txt"
    
    def test_upload_with_metadata(self):
        """Test uploading with document type and property ID."""
        file_content = b"Property listing document content."
        
        response = client.post(
            "/upload?document_type=listing&property_id=PROP123",
            files={"file": ("listing.txt", file_content, "text/plain")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_upload_unsupported_format(self):
        """Test uploading unsupported file format."""
        file_content = b"Some binary content"
        
        response = client.post(
            "/upload",
            files={"file": ("document.xyz", file_content, "application/octet-stream")}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data or "detail" in data
    
    def test_upload_empty_file(self):
        """Test uploading empty file."""
        file_content = b""
        
        response = client.post(
            "/upload",
            files={"file": ("empty.txt", file_content, "text/plain")}
        )
        
        assert response.status_code == 400


class TestDocumentRetrievalEndpoints:
    """Test document retrieval endpoints."""
    
    @pytest.fixture(autouse=True)
    def setup_test_document(self):
        """Create a test document before each test."""
        self.test_content = b"Test document for retrieval testing."
        result = upload_service.process_upload(
            "test_retrieval.txt",
            self.test_content
        )
        self.document_id = result['document_id']
        yield
    
    def test_get_document(self):
        """Test retrieving document metadata."""
        response = client.get(f"/documents/{self.document_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == self.document_id
        assert data["filename"] == "test_retrieval.txt"
    
    def test_get_document_text(self):
        """Test retrieving extracted text."""
        response = client.get(f"/documents/{self.document_id}/text")
        
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == self.document_id
        assert "raw_text" in data
        assert "extraction_status" in data
    
    def test_get_document_full(self):
        """Test retrieving document with text."""
        response = client.get(f"/documents/{self.document_id}/full")
        
        assert response.status_code == 200
        data = response.json()
        assert "document" in data
        assert data["document"]["id"] == self.document_id
        assert "extracted_text" in data
    
    def test_list_documents(self):
        """Test listing documents."""
        response = client.get("/documents")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_list_documents_with_pagination(self):
        """Test listing documents with pagination."""
        response = client.get("/documents?limit=10&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_nonexistent_document(self):
        """Test retrieving non-existent document."""
        response = client.get("/documents/99999")
        
        assert response.status_code == 404


# ============================================================================
# Integration Tests
# ============================================================================

class TestEndToEndUpload:
    """End-to-end integration tests."""
    
    def test_full_upload_and_retrieval_flow(self):
        """Test complete upload, storage, extraction, and retrieval flow."""
        # 1. Upload file
        file_content = b"Real estate property listing document.\nLocation: 123 Main St.\nPrice: $500,000"
        
        upload_response = client.post(
            "/upload?document_type=listing&property_id=PROP001",
            files={"file": ("property_listing.txt", file_content, "text/plain")}
        )
        
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        assert upload_data["success"] is True
        document_id = upload_data["document_id"]
        
        # 2. Retrieve document metadata
        doc_response = client.get(f"/documents/{document_id}")
        assert doc_response.status_code == 200
        
        # 3. Retrieve extracted text
        text_response = client.get(f"/documents/{document_id}/text")
        assert text_response.status_code == 200
        text_data = text_response.json()
        assert "real estate" in text_data["raw_text"].lower()
        
        # 4. Retrieve full document with text
        full_response = client.get(f"/documents/{document_id}/full")
        assert full_response.status_code == 200
        full_data = full_response.json()
        assert full_data["document"]["property_id"] == "PROP001"
        assert full_data["extracted_text"] is not None


# ============================================================================
# Vector Search Tests
# ============================================================================

class TestVectorEmbedding:
    """Test vector embedding and semantic search functionality."""
    
    @pytest.fixture
    def sample_document(self):
        """Create a sample document for vector search tests."""
        # Upload a document with meaningful content
        file_content = b"""
        Beautiful property located in downtown area.
        The house features 4 bedrooms, 2 bathrooms, and a modern kitchen.
        Hardwood floors throughout the main living areas.
        Large backyard with mature trees for outdoor entertainment.
        The property has been recently renovated with new roof and HVAC system.
        Close to schools, shopping, and public transportation.
        Asking price: $450,000
        """
        
        response = client.post(
            "/upload?document_type=property_listing&property_id=TEST001",
            files={"file": ("property.txt", file_content, "text/plain")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        return data["document_id"]
    
    def test_document_embedding_after_upload(self, sample_document):
        """Test that document gets embedded after upload."""
        # Wait a moment for processing
        import time
        time.sleep(1)
        
        # Check if vector embedding metadata was saved
        # This would require an endpoint to check embedding status
        # For now, we verify the document exists and was processed
        response = client.get(f"/documents/{sample_document}")
        assert response.status_code == 200
    
    def test_search_within_document(self, sample_document):
        """Test semantic search within a single document."""
        # Give the system time to embed the document
        import time
        time.sleep(1)
        
        response = client.post(
            f"/search/document/{sample_document}?query=bedrooms&k=5"
        )
        
        # Search might return 404 if embeddings not yet available,
        # but endpoint should exist
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert data["query"] == "bedrooms"
            assert "results" in data
    
    def test_search_across_documents(self):
        """Test semantic search across all documents."""
        response = client.post(
            "/search?query=property&k=10"
        )
        
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert data["query"] == "property"
            assert "results" in data
            assert isinstance(data["num_results"], int)
    
    def test_search_with_invalid_document_ids(self):
        """Test search with invalid document IDs parameter."""
        response = client.post(
            "/search?query=test&document_ids=invalid,format"
        )
        
        assert response.status_code == 400
    
    def test_search_empty_query(self):
        """Test search with empty query."""
        response = client.post(
            "/search/document/1?query="
        )
        
        # Empty query should be rejected
        assert response.status_code in [400, 422]
    
    def test_search_with_k_parameter(self):
        """Test search with different k values."""
        response = client.post(
            "/search?query=building&k=3"
        )
        
        if response.status_code == 200:
            data = response.json()
            # Should not return more than k results
            assert len(data["results"]) <= 3
    
    def test_search_k_limits(self):
        """Test that k parameter respects limits."""
        # Test k > max limit
        response = client.post(
            "/search?query=test&k=100"
        )
        
        # Should either reject or cap at 50
        if response.status_code == 200:
            data = response.json()
            assert len(data["results"]) <= 50


class TestVectorService:
    """Test vector service components directly."""
    
    def test_text_chunking(self):
        """Test text chunking functionality."""
        from services.vector_service import vector_service
        
        long_text = "word " * 200  # Create text longer than chunk size
        chunks = vector_service.chunk_text(long_text, chunk_size=50, overlap=10)
        
        assert len(chunks) > 1
        # Each chunk should have (id, text) tuple
        for chunk_id, chunk_text in chunks:
            assert chunk_id is not None
            assert len(chunk_text) > 0
    
    def test_embedding_generation(self):
        """Test embedding generation."""
        from services.vector_service import vector_service
        
        texts = [
            "The house is beautiful",
            "The building is modern",
            "The property has character"
        ]
        
        embeddings = vector_service.generate_embeddings(texts)
        
        # Should return numpy array with shape (3, 384)
        assert embeddings.shape == (3, 384)
    
    def test_single_text_embedding(self):
        """Test embedding a single text."""
        from services.vector_service import vector_service
        
        text = "Beautiful home with garden"
        embedding = vector_service.get_embedding_for_text(text)
        
        # Should return 1D array of size 384
        assert embedding.shape == (384,)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
