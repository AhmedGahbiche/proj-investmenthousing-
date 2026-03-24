# Quick Start Guide

Get the Document Management Service running in 5 minutes.

## Prerequisites

- Python 3.10 or higher
- PostgreSQL 12 or higher
- pip (Python package manager)

## Quick Start

### 1. Install Dependencies (1 minute)

```bash
cd backend
pip install -r requirements.txt
```

### 2. Set Up Database (2 minutes)

**Create PostgreSQL Database:**

```bash
# Open PostgreSQL terminal
psql -U postgres

# Create database
CREATE DATABASE document_management;

# Exit
\q
```

**Or use docker:**

```bash
docker run --name postgres-dms \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=document_management \
  -p 5432:5432 \
  -d postgres:15
```

### 3. Verify Database Connection (1 minute)

```bash
# Test connection
psql -U postgres -d document_management -c "SELECT 1;"

# Should output: "1"
```

### 4. Run the Application (1 minute)

```bash
# Start development server
python -m uvicorn main:app --reload

# Server runs at: http://localhost:8000
```

### 5. Test with a Sample Upload

**Open in browser:**

```
http://localhost:8000/docs
```

**Or use curl:**

```bash
# Create a test file
echo "This is a test real estate document." > test.txt

# Upload it
curl -X POST "http://localhost:8000/upload?document_type=listing" \
  -F "file=@test.txt"

# Response:
# {
#   "success": true,
#   "message": "Document uploaded and processed successfully",
#   "document_id": 1,
#   "filename": "test.txt"
# }
```

## Common Tasks

### Upload a PDF Document

```bash
curl -X POST "http://localhost:8000/upload?document_type=report&property_id=PROP001" \
  -F "file=@property_inspection.pdf"
```

### Retrieve Document Information

```bash
curl "http://localhost:8000/documents/1"
```

### Get Extracted Text

```bash
curl "http://localhost:8000/documents/1/text"
```

### List All Documents

```bash
curl "http://localhost:8000/documents?limit=20"
```

## API Documentation

**Interactive API Docs:** http://localhost:8000/docs
**Alternative Docs:** http://localhost:8000/redoc

## Run Tests

```bash
# Install test dependencies (included in requirements.txt)
pytest tests/ -v

# Single test
pytest tests/__init__.py::TestUploadEndpoint::test_upload_txt_file -v
```

## Troubleshooting

### Database Connection Error

**Problem:** `FATAL: Ident authentication failed for user "postgres"`

**Solution:**

```bash
# Use password authentication instead
psql -U postgres -h localhost
```

### Port Already in Use

**Problem:** `Address already in use`

**Solution:**

```bash
# Run on different port
python -m uvicorn main:app --port 8001
```

### Missing Dependencies

**Problem:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**

```bash
pip install -r requirements.txt
```

### OCR Not Working

**Problem:** `pytesseract.TesseractNotFoundError`

**Solution:**

- macOS: `brew install tesseract`
- Ubuntu: `apt-get install tesseract-ocr`
- Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki

## Next Steps

1. Check out the [README.md](README.md) for complete documentation
2. Explore the API at http://localhost:8000/docs
3. Configure settings in `.env`
4. Deploy to production using Gunicorn + Nginx
5. Integrate with your frontend application

## Example: Complete Upload Workflow

```bash
#!/bin/bash

# 1. Create a sample document
cat > sample_property.txt << EOF
Property Listing: 123 Main Street
Price: $500,000
Bedrooms: 3
Bathrooms: 2
Square Feet: 2,500
Description: Beautiful home in quiet neighborhood
EOF

# 2. Upload document
RESPONSE=$(curl -s -X POST "http://localhost:8000/upload?document_type=listing&property_id=PROP123" \
  -F "file=@sample_property.txt")

echo "Upload Response: $RESPONSE"

# 3. Extract document_id from response
DOCUMENT_ID=$(echo $RESPONSE | grep -o '"document_id":[0-9]*' | grep -o '[0-9]*')

echo "Document ID: $DOCUMENT_ID"

# 4. Retrieve document metadata
echo -e "\n--- Document Metadata ---"
curl -s "http://localhost:8000/documents/$DOCUMENT_ID" | jq .

# 5. Retrieve extracted text
echo -e "\n--- Extracted Text ---"
curl -s "http://localhost:8000/documents/$DOCUMENT_ID/text" | jq .raw_text

# 6. List all documents
echo -e "\n--- All Documents ---"
curl -s "http://localhost:8000/documents" | jq .
```

Run with:

```bash
bash workflow.sh
```

## Support

For more details, see [README.md](README.md)
