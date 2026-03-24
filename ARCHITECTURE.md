# System Architecture & How Things Work

This document explains how all the pieces fit together in the document management system.

---

## Overview: The Big Picture

```
Your Computer          Your Server Process                Database
┌──────────────┐      ┌─────────────────────────┐       ┌──────────┐
│   Browser    │      │ FastAPI Server          │       │PostgreSQL│
│ or Client    │      │ (processes requests)    │       │(stores   │
└──────────────┘      │                         │       │ data)    │
       │              │  ┌─────────────────┐   │       └──────────┘
       │──upload──────→  │ Upload Service  │   │             ▲
       │              │  └─────────────────┘   │             │
       │              │         │              │             │
       │              │         ├→Text Extract │─save─→      │
       │              │         │              │             │
       │              │         ├→Vector Index │─save─→      │
       │              │         │              │             │
       │              │  ┌─────────────────┐   │             │
       │              │  │Database Service │──→─(queries)    │
       │              │  └─────────────────┘   │             │
       │              │                         │             │
       │──search──────→  Search Endpoints       │             │
       │              │  (uses FAISS + AI)      │             │
       │              │                         │             │
       │←─results─────│  Return JSON response   │             │
       │              │                         │             │
       └──────────────┘      └─────────────────────────┘       └──────────┘
```

---

## Component Breakdown

### 1. **FastAPI Application** (main.py)

**What it does:** Receives HTTP requests (like a receptionist), routes them to the right handler, and sends back responses.

**Key concepts:**

- **Endpoint:** A specific URL path that does something
  - `/upload` - upload files
  - `/search` - search documents
  - `/documents/1` - get document info
- **HTTP Methods:**
  - GET: retrieve information
  - POST: send data and get back a result

**Flow:**

```
User sends request → FastAPI routes it → Service handles it → Response sent back
```

**Example:**

```python
@app.post("/upload")
async def upload_document(file: UploadFile):
    # This function runs when someone sends a POST request to /upload
    result = upload_service.process_upload(...)
    return result
```

---

### 2. **Upload Service** (services/upload_service.py)

**What it does:** Orchestrates the entire upload process (controls the flow).

**6-Step Process:**

```
Step 1: Validate File
├─ Check filename isn't empty
├─ Check file size ≤ MAX_FILE_SIZE_MB
├─ Check file type is in ALLOWED_FORMATS
└─ ✓ Passes: continue, ✗ Fails: return error

Step 2: Save File to Disk
├─ Create unique filename (add timestamp to prevent conflicts)
├─ Save to ./uploads/ folder
└─ Remember the file path

Step 3: Save to Database
├─ Create Document record
├─ Store: filename, size, type, upload time
└─ Get back the document_id (unique number)

Step 4: Extract Text
├─ Determine file type (.pdf, .docx, .png, .txt)
├─ Use appropriate extractor
├─ Get raw text from file
└─ Note: if fails, continue anyway (non-blocking)

Step 5: Save Extracted Text
├─ Create ExtractedText record
├─ Store: raw text, extraction status, any errors
└─ Link to document_id

Step 6: Create Vector Embeddings
├─ If text was extracted successfully:
│  ├─ Call vector_service.embed_document()
│  ├─ Save embedding metadata
│  └─ Document is now searchable
└─ If fails: log warning but don't block upload
```

**Code structure:**

```python
class UploadService:
    def validate_file(filename, content):
        # Check if file is valid

    def process_upload(filename, content, document_type):
        # Orchestrates the 6 steps above
        # Returns {"success": true/false, "document_id": X, ...}
```

---

### 3. **File Storage** (services/file_storage.py)

**What it does:** Saves files to disk with unique names.

**Why unique names?** If two people upload files named "report.pdf", we need to prevent overwriting.

**Solution:** Add timestamp and random number

```
report.pdf → report_20240323_142530_a8f3k.pdf
           └─ timestamp added ─┘
```

**How it works:**

```python
def save_file(content, original_filename):
    # Extract extension (.pdf, .docx, etc.)
    # Generate unique filename with timestamp
    # Save to uploads/ folder
    # Return file path
```

---

### 4. **Text Extraction** (services/text_extraction.py)

**What it does:** Reads text from different file types.

**Supported formats:**

| Format              | Tool Used   | How It Works                                   |
| ------------------- | ----------- | ---------------------------------------------- |
| PDF                 | pdfplumber  | Reads text directly from PDF structure         |
| Word (.docx)        | python-docx | Extracts text from Word file (basically a ZIP) |
| Images (.png, .jpg) | pytesseract | OCR - recognizes text in images                |
| Text (.txt)         | Built-in    | Reads directly, no special handling            |

**Example:**

```python
def extract_text(file_path, file_type):
    if file_type == 'pdf':
        return extract_pdf(file_path)
    elif file_type == 'docx':
        return extract_docx(file_path)
    elif file_type == 'png':
        return extract_image_ocr(file_path)
    # etc.
```

---

### 5. **Vector Service** (services/vector_service.py)

**What it does:** Converts text to mathematical vectors (lists of numbers) that represent meaning.

**Why?** Computers can't understand languages naturally. We need to convert text to numbers. These numbers capture the "meaning" of the text so we can compare meanings.

**The Process:**

#### Step 1: Chunk Text (Break into pieces)

Why? Long documents can't be processed all at once. Breaking into chunks allows precise searching.

```
Original text: "Beautiful 4-bedroom home with modern kitchen.
               Large backyard with mature trees..."

Chunks (512 chars each, 50-char overlap):
├─ "Beautiful 4-bedroom home with modern kitchen. Large backyard with..."
├─ "...Large backyard with mature trees. Stone patio ideal..."
└─ "..."
```

**Overlap purpose:** Prevents cutting context

```
Without overlap:
"...home with" | "modern kitchen..." ← Breaks at word

With overlap (50 chars):
"...home with modern ki" | "ki...kitchen..." ← Context preserved
```

#### Step 2: Generate Embeddings (Convert to numbers)

Using an AI model (all-MiniLM-L6-v2):

```
Input text: "Beautiful modern kitchen"
                    ↓
            [AI Model Processing]
                    ↓
Output: 384-dimensional vector
[0.234, 0.105, -0.089, 0.456, ... (384 numbers total) ... 0.012]

This vector captures the "meaning" of the text.
Similar texts get similar vectors.
```

**Why 384 dimensions?** The model produces 384 numbers. Each represents some aspect of the meaning.

#### Step 3: Store in FAISS Index

FAISS = Facebook AI Similarity Search

Instead of storing text, store the vectors for fast searching:

```
Document 1
├─ Chunk 1 → [0.234, 0.105, -0.089, ...] → stored in FAISS
├─ Chunk 2 → [0.156, 0.234, 0.089, ...] → stored in FAISS
└─ Chunk 3 → [0.401, -0.102, 0.301, ...] → stored in FAISS

Document 2
├─ Chunk 1 → [0.245, 0.110, -0.088, ...] → stored in FAISS
└─ Chunk 2 → [0.165, 0.240, 0.090, ...] → stored in FAISS
```

**What FAISS does:** When you search, it converts your query to a vector, then finds the most similar vectors in its index.

---

### 6. **Vector Index Manager** (services/vector_index.py)

**What it does:** Manages the FAISS indices (the search databases).

**Key responsibilities:**

```
┌─ Create Index
│  └─ Set up a new FAISS index for a document
│
├─ Add Vectors
│  ├─ Insert embeddings into index
│  ├─ Track chunk IDs and original text
│  └─ Enable fast searching
│
├─ Search
│  ├─ Single document: search within one document
│  └─ Cross-document: search across all documents
│
├─ Save/Load
│  ├─ Save to disk (for persistence - so data survives restarts)
│  └─ Load from disk (recover on startup)
│
└─ Delete
   └─ Remove indices when document is deleted
```

**How searching works:**

```
Query: "modern kitchen"
       ↓
[AI Model] Converts to vector: [0.198, 0.234, 0.067, ...]
       ↓
[FAISS] Searches for nearest vectors
       ├─ Could search in one document (faster)
       └─ Could search all documents (comprehensive)
       ↓
Returns: Chunk IDs + distances (how different they are)
       ↓
Distance = 0.156 → similarity_score = 1/(1+0.156) = 0.865 (86.5% match)
Distance = 0.234 → similarity_score = 1/(1+0.234) = 0.810 (81.0% match)
```

---

### 7. **Database Service** (services/database.py)

**What it does:** Handles all communication with PostgreSQL.

**Database Tables:**

#### Document Table

```sql
CREATE TABLE documents (
    id INTEGER PRIMARY KEY,           -- Document ID
    filename VARCHAR(255),            -- Original filename
    file_format VARCHAR(10),          -- pdf, docx, txt, png
    file_path VARCHAR(500),           -- Where it's saved on disk
    file_size INTEGER,                -- Size in bytes
    document_type VARCHAR(50),        -- classification (optional)
    property_id VARCHAR(50),          -- Reference to property (optional)
    upload_date TIMESTAMP             -- When uploaded
);
```

#### ExtractedText Table

```sql
CREATE TABLE extracted_texts (
    id INTEGER PRIMARY KEY,
    document_id INTEGER,              -- Links to document
    raw_text TEXT,                    -- The extracted text
    extraction_status VARCHAR(50),    -- success, failed, partial
    extraction_error VARCHAR(500),    -- Error message if failed
    FOREIGN KEY (document_id)         -- Must be a valid document
);
```

#### VectorEmbedding Table

```sql
CREATE TABLE vector_embeddings (
    id INTEGER PRIMARY KEY,
    document_id INTEGER UNIQUE,       -- Links to document (one per doc)
    num_chunks INTEGER,               -- How many chunks created
    embedding_model VARCHAR(100),     -- Model name used
    chunk_size INTEGER,               -- Size of chunks (512)
    chunk_overlap INTEGER,            -- Overlap between chunks (50)
    embedding_timestamp TIMESTAMP,    -- When embeddings created
    FOREIGN KEY (document_id)         -- Must be valid document
);
```

**What we track:** We don't store the actual vectors in the database (too much data). We store metadata saying which document has embeddings. The actual vectors are in the FAISS index on disk.

---

## Data Flow: Complete Upload + Search Example

### Scenario: Upload a Real Estate Listing, Then Search It

```
1. USER UPLOADS PROPERTY_LISTING.PDF (500 KB)
   ↓

2. FASTAPI RECEIVES REQUEST
   - Validates file (is it under 50 MB? Is it a PDF?)
   - ✓ Passes validation
   ↓

3. FILE STORAGE SERVICE
   - Generates unique name: property_listing_20240323_152530_xyz.pdf
   - Saves to disk: ./uploads/property_listing_20240323_152530_xyz.pdf
   - Returns: file path
   ↓

4. DATABASE SERVICE
   - Creates document record
   - Columns: filename, file_format (pdf), file_path, file_size (500000), upload_date (now)
   - Returns: document_id = 5
   ↓

5. TEXT EXTRACTION SERVICE
   - Reads PDF file using pdfplumber
   - Extracts all text:
     "Beautiful 4-bedroom home in downtown. Modern kitchen with granite
      counters. Master suite with spa bathroom. Large backyard with
      mature oak trees. Updated HVAC and roof. Close to schools and
      shopping. $450,000"
   - Returns: extracted_text + status (success)
   ↓

6. DATABASE SERVICE
   - Creates extracted_text record
   - Stores: raw_text, extraction_status (success)
   - Links: document_id = 5
   ↓

7. VECTOR SERVICE
   - Chunks text (512 char chunks, 50 char overlap):
     Chunk 1: "Beautiful 4-bedroom home in downtown. Modern kitchen with
              granite counters. Master suite..."
     Chunk 2: "Master suite with spa bathroom. Large backyard with mature
              oak trees. Updated HVAC..."
   - Generates embeddings using sentence-transformers:
     Chunk 1 → [0.234, 0.156, -0.089, ..., 0.012] (384 numbers)
     Chunk 2 → [0.245, 0.167, -0.095, ..., 0.018] (384 numbers)
   - Returns: embeddings + chunk IDs
   ↓

8. VECTOR INDEX MANAGER
   - Creates FAISS index for document 5
   - Adds vectors to index
   - Saves to disk: ./vector_indices/document_5.index
   ↓

9. DATABASE SERVICE
   - Creates vector_embedding record
   - Stores: document_id=5, num_chunks=2, embedding_model=all-MiniLM-L6-v2, chunk_size=512
   ↓

✓ UPLOAD COMPLETE - Document is now searchable!

═══════════════════════════════════════════════════════════════

NOW USER SEARCHES: "modern updated home with large yard"
   ↓

10. FASTAPI RECEIVES SEARCH REQUEST
    - Query: "modern updated home with large yard"
    - document_id: 5
    - k: 5 (return 5 results max)
    ↓

11. VECTOR SERVICE
    - Converts query to embedding:
      Query → [0.240, 0.160, -0.091, ..., 0.015] (384 numbers)
    ↓

12. VECTOR INDEX MANAGER
    - Takes query embedding
    - Searches FAISS index for document 5
    - Compares to stored vectors:
      - Chunk 1 distance: 0.145 ← Very similar (small distance)
      - Chunk 2 distance: 0.234 ← Less similar (larger distance)
    ↓

13. CONVERT TO SIMILARITY SCORES
    - Distance 0.145 → similarity = 1/(1+0.145) = 0.873 (87.3% match)
    - Distance 0.234 → similarity = 1/(1+0.234) = 0.810 (81.0% match)
    ↓

14. RETURN RESULTS (ranked by similarity)
    [
      {
        "rank": 1,
        "chunk_id": "chunk_1",
        "distance": 0.145,
        "similarity_score": 0.873  ← Better match
      },
      {
        "rank": 2,
        "chunk_id": "chunk_2",
        "distance": 0.234,
        "similarity_score": 0.810  ← Lesser match
      }
    ]

✓ SEARCH COMPLETE!
```

---

## Performance Characteristics

### Upload Performance

```
500 KB PDF
  ├─ Validate: <10ms
  ├─ Save to disk: 50-100ms
  ├─ Extract text: 500-2000ms (depends on PDF complexity)
  ├─ Save to database: 10-50ms
  └─ Generate embeddings: 2000-5000ms

Total: ~3-7 seconds
```

### Search Performance

```
Single Document (1000 chunks)
  ├─ Convert query to embedding: 100-200ms
  └─ Search FAISS: 10-50ms
  Total: ~150ms

Cross-Document (50 documents, 50000 total chunks)
  ├─ Convert query to embedding: 100-200ms
  └─ Search all FAISS indices: 200-500ms
  Total: ~500ms
```

### Storage Usage

```
Per Document (500 KB original)
  ├─ Stored PDF: 500 KB
  ├─ Extracted text: ~50 KB (text only)
  ├─ Embeddings (100 chunks): 100 chunks × 384 floats × 4 bytes = 153.6 KB
  ├─ Database metadata: ~2 KB
  └─ Total: ~700 KB on disk
```

---

## Error Handling

### Non-Blocking Errors

These don't stop the upload:

1. **Text extraction fails** → Document saved, just not searchable

   ```
   Upload still succeeds, but vector embedding skipped
   ```

2. **Vector embedding fails** → Document saved and extractable, just not AI-searchable
   ```
   User can still read extracted text, can't use semantic search
   ```

### Blocking Errors

These stop the upload:

1. **File validation fails** → File rejected (bad size, type)
2. **File save fails** → Disk issue, whole upload fails
3. **Database save fails** → Database issue, whole upload fails

### Error Response Example

```json
{
  "success": false,
  "document_id": null,
  "filename": "myfile.pdf",
  "message": "File validation failed",
  "error": "File size (60 MB) exceeds maximum allowed (50 MB)"
}
```

---

## Security Considerations

### What's Implemented

1. **File type validation** - Only allowed formats accepted
2. **File size limits** - Prevents denial of service (filling up disk)
3. **Unique filenames** - Prevents accidental overwrites
4. **Database password protection** - PostgreSQL user authentication
5. **Logging** - All operations recorded for audit trails

### What's NOT Implemented (Add Later)

1. **User authentication** - Anyone can upload (add login system)
2. **Encryption** - Files not encrypted on disk
3. **Access control** - No permissions by user
4. **HTTPS/TLS** - Communication not encrypted (add SSL certificate)

### Recommendations for Production

```
1. Add user authentication (JWT tokens, OAuth)
2. Enable HTTPS (SSL/TLS certificate)
3. Encrypt files at rest (pgcrypto for database, LUKS for filesystem)
4. Add rate limiting (prevent huge uploads spam)
5. Implement audit logging (track who accessed what)
6. Regular backups (database and file storage)
7. Database access controls (firewall, VPC in cloud)
```

---

## Scaling Considerations

### Current Limits (FAISS-based)

- ✓ Works well up to: 100,000 documents
- ⚠️ Performance degrades at: 500,000+ documents
- ✗ Not suitable for: 10M+ documents

### When to Upgrade

**If you have 100K+ documents, upgrade to:**

```
Frontend ↓
    ↓
FastAPI Server (can stay same)
    ↓
    ├─ PostgreSQL (keep for metadata)
    └─ Qdrant Vector Database ← Replace FAISS here
         (professional vector database, scales to billions)
```

**Code change needed:** Only replace `vector_index.py` — rest of code stays identical!

---

## Testing Strategy

### Unit Tests (Test individual components)

```python
# Test text chunking
chunks = vector_service.chunk_text("text...", chunk_size=512)
assert len(chunks) > 0

# Test embedding generation
embeddings = vector_service.generate_embeddings(["text1", "text2"])
assert embeddings.shape == (2, 384)
```

### Integration Tests (Test components working together)

```python
# Test full upload process
result = upload_service.process_upload("file.pdf", content, "listing")
assert result['success'] == True
assert result['document_id'] > 0
```

### Smoke Tests (Quick checks)

```python
# Just verify core imports work
from services.vector_service import vector_service
from services.database import db_service
```

---

## Configuration & Customization

### Key Settings in .env

```ini
# Chunk size: smaller (256) = more detail, larger (1024) = more context
CHUNK_SIZE=512

# Overlap: larger (100) = prevent missed content, smaller (10) = faster
CHUNK_OVERLAP=50

# Default search results: higher (20) = more options, lower (5) = faster
DEFAULT_K=5

# Search result limit: higher (20) = more thorough, lower (10) = faster
MAX_K=20
```

### Swappable Components

Modular design means you can swap things easily:

```
# Swap database
Change DATABASE_URL → PostgreSQL, SQLite, MySQL, etc.

# Swap embedding model
Change model_name in VectorService → use different AI model

# Swap vector index
Replace vector_index.py → use Qdrant, Milvus, Weaviate, etc.

# Swap file storage
Replace file_storage.py → use S3, GCS, Azure Blob, etc.
```

The API endpoints stay the same!

---

## Next Steps

This architecture is production-ready for MVP (Minimum Viable Product - the basic working version).

For production scale:

1. Monitor logs for performance bottlenecks
2. Set up database backups
3. Add user authentication
4. Configure HTTPS/SSL
5. Plan migration to Qdrant when you reach 100K+ documents

---

## Reference Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      CLIENT APPLICATION                        │
│  (Web frontend, mobile app, desktop client, API consumer)       │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP Requests
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FASTAPI SERVER                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ API Endpoints                                            │  │
│  │ ├─ POST /upload          (Upload Document)              │  │
│  │ ├─ GET  /documents       (List Documents)               │  │
│  │ ├─ GET  /documents/{id}  (Get Document Info)            │  │
│  │ ├─ GET  /documents/{id}/text (Get Extracted Text)       │  │
│  │ ├─ POST /search/document/{id} (Search Within Document)  │  │
│  │ └─ POST /search          (Search All Documents)         │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────┬───────────────────────────────────────────────────┘
             │
    ┌────────┴────────┬────────────┬─────────────┐
    ▼                 ▼            ▼             ▼
┌──────────────┐ ┌──────────────┐  ┌──────────────┐  ┌─────────────┐
│Upload Service│ │File Storage  │  │Text Extraction   │Database Srvc│
│              │ │              │  │                  │             │
│Coordinates:  │ │Saves files   │  │Reads content:    │Stores:      │
│1. Validate   │ │to disk with  │  │- PDF (complex)   │- Metadata   │
│2. Save file  │ │unique names  │  │- Word (docx)     │- Full text  │
│3. Extract    │ │              │  │- Images (OCR)    │- Embeddings │
│4. Embed      │ │              │  │- Text (simple)   │  info       │
└──────────────┘ └──────────────┘  └──────────────┘  └──────┬──────┘
    │                │                  │                     │
    └────────────────┴──────────────────┴─────────────────────┘
                 │
    ┌────────────┴────────────┐
    ▼                         ▼
┌──────────────────────┐  ┌──────────────────────┐
│   Vector Service     │  │  Vector Index        │
│                      │  │  (FAISS)             │
│Chunks text & creates │  │                      │
│embeddings using      │  │Stores vectors &      │
│pre-trained AI model  │  │enables fast searches │
│                      │  │                      │
│Input: "modern home"  │  │Searches for similar  │
│Output: [0.23, 0.15, │  │meanings, not keywords│
│ ...384 numbers...]   │  │                      │
└──────────────────────┘  └──────────────────────┘
    │                         │
    └────────────┬────────────┘
                 ▼
        ┌──────────────────────┐
        │   PostgreSQL DB      │
        │                      │
        │Documents table       │
        │Extracted_texts table │
        │Vector_embeddings tbl │
        │                      │
        │Stores configuration  │
        │and metadata          │
        └──────────────────────┘
```

---

This architecture provides:

- ✅ Scalability (add more servers)
- ✅ Reliability (database backup, error handling)
- ✅ Flexibility (swap components)
- ✅ Performance (optimized search)
- ✅ Maintainability (clean separation)

Perfect for starting a production service!
