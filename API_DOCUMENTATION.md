# API Documentation

Complete reference for the Document Management Service REST API.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently no authentication required. In production, implement JWT or OAuth2.

## Response Formats

All responses are JSON.

### Success Response

```json
{
  "success": true,
  "message": "Operation successful",
  "data": {}
}
```

### Error Response

```json
{
  "error": "Error description",
  "status": 400
}
```

## Endpoints

### 1. Health Check

Check if service is running.

**Endpoint:**

```http
GET /health
```

**Response (200 OK):**

```json
{
  "status": "healthy",
  "service": "Document Management Service",
  "version": "1.0.0"
}
```

**Example:**

```bash
curl http://localhost:8000/health
```

---

### 2. Upload Document

Upload a document for storage and text extraction.

**Endpoint:**

```http
POST /upload
```

**Parameters:**

| Name          | Type   | Location         | Required | Description                                |
| ------------- | ------ | ---------------- | -------- | ------------------------------------------ |
| file          | file   | body (multipart) | Yes      | Document file (PDF, DOCX, PNG, TXT)        |
| document_type | string | query            | No       | Classification (e.g., "listing", "report") |
| property_id   | string | query            | No       | Property reference ID                      |

**Supported File Formats:**

- `pdf` - PDF documents
- `docx` - Microsoft Word documents
- `png` - PNG images (with OCR)
- `txt` - Plain text files

**Constraints:**

- Max file size: 50 MB
- Empty files: Not allowed
- Unsupported formats: Rejected

**Request:**

```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@document.pdf"
```

With metadata:

```bash
curl -X POST "http://localhost:8000/upload?document_type=listing&property_id=PROP001" \
  -F "file=@property_listing.pdf"
```

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Document uploaded and processed successfully",
  "document_id": 1,
  "filename": "property_listing.pdf"
}
```

**Error Response (400 Bad Request):**

```json
{
  "error": "File format '.xyz' is not supported. Allowed formats: pdf, docx, png, txt"
}
```

**Possible Errors:**
| Status | Error |
|--------|-------|
| 400 | File is empty |
| 400 | File format not supported |
| 400 | File exceeds maximum size |
| 400 | Filename is empty or invalid |
| 405 | File validation failed |
| 500 | Server error during processing |

---

### 3. Get Document Metadata

Retrieve document information by ID.

**Endpoint:**

```http
GET /documents/{document_id}
```

**Parameters:**

| Name        | Type    | Location | Required | Description |
| ----------- | ------- | -------- | -------- | ----------- |
| document_id | integer | path     | Yes      | Document ID |

**Request:**

```bash
curl http://localhost:8000/documents/1
```

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

**Error Response (404 Not Found):**

```json
{
  "error": "Document with ID 999 not found"
}
```

---

### 4. Get Extracted Text

Retrieve text extracted from a document.

**Endpoint:**

```http
GET /documents/{document_id}/text
```

**Parameters:**

| Name        | Type    | Location | Required | Description |
| ----------- | ------- | -------- | -------- | ----------- |
| document_id | integer | path     | Yes      | Document ID |

**Request:**

```bash
curl http://localhost:8000/documents/1/text
```

**Response (200 OK):**

```json
{
  "id": 1,
  "document_id": 1,
  "raw_text": "Property Details:\nLocation: 123 Main Street\nPrice: $500,000\nBedrooms: 3\nBathrooms: 2",
  "extraction_timestamp": "2024-03-23T10:30:46.234567",
  "extraction_status": "success"
}
```

**Extraction Status Values:**

- `success` - Text successfully extracted
- `partial` - Some text extracted, but may be incomplete
- `failed` - Text extraction failed

**Extra Fields (when status != success):**

```json
{
  "id": 2,
  "document_id": 2,
  "raw_text": "",
  "extraction_timestamp": "2024-03-23T10:35:12.345678",
  "extraction_status": "failed",
  "extraction_error": "PDF is corrupted or encrypted"
}
```

**Error Response (404 Not Found):**

```json
{
  "error": "Extracted text not found for document ID 999"
}
```

---

### 5. Get Document with Extracted Text

Retrieve both document metadata and extracted text in one request.

**Endpoint:**

```http
GET /documents/{document_id}/full
```

**Parameters:**

| Name        | Type    | Location | Required | Description |
| ----------- | ------- | -------- | -------- | ----------- |
| document_id | integer | path     | Yes      | Document ID |

**Request:**

```bash
curl http://localhost:8000/documents/1/full
```

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
    "raw_text": "Property Details...",
    "extraction_timestamp": "2024-03-23T10:30:46.234567",
    "extraction_status": "success"
  }
}
```

**When text extraction failed:**

```json
{
  "document": {
    "id": 2,
    "filename": "corrupted.pdf",
    ...
  },
  "extracted_text": null
}
```

---

### 6. List Documents

List all documents with pagination.

**Endpoint:**

```http
GET /documents
```

**Parameters:**

| Name   | Type    | Location | Required | Default | Description                      |
| ------ | ------- | -------- | -------- | ------- | -------------------------------- |
| limit  | integer | query    | No       | 100     | Max documents to return (1-1000) |
| offset | integer | query    | No       | 0       | Documents to skip                |

**Request:**

```bash
# Get first 10 documents
curl "http://localhost:8000/documents?limit=10&offset=0"

# Get next 10 documents
curl "http://localhost:8000/documents?limit=10&offset=10"

# Get all (up to 1000)
curl "http://localhost:8000/documents?limit=1000"
```

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
    "filename": "inspection_report.docx",
    "file_format": "docx",
    "file_size": 125000,
    "upload_timestamp": "2024-03-23T10:35:12.567890",
    "document_type": "report",
    "property_id": "PROP123"
  }
]
```

**Empty Response (200 OK):**

```json
[]
```

---

## HTTP Status Codes

| Code | Meaning      | When It Occurs                                     |
| ---- | ------------ | -------------------------------------------------- |
| 200  | OK           | Successful request                                 |
| 400  | Bad Request  | Validation error, invalid file, unsupported format |
| 404  | Not Found    | Document doesn't exist                             |
| 500  | Server Error | Database error, storage error, extraction error    |

## Rate Limiting

Currently not implemented. To be added in production.

## Pagination

Use `limit` and `offset` for pagination:

```bash
# Page 1 (items 0-9)
curl "http://localhost:8000/documents?limit=10&offset=0"

# Page 2 (items 10-19)
curl "http://localhost:8000/documents?limit=10&offset=10"

# Page 3 (items 20-29)
curl "http://localhost:8000/documents?limit=10&offset=20"
```

## Common Workflows

### Complete Upload Workflow

```bash
#!/bin/bash

# 1. Upload document
UPLOAD=$(curl -s -X POST "http://localhost:8000/upload?document_type=listing" \
  -F "file=@property.pdf")

DOC_ID=$(echo $UPLOAD | jq '.document_id')
echo "Uploaded Document ID: $DOC_ID"

# 2. Retrieve metadata
curl -s "http://localhost:8000/documents/$DOC_ID" | jq .

# 3. Get extracted text
curl -s "http://localhost:8000/documents/$DOC_ID/text" | jq .raw_text

# 4. Get everything together
curl -s "http://localhost:8000/documents/$DOC_ID/full" | jq .

# 5. List all documents
curl -s "http://localhost:8000/documents?limit=5" | jq .
```

### Batch Upload

```bash
#!/bin/bash

for file in *.pdf; do
  echo "Uploading $file..."
  curl -X POST "http://localhost:8000/upload" \
    -F "file=@$file"
  sleep 1
done
```

### Search Recently Uploaded Documents

```bash
# Get last 10 documents (ordered by upload timestamp)
curl "http://localhost:8000/documents?limit=10&offset=0" | jq '.[] | {id, filename, upload_timestamp}'
```

## Error Handling Examples

### Example 1: Upload Unsupported Format

**Request:**

```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@document.exe"
```

**Response (400 Bad Request):**

```json
{
  "error": "File format '.exe' is not supported. Allowed formats: pdf, docx, png, txt"
}
```

### Example 2: Document Not Found

**Request:**

```bash
curl "http://localhost:8000/documents/99999"
```

**Response (404 Not Found):**

```json
{
  "error": "Document with ID 99999 not found"
}
```

### Example 3: File Too Large

**Request:**

```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@huge_file.pdf"  # 100 MB file
```

**Response (400 Bad Request):**

```json
{
  "error": "File size exceeds maximum allowed size (50.0 MB)"
}
```

## Client Libraries

### Python (requests)

```python
import requests

# Upload
with open('document.pdf', 'rb') as f:
    files = {'file': f}
    params = {'document_type': 'listing', 'property_id': 'PROP001'}
    response = requests.post(
        'http://localhost:8000/upload',
        files=files,
        params=params
    )
    doc_id = response.json()['document_id']

# Retrieve
response = requests.get(f'http://localhost:8000/documents/{doc_id}')
metadata = response.json()

# Get text
response = requests.get(f'http://localhost:8000/documents/{doc_id}/text')
text = response.json()['raw_text']
```

### JavaScript (fetch)

```javascript
// Upload
const formData = new FormData();
formData.append("file", fileInput.files[0]);

const response = await fetch(
  "http://localhost:8000/upload?document_type=listing",
  {
    method: "POST",
    body: formData,
  },
);

const result = await response.json();
console.log("Document ID:", result.document_id);

// Retrieve
const docResponse = await fetch(
  `http://localhost:8000/documents/${result.document_id}`,
);
const metadata = await docResponse.json();
console.log("Metadata:", metadata);
```

### cURL

See examples throughout this document.

## Webhooks (Future)

Planned: Notify client when document processing completes.

```http
POST /webhooks/register
```

## Versioning

Current API version: 1.0

- Path: `/api/v1/upload` (future)

## CORS (Future)

CORS headers will be added for cross-origin requests in production.

## Support

For API support, refer to [README.md](README.md) or contact development team.
