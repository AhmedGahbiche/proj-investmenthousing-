# Development Guide

Guide for developers working on the Document Management Service.

## Development Environment Setup

### 1. Clone Repository and Install

```bash
cd backend
python -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Database Setup

```bash
# Option 1: Local PostgreSQL
createdb document_management

# Option 2: Docker
docker run --name postgres-dms \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=document_management \
  -p 5432:5432 \
  -d postgres:15
```

### 3. Environment Configuration

Create `.env` file:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/document_management
DEBUG=True
LOG_LEVEL=DEBUG
```

### 4. Run Development Server

```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Server will auto-reload when you modify code.

## Project Structure

```
backend/
├── main.py                    # FastAPI app and endpoints
├── config.py                  # Configuration management
├── models.py                  # SQLAlchemy ORM + Pydantic schemas
├── services/                  # Business logic modules
│   ├── __init__.py
│   ├── upload_service.py      # Upload orchestration
│   ├── file_storage.py        # File persistence
│   ├── text_extraction.py     # Text extraction logic
│   └── database.py            # Database operations
├── tests/                     # Test suite
│   ├── __init__.py           # Contains all tests
│   └── test_upload.py        # Placeholder for additional tests
├── uploads/                   # Uploaded files storage
├── logs/                      # Application logs
└── requirements.txt          # Python dependencies
```

## Module Architecture

### Dependency Flow

```
main.py (FastAPI endpoints)
    ↓
services/upload_service.py (orchestration)
    ├→ services/file_storage.py
    ├→ services/text_extraction.py
    └→ services/database.py
         ↓
    PostgreSQL Database
```

### Module Responsibilities

**main.py:**

- FastAPI application setup
- HTTP endpoints
- Request/response handling
- Error handling

**config.py:**

- Environment variable management
- Settings validation
- Directory initialization

**models.py:**

- SQLAlchemy ORM models (database layer)
- Pydantic schemas (API layer)
- Data validation

**services/upload_service.py:**

- File validation logic
- Upload pipeline orchestration
- Error handling and rollback

**services/file_storage.py:**

- File system operations
- Unique filename generation
- File read/write/delete

**services/text_extraction.py:**

- Format-specific text extraction
- Error handling per format
- Status reporting

**services/database.py:**

- PostgreSQL connection management
- CRUD operations
- Transaction management

## Code Style

### Python Style Guide

Follow PEP 8:

```bash
# Install linter
pip install flake8

# Check style
flake8 services/ main.py models.py config.py
```

### Naming Conventions

- **Functions/Variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: `_leading_underscore`

### Example

```python
class DocumentService:
    """Class for document operations."""

    MAX_FILE_SIZE = 52428800

    def process_document(self, filename: str):
        """Process uploaded document."""
        _internal_helper()
```

## Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test Class

```bash
pytest tests/__init__.py::TestUploadEndpoint -v
```

### Run Specific Test

```bash
pytest tests/__init__.py::TestUploadEndpoint::test_upload_txt_file -v
```

### Test with Coverage

```bash
pytest tests/ --cov=services --cov=main --cov-report=html
```

### Test Organization

Tests are organized by functional areas:

```python
class TestUploadService:
    """Tests for upload_service module"""

    def test_validate_file_success(self):
        """Test successful file validation"""
        ...

    def test_validate_file_unsupported_format(self):
        """Test validation of unsupported format"""
        ...
```

## Adding New Features

### Example: Add NEW HTTP Status Code to Upload

**Step 1: Update models.py**

Add new response type if needed:

```python
class DocumentQuotaExceededResponse(BaseModel):
    success: bool = False
    message: str = "Upload quota exceeded"
```

**Step 2: Update services/upload_service.py**

Add validation:

```python
def process_upload(self, ...):
    if document_count > DAILY_QUOTA:
        return {
            'success': False,
            'error': 'Upload quota exceeded for today'
        }
```

**Step 3: Update main.py**

Add endpoint handling:

```python
@app.post("/upload")
async def upload_document(...):
    result = upload_service.process_upload(...)

    if result['error'] == 'Upload quota exceeded':
        raise HTTPException(
            status_code=429,
            detail=result['error']
        )
```

**Step 4: Add Tests**

```python
def test_upload_quota_exceeded(self):
    """Test rejection when quota exceeded"""
    # Create enough documents to exceed quota
    for i in range(DAILY_QUOTA + 1):
        result = upload_service.process_upload(...)

    assert result['success'] is False
    assert 'quota' in result['error'].lower()
```

### Example: Add NEW File Format Support

**Step 1: Update config.py**

```python
ALLOWED_FORMATS: list = ["pdf", "docx", "png", "txt", "xlsx"]
```

**Step 2: Implement extraction in services/text_extraction.py**

```python
@staticmethod
def extract_text_from_xlsx(file_path: str) -> Tuple[str, str]:
    """Extract text from Excel files."""
    try:
        import openpyxl
        workbook = openpyxl.load_workbook(file_path)

        text_content = []
        for sheet in workbook.sheetnames:
            ws = workbook[sheet]
            text_content.append(f"--- Sheet: {sheet} ---")
            for row in ws.iter_rows(values_only=True):
                row_text = " | ".join(str(cell) for cell in row if cell)
                if row_text.strip():
                    text_content.append(row_text)

        return "\n".join(text_content), "success"
    except Exception as e:
        raise Exception(f"Failed to extract from Excel: {str(e)}")

# Map new format
SUPPORTED_FORMATS = {
    'pdf': 'extract_text_from_pdf',
    'docx': 'extract_text_from_docx',
    'png': 'extract_text_from_png',
    'txt': 'extract_text_from_txt',
    'xlsx': 'extract_text_from_xlsx',  # NEW
}
```

**Step 3: Add tests**

```python
def test_extract_text_from_xlsx(self):
    """Test extracting text from Excel files"""
    # Create test Excel file
    # Extract and verify content
```

## Debugging

### Enable Debug Logging

Set in `.env`:

```env
DEBUG=True
LOG_LEVEL=DEBUG
```

### Add Breakpoints

```python
import pdb

def some_function():
    pdb.set_trace()  # Debugger will pause here
    ...
```

### Check Application Logs

```bash
# Watch log file
tail -f logs/app.log

# Search for errors
grep ERROR logs/app.log
```

### Database Debugging

```python
from services.database import db_service

session = db_service.get_session()
docs = session.query(Document).all()
for doc in docs:
    print(f"ID: {doc.id}, Filename: {doc.filename}")
session.close()
```

## Performance Optimization

### Database Optimization

```python
# Add indexes
class Document(Base):
    __table_args__ = (
        Index('idx_property_id', 'property_id'),
        Index('idx_upload_timestamp', 'upload_timestamp'),
    )
```

### Text Extraction Optimization

Use `pdfplumber` instead of `PyPDF2` for faster PDF extraction:

```python
# pdfplumber: ~100ms for typical PDF
# PyPDF2: ~300ms for same PDF
```

### Caching

Future enhancement: Add caching for frequently accessed documents:

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_document_cached(document_id: int):
    return db_service.get_document(document_id)
```

## Common Issues

### Issue: "UNIQUE constraint failed: documents.file_path"

**Cause:** File already uploaded with same unique name

**Solution:** Filenames are already made unique with timestamps; if this occurs, check for:

- Corrupted file references
- Duplicate uploads in rapid succession

### Issue: "pytesseract.TesseractNotFoundError"

**Cause:** Tesseract OCR not installed

**Solution:**

```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Windows
# Download from https://github.com/UB-Mannheim/tesseract/wiki
```

### Issue: Database connection timeout

**Cause:** PostgreSQL unreachable or credentials wrong

**Solution:**

```bash
# Test connection
psql -U postgres -d document_management -c "SELECT 1"

# Check DATABASE_URL in .env
# Restart PostgreSQL if needed
```

## Git Workflow

### Branch Naming

```
feature/add-ocr-caching
fix/handle-corrupted-pdfs
docs/update-api-documentation
```

### Commit Messages

```
feat: Add OCR caching for image documents
fix: Handle corrupted PDF files gracefully
docs: Update API documentation
test: Add tests for Excel extraction
```

### Pre-commit Checklist

- [ ] Tests pass: `pytest tests/ -v`
- [ ] Code style OK: `flake8 .`
- [ ] No debug statements left
- [ ] Docstrings added/updated
- [ ] README updated if needed
- [ ] No credentials in commits

## Documentation

### Docstring Format

Use Google-style docstrings:

```python
def extract_text(file_path: str, file_format: str) -> Tuple[str, str]:
    """
    Extract text from document.

    Supports PDF, DOCX, PNG, TXT formats with format-specific
    optimization and error handling.

    Args:
        file_path: Path to the file
        file_format: File format (pdf, docx, png, txt)

    Returns:
        Tuple of (extracted_text, status) where status is one of:
        - 'success': Full text extracted
        - 'partial': Some text extracted
        - 'failed': Extraction failed

    Raises:
        Exception: If unsupported format or extraction error

    Example:
        >>> text, status = extract_text('doc.pdf', 'pdf')
        >>> print(f"Status: {status}")
        Status: success
    """
```

## Release Process

### Version Bumping

Update in `config.py`:

```python
APP_VERSION: str = "1.1.0"  # Major.Minor.Patch
```

### Release Notes

Create CHANGELOG.md entry:

```markdown
## [1.1.0] - 2024-03-23

### Added

- Excel format support
- OCR caching for images
- Webhook notifications

### Fixed

- Handle corrupted PDF files gracefully

### Changed

- Improved text extraction performance
```

## Getting Help

- Check [README.md](README.md) for architecture overview
- See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for endpoint details
- Review [QUICKSTART.md](QUICKSTART.md) for setup help
- Check logs in `logs/` directory
- Review test cases in `tests/` for usage examples

## Future Improvements

Tracked in issue tracker:

- [ ] Add async file processing with Celery
- [ ] Implement document versioning
- [ ] Add full-text search capability
- [ ] Implement API authentication (OAuth2/JWT)
- [ ] Add webhook support
- [ ] Implement document compression
- [ ] Add advanced OCR with layout preservation
- [ ] Support for cloud storage (S3, Azure Blob)

## Contributing

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes with tests: `pytest tests/`
3. Ensure style compliance: `flake8 .`
4. Commit with descriptive message
5. Push and create pull request

For significant changes, open an issue first for discussion.
