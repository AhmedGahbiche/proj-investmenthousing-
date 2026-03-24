# Document Management Service

A production-ready document management service for a real estate analysis platform. Built with FastAPI, PostgreSQL, and modular Python services.

## Overview

This backend service provides a robust document upload and storage system with the following capabilities:

- **Multi-format Document Upload**: Accepts PDF, DOCX, PNG (with OCR), and TXT files
- **Automatic Text Extraction**: Extracts text content from documents for later processing
- **Persistent Storage**: Stores documents and extracted text in PostgreSQL
- **Modular Architecture**: Clean separation of concerns across specialized modules
- **Production-Ready**: Error handling, logging, input validation, and transaction management

## Architecture

### Module Structure

```
backend/
├── main.py                    # FastAPI application and endpoints
├── config.py                  # Configuration management
├── models.py                  # SQLAlchemy ORM models + Pydantic schemas
├── services/
│   ├── upload_service.py      # File validation and upload orchestration
│   ├── file_storage.py        # Persistent file storage operations
│   ├── text_extraction.py     # Format-specific text extraction
│   └── database.py            # PostgreSQL operations
├── uploads/                   # Directory for storing uploaded files
├── logs/                      # Application logs
└── tests/                     # Test suite
```

### Data Flow

```
Uploaded File
    ↓
File Validation (upload_service)
    ↓
    ├→ File Storage (file_storage) → Disk
    ├→ Document Metadata Save (database) → PostgreSQL
    └→ Text Extraction (text_extraction)
         ↓
    Extracted Text Save (database) → PostgreSQL
    ↓
Response to Client
```

## Installation & Setup

### Prerequisites

- Python 3.10+
- PostgreSQL 12+
- pip/conda for package management

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Database

Create a `.env` file in the `backend` directory:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/document_management
APP_NAME=Document Management Service
DEBUG=False
LOG_LEVEL=INFO
```

Or use environment variables:

```bash
export DATABASE_URL="postgresql://postgres:password@localhost:5432/document_management"
```

### 3. Create PostgreSQL Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE document_management;
```

### 4. Initialize Database Tables

Tables are automatically created when the application starts. No manual migration needed.

### 5. Run Development Server

```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Server will be available at: `http://localhost:8000`

### 6. Access API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Health Check

```http
GET /health
```

Returns service status and version.

**Response (200 OK):**

```json
{
  "status": "healthy",
  "service": "Document Management Service",
  "version": "1.0.0"
}
```

### Upload Document

```http
POST /upload
```

Upload a document and extract text content.

**Parameters:**

- `file` (multipart): Document file (required)
- `document_type` (query): Optional classification (e.g., "listing", "report")
- `property_id` (query): Optional property reference ID

**Supported Formats:**

- PDF (via pdfplumber/PyPDF2)
- DOCX (via python-docx)
- PNG (via Tesseract OCR)
- TXT (plain text)

**Request:**

```bash
curl -X POST "http://localhost:8000/upload?document_type=listing" \
  -F "file=@document.pdf"
```

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Document uploaded and processed successfully",
  "document_id": 1,
  "filename": "document.pdf"
}
```

**Error (400 Bad Request):**

```json
{
  "error": "File format '.xyz' is not supported. Allowed formats: pdf, docx, png, txt"
}
```

### Get Document Metadata

```http
GET /documents/{document_id}
```

Retrieve document metadata by ID.

**Response (200 OK):**

```json
{
  "id": 1,
  "filename": "property_listing.pdf",
  "file_format": "pdf",
  "file_size": 245000,
  "upload_timestamp": "2024-03-23T10:30:45.123456",
  "document_type": "listing",
  "property_id": "PROP123"
}
```

### Get Extracted Text

```http
GET /documents/{document_id}/text
```

Retrieve extracted text content for a document.

**Response (200 OK):**

```json
{
  "id": 1,
  "document_id": 1,
  "raw_text": "Property listing information...",
  "extraction_timestamp": "2024-03-23T10:30:46.234567",
  "extraction_status": "success"
}
```

### Get Document with Text

```http
GET /documents/{document_id}/full
```

Retrieve document metadata along with extracted text.

**Response (200 OK):**

```json
{
  "document": {
    "id": 1,
    "filename": "property_listing.pdf",
    "file_format": "pdf",
    "file_size": 245000,
    "upload_timestamp": "2024-03-23T10:30:45.123456",
    "document_type": "listing",
    "property_id": "PROP123"
  },
  "extracted_text": {
    "id": 1,
    "document_id": 1,
    "raw_text": "Property listing information...",
    "extraction_timestamp": "2024-03-23T10:30:46.234567",
    "extraction_status": "success"
  }
}
```

### List Documents

```http
GET /documents?limit=100&offset=0
```

List all documents with pagination.

**Parameters:**

- `limit` (query): Max documents to return (default: 100, max: 1000)
- `offset` (query): Documents to skip (default: 0)

**Response (200 OK):**

```json
[
  {
    "id": 1,
    "filename": "property_listing.pdf",
    "file_format": "pdf",
    "file_size": 245000,
    "upload_timestamp": "2024-03-23T10:30:45.123456",
    "document_type": "listing",
    "property_id": "PROP123"
  },
  {
    "id": 2,
    "filename": "property_inspection.pdf",
    "file_format": "pdf",
    "file_size": 320000,
    "upload_timestamp": "2024-03-23T10:35:12.567890",
    "document_type": "report",
    "property_id": "PROP123"
  }
]
```

## Database Schema

### documents Table

```sql
CREATE TABLE documents (
  id SERIAL PRIMARY KEY,
  filename VARCHAR(255) NOT NULL,
  file_format VARCHAR(10) NOT NULL,  -- pdf, docx, png, txt
  file_path VARCHAR(500) NOT NULL UNIQUE,
  file_size INTEGER NOT NULL,  -- in bytes
  upload_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  document_type VARCHAR(100),  -- future extensibility
  property_id VARCHAR(100),    -- future extensibility
  INDEX idx_upload_timestamp,
  INDEX idx_property_id
);
```

### extracted_texts Table

```sql
CREATE TABLE extracted_texts (
  id SERIAL PRIMARY KEY,
  document_id INTEGER NOT NULL UNIQUE,
  raw_text TEXT NOT NULL,
  extraction_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  extraction_status VARCHAR(20) NOT NULL DEFAULT 'success',  -- success, failed, partial
  extraction_error TEXT,
  FOREIGN KEY (document_id) REFERENCES documents(id),
  INDEX idx_document_id
);
```

## Service Modules

### upload_service

Main orchestration service that coordinates the upload pipeline.

**Key Methods:**

- `validate_file(filename, file_content)`: Validates file format, size, and content
- `process_upload(filename, file_content, document_type, property_id)`: Orchestrates full upload pipeline

**Features:**

- File type validation (extension + MIME type)
- File size validation (default: 50 MB max)
- Atomicity: Saves file, metadata, AND extracted text or rolls back

### file_storage

Manages persistent file storage on disk.

**Key Methods:**

- `save_file(file_content, original_filename)`: Saves file with unique name
- `read_file(file_path)`: Reads file from disk
- `delete_file(file_path)`: Removes file from storage
- `file_exists(file_path)`: Checks if file exists

**Features:**

- Automatic conflict resolution via timestamp-based unique naming
- Safe file operations with error handling

### text_extraction

Handles format-specific text extraction.

**Key Methods:**

- `extract_text(file_path, file_format)`: Main dispatch method
- `extract_text_from_pdf(file_path)`: PDF extraction (pdfplumber > PyPDF2)
- `extract_text_from_docx(file_path)`: DOCX extraction (includes tables)
- `extract_text_from_png(file_path)`: OCR extraction (Tesseract)
- `extract_text_from_txt(file_path)`: Plain text extraction

**Features:**

- Format-specific optimization (faster PDF extraction with pdfplumber)
- Graceful fallbacks (PyPDF2 if pdfplumber unavailable)
- Page annotations for PDFs ("--- Page N ---")
- Table extraction for DOCX files
- Multiple encoding support for TXT
- Status reporting (success, partial, failed)

### database

Manages all PostgreSQL operations.

**Key Methods:**

- `init_db()`: Create tables if they don't exist
- `save_document(...)`: Save document metadata
- `save_extracted_text(...)`: Save extracted content
- `get_document(document_id)`: Retrieve document by ID
- `get_document_text(document_id)`: Retrieve extracted text
- `get_all_documents(limit, offset)`: List documents with pagination

**Features:**

- Connection pooling and recycling
- Transaction management with rollback
- Pre-ping to verify connections
- Detailed logging

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest tests/ -v

# Run specific test class
pytest tests/__init__.py::TestHealthCheck -v

# Run with coverage
pytest tests/ --cov=services --cov=main
```

### Test Coverage

The test suite includes:

1. **Health Check Tests**: Service status verification
2. **File Storage Tests**: File persistence and retrieval
3. **Text Extraction Tests**: Format-specific extraction
4. **Upload Service Tests**: File validation and pipeline
5. **API Endpoint Tests**: HTTP endpoint functionality
6. **Integration Tests**: End-to-end workflows

### Running a Specific Test

```bash
pytest tests/__init__.py::TestEndToEndUpload::test_full_upload_and_retrieval_flow -v
```

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/document_management

# Application
APP_NAME=Document Management Service
DEBUG=False (set to True for development)
LOG_LEVEL=INFO (DEBUG, WARNING, ERROR also supported)

# File Storage
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=52428800 (50 MB in bytes)

# Logging
LOG_DIR=./logs
```

### Configuration File (config.py)

All settings managed through Pydantic `BaseSettings`:

- Environment variables take precedence
- `.env` file as fallback
- Sensible defaults provided

## Error Handling

### HTTP Status Codes

| Status | Scenario                                                         |
| ------ | ---------------------------------------------------------------- |
| 200    | Success                                                          |
| 400    | Validation error, unsupported format, empty file, file too large |
| 404    | Document not found, extracted text not found                     |
| 500    | Server error, database error, storage error                      |

### Error Response Format

```json
{
  "error": "Descriptive error message"
}
```

## Logging

Application logs to both file and console:

**Log Levels:**

- `DEBUG`: Detailed diagnostic information
- `INFO`: General informational messages
- `WARNING`: Warning messages for suspicious activity
- `ERROR`: Error messages for failures

**Log Location:**

- File: `./logs/app.log` (rotating, 10 MB max, 5 backups)
- Console: stdout

**Example Log Entry:**

```
2024-03-23 10:30:45,123 - services.upload_service - INFO - Successfully extracted text from PDF: property_listing.pdf
```

## Production Deployment

### Recommended Setup

1. **Database**: Use managed PostgreSQL (AWS RDS, Azure Database, etc.)
2. **File Storage**: Consider object storage (AWS S3, Azure Blob Storage) instead of local disk
3. **Application Server**: Use production WSGI server (Gunicorn)
4. **Reverse Proxy**: Nginx for load balancing and SSL
5. **Monitoring**: Prometheus + Grafana for metrics

### Running with Gunicorn

```bash
pip install gunicorn

gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile ./logs/access.log \
  --error-logfile ./logs/error.log
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

## Future Enhancements

- [ ] Object storage integration (S3, Azure Blob)
- [ ] Async file processing with Celery
- [ ] Full-text search across extracted content
- [ ] Document preprocessing (image enhancement, deskewing)
- [ ] Advanced metadata extraction (dates, entities, categories)
- [ ] API authentication and authorization
- [ ] Document versioning support
- [ ] Webhook notifications for processing completion
- [ ] Advanced OCR with layout analysis
- [ ] Document compression and optimization

## Troubleshooting

### Database Connection Error

```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not connect to server
```

**Solutions:**

1. Verify PostgreSQL is running: `psql -U postgres -c "SELECT 1"`
2. Check `DATABASE_URL` environment variable
3. Verify database exists: `psql -l`
4. Check credentials and permissions

### Text Extraction Failures

**PyPDF2/pdfplumber issues:**

- Verify `pip install pdfplumber PyPDF2`
- Check file is actually a valid PDF

**Tesseract OCR issues:**

- Install Tesseract: `brew install tesseract` (macOS) or `apt-get install tesseract-ocr` (Linux)
- Verify installation: `tesseract --version`

**DOCX extraction issues:**

- Verify `pip install python-docx`
- Check file is valid Office format

### File Storage Permissions

```
PermissionError: [Errno 13] Permission denied
```

**Solution:**

- Ensure `./uploads` directory is writable: `chmod 755 ./uploads`

## Performance Considerations

- **Database**: Add indexes on `upload_timestamp` and `property_id` for fast queries
- **Text Extraction**: PDF extraction with pdfplumber is ~3x faster than PyPDF2
- **Concurrent Uploads**: FastAPI handles async operations natively
- **Large Files**: Consider chunked uploads for files >100 MB
- **Storage**: Use SSD for file storage to optimize I/O

## License

Proprietary - Real Estate Analysis Platform

## Support

For issues or questions, contact the development team.
