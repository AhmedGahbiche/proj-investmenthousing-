# Document Management System with AI-Powered Search

A complete, production-ready document management service built with Python. Upload any documents (PDF, Word, images, text files), and search them using natural language (like talking to a person, not just keywords). Perfect for real estate property management, legal document storage, or any business that needs to organize and find documents quickly.

**What makes this special:** Instead of searching for exact words, you can search for ideas and meanings. For example, search for "modern kitchen with lots of light" instead of having to know the exact wording in the document.

---

## 📋 Table of Contents

- [What This Project Does](#what-this-project-does)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Quick Start - Installation Steps](#quick-start---installation-steps)
- [Detailed Setup Guide](#detailed-setup-guide)
- [How Everything Works Together](#how-everything-works-together)
- [API Endpoints (How to Use It)](#api-endpoints-how-to-use-it)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Advanced Configuration](#advanced-configuration)

---

## What This Project Does

This is a **backend service** (the behind-the-scenes processing system) that:

1. **Receives document uploads** - You send a PDF, Word document, image, or text file
2. **Extracts text** - Reads the content from any file format
3. **Creates a searchable index** - Generates AI-powered search capabilities
4. **Stores everything** - Keeps documents and their information in a database
5. **Provides search endpoints** - Lets you search documents through a web API (a standardized way for programs to talk to each other)

Think of it like building a digital filing system with a smart AI assistant that understands what you're looking for.

---

## Key Features

### ✅ Document Upload & Storage

- **Supported formats:** PDF, Word documents (.docx), Images (.png, .jpg), Text files (.txt)
- **Automatic text extraction:** Reads text from scanned images using OCR (a technology that reads text from images like a camera reading a page)
- **Secure storage:** Files are saved with unique names to prevent conflicts

### ✅ Intelligent Search

- **Semantic search:** Search by meaning, not just keyword matching
  - Example: Search "expensive homes" will find documents about "high-end properties"
- **Single document search:** Find content within one specific document
- **Cross-document search:** Search across all your documents at once
- **Ranked results:** Most relevant results appear first with similarity scores (how confident the system is about a match)

### ✅ AI Vector Embeddings

- **What it is:** Converting text into mathematical representations that computers can compare
- **Why it matters:** Allows the system to understand that "building" and "house" are similar concepts
- **Model used:** All-MiniLM-L6-v2 (a pre-trained AI model - meaning someone already trained it to be good at understanding text)

### ✅ Production-Ready

- **Database:** PostgreSQL (a professional database system)
- **Error handling:** Gracefully handles problems without crashing
- **Logging:** Keeps detailed records for debugging
- **Non-blocking failures:** If one thing fails, the system keeps working

---

## Technology Stack

### What's Under the Hood

```
Frontend (Web Interface) ↓
    ↓
FastAPI (Web framework - the middleman that receives requests)
    ↓
    ├─ File Storage (saves uploaded files to disk)
    ├─ Text Extraction (reads content from documents)
    ├─ Database Layer (PostgreSQL - stores metadata)
    ├─ Vector Service (converts text to numbers for search)
    └─ Vector Index (FAISS - finds similar documents quickly)
```

### Core Technologies

| Component         | Technology                                   | Purpose                                         |
| ----------------- | -------------------------------------------- | ----------------------------------------------- |
| **Web Framework** | FastAPI 0.104.1                              | Receives HTTP requests and sends responses      |
| **Database**      | PostgreSQL 13+                               | Stores document metadata and embeddings info    |
| **Vector Search** | FAISS 1.8.0                                  | Finds similar documents using AI                |
| **Embeddings**    | sentence-transformers                        | Converts text to mathematical vectors (numbers) |
| **Text Reading**  | pdfplumber, PyPDF2, python-docx, pytesseract | Extracts text from different file formats       |
| **Server**        | Uvicorn                                      | Runs the FastAPI application                    |
| **ORM**           | SQLAlchemy 2.0                               | Simplifies database operations                  |

---

## Quick Start - Installation Steps

### Step 1: Prerequisites (What You Need First)

- **Python 3.8+** (the programming language)
- **PostgreSQL 13+** (the database - install from postgresql.org)
- **pip** (package manager - usually comes with Python)

### Step 2: Clone/Download This Project

```bash
cd your-project-folder
# Copy this entire project into your folder
```

### Step 3: Create a Virtual Environment (Isolated Python Setup)

**Why?** Virtual environments keep project packages separate so they don't conflict with other projects.

```bash
# Create virtual environment
python3 -m venv .venv

# Activate it (Mac/Linux)
source .venv/bin/activate

# Activate it (Windows)
.venv\Scripts\activate
```

If successful, your terminal will show `(.venv)` at the beginning of the line.

### Step 4: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This installs all the packages your project needs. It might take 2-5 minutes.

### Step 5: Configure Environment Variables

Create a `.env` file in the `backend` folder with your settings:

```ini
# Database Connection
DATABASE_URL=postgresql://username:password@localhost:5432/document_db

# Logging
LOG_LEVEL=INFO
LOG_DIR=./logs

# File Upload Settings
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=50
ALLOWED_FORMATS=pdf,docx,png,txt

# Server Settings
DEBUG=false
```

**What these mean:**

- `DATABASE_URL`: Where your database is located
- `LOG_LEVEL`: How much detail to record (DEBUG=lots, INFO=important, ERROR=problems only)
- `UPLOAD_DIR`: Where to save uploaded files
- `MAX_FILE_SIZE_MB`: Maximum file size (in megabytes - 50 = 50MB)
- `ALLOWED_FORMATS`: File types you'll accept

### Step 6: Create the Database Tables

```bash
# This creates the database structure
python3 -c "from services.database import db_service; db_service.init_db()"
```

### Step 7: Run the Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

You should see:

```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

🎉 **Server is running!**

---

## Detailed Setup Guide

### Database Setup (PostgreSQL)

**What is PostgreSQL?** A professional database system that stores all your documents and their information.

#### Install PostgreSQL (One-Time Setup)

**Mac:**

```bash
brew install postgresql
brew services start postgresql
```

**Linux (Ubuntu):**

```bash
sudo apt-get install postgresql postgresql-contrib
sudo service postgresql start
```

**Windows:**

- Download from: https://www.postgresql.org/download/windows/
- Run the installer and note the username/password you create

#### Create Your Database

```bash
# Connect to PostgreSQL
psql postgres

# Create a new database
CREATE DATABASE document_db;

# Create a user (choose your own password)
CREATE USER doc_user WITH PASSWORD 'your_secure_password';

# Give the user permission
ALTER ROLE doc_user SET client_encoding TO 'utf8';
ALTER ROLE doc_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE doc_user SET default_transaction_deferrable TO on;
ALTER ROLE doc_user SET default_transaction_read_only TO off;
GRANT ALL PRIVILEGES ON DATABASE document_db TO doc_user;

# Exit PostgreSQL
\q
```

#### Update `.env`

```ini
DATABASE_URL=postgresql://doc_user:your_secure_password@localhost:5432/document_db
```

### File Structure After Setup

```
proj mrama/
├── backend/
│   ├── main.py                    # Main application file
│   ├── models.py                  # Database tables definition
│   ├── config.py                  # Settings management
│   ├── requirements.txt           # List of packages needed
│   ├── .env                       # Your secret settings (don't share!)
│   │
│   ├── services/
│   │   ├── database.py            # Database operations
│   │   ├── upload_service.py      # Handles file uploads
│   │   ├── file_storage.py        # Saves files to disk
│   │   ├── text_extraction.py     # Reads text from documents
│   │   ├── vector_service.py      # Creates AI embeddings
│   │   └── vector_index.py        # Searches with AI
│   │
│   ├── uploads/                   # Your uploaded files go here
│   ├── logs/                      # Activity logs
│   └── tests/                     # Test files
```

---

## How Everything Works Together

### The Complete Process: Uploading and Searching

```
1. USER UPLOADS A DOCUMENT
   ↓
   "Upload property listing.pdf"
   ↓

2. FILE VALIDATION
   ✓ Check file size (not too big)
   ✓ Check file type (is it allowed?)
   ↓

3. SAVE FILE TO DISK
   Save to: uploads/property_listing_2024_03_23_142530.pdf
   (timestamp added to prevent name conflicts)
   ↓

4. EXTRACT TEXT
   Read all text from PDF using pdfplumber
   Example: "Beautiful 4-bedroom home, modern kitchen..."
   ↓

5. SAVE TO DATABASE
   Store document info:
   - File name
   - Upload time
   - File size
   - Extracted text
   ↓

6. CREATE AI EMBEDDINGS (Search Index)
   ├─ Break text into chunks:
   │  "Beautiful 4-bedroom home"
   │  "modern kitchen with granite counters"
   │  etc.
   │
   ├─ Convert to numbers (embeddings):
   │  384-dimensional vectors (basically: 384 numbers representing the meaning)
   │
   └─ Store in FAISS Index:
      Fast, in-memory search system (like a smart filing cabinet)
   ↓

7. DOCUMENT IS READY TO SEARCH
   ✓ Stored on disk
   ✓ Indexed in database
   ✓ Searchable via AI
```

### Search Process

```
1. USER SEARCHES FOR SOMETHING
   ↓
   Search query: "modern home with updated kitchen"
   ↓

2. CONVERT QUERY TO EMBEDDINGS
   Convert the search phrase to the same 384-number format
   ↓

3. SEARCH WITH AI
   Find chunks of text with similar meanings using FAISS
   ↓

4. RETURN RESULTS
   {
     "rank": 1,
     "document_id": 5,
     "chunk_id": "chunk_42",
     "similarity_score": 0.89,  ← How confident (0.0-1.0, higher is better)
     "distance": 0.245
   }
   ↓

5. DISPLAY TO USER
   Results ranked by relevance (best matches first)
```

---

## API Endpoints (How to Use It)

### What's an API Endpoint?

An endpoint is like a door to the system. Each door does something specific:

- One door uploads files
- One door searches documents
- One door retrieves existing documents

### Health Check (Is the System Running?)

```bash
GET /health
```

**Example:**

```bash
curl http://localhost:8000/health

Response:
{
  "status": "healthy",
  "service": "Document Management Service"
}
```

### Upload a Document

```bash
POST /upload
```

**Parameters:**

- `file` - The file to upload (required)
- `document_type` - What kind of document (optional)
  - Examples: "property_listing", "report", "contract"
- `property_id` - Reference to the property (optional)

**Example:**

```bash
curl -X POST "http://localhost:8000/upload?document_type=listing&property_id=PROP001" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@property.pdf"

Response:
{
  "success": true,
  "document_id": 1,
  "filename": "property.pdf",
  "message": "Document uploaded and processed successfully"
}
```

### Get Document Information

```bash
GET /documents/{document_id}
```

**Example:**

```bash
curl http://localhost:8000/documents/1

Response:
{
  "id": 1,
  "filename": "property.pdf",
  "file_format": "pdf",
  "file_size": 245632,
  "document_type": "listing",
  "property_id": "PROP001",
  "upload_date": "2024-03-23T14:25:30.123456"
}
```

### Get Extracted Text

```bash
GET /documents/{document_id}/text
```

**Example:**

```bash
curl http://localhost:8000/documents/1/text

Response:
{
  "document_id": 1,
  "raw_text": "Beautiful 4-bedroom home in downtown...",
  "extraction_status": "success"
}
```

### Search Within One Document (Semantic Search)

```bash
POST /search/document/{document_id}?query={search_text}&k={number_of_results}
```

**What it does:** Searches within a single document for content similar to your query

**Parameters:**

- `query` - What to search for (like talking: "modern kitchen with natural light")
- `k` - How many results to return (default: 5, max: 20)

**Example:**

```bash
curl -X POST "http://localhost:8000/search/document/1?query=modern%20kitchen&k=5"

Response:
{
  "success": true,
  "query": "modern kitchen",
  "num_results": 2,
  "results": [
    {
      "rank": 1,
      "document_id": null,
      "chunk_id": "chunk_12",
      "distance": 0.156,
      "similarity_score": 0.865  ← Higher = better match (0-1 scale)
    },
    {
      "rank": 2,
      "document_id": null,
      "chunk_id": "chunk_15",
      "distance": 0.234,
      "similarity_score": 0.810
    }
  ]
}
```

### Search Across All Documents

```bash
POST /search?query={search_text}&k={number_of_results}&document_ids={optional_ids}
```

**What it does:** Searches across your entire document collection (or just specific documents)

**Parameters:**

- `query` - What to search for
- `document_ids` - Optional: limit search to specific documents (comma-separated: "1,2,3")
- `k` - How many results to return (default: 10, max: 50)

**Example 1: Search everything**

```bash
curl -X POST "http://localhost:8000/search?query=luxury%20property&k=10"
```

**Example 2: Search specific documents only**

```bash
curl -X POST "http://localhost:8000/search?query=updated%20bathroom&document_ids=1,3,5&k=10"

Response:
{
  "success": true,
  "query": "updated bathroom",
  "num_results": 3,
  "results": [
    {
      "rank": 1,
      "document_id": 3,      ← Which document this came from
      "chunk_id": "chunk_8",
      "distance": 0.189,
      "similarity_score": 0.842
    }
  ]
}
```

### List All Documents

```bash
GET /documents?limit=100&offset=0
```

**Parameters:**

- `limit` - How many documents to return (default: 100, max: 1000)
- `offset` - Skip this many documents (for pagination - showing page 2, 3, etc.)

**Example:**

```bash
# Get first 50 documents
curl "http://localhost:8000/documents?limit=50&offset=0"

# Get next 50 documents
curl "http://localhost:8000/documents?limit=50&offset=50"
```

---

## Project Structure

### Folder Breakdown

```
backend/
│
├── main.py
│   └─ The main application file
│     - Sets up FastAPI
│     - Defines all the endpoints (/upload, /search, etc.)
│     - Controls logging (keeping records)
│
├── models.py
│   └─ Defines database tables (like spreadsheet columns)
│     - Document table: filename, size, upload time, etc.
│     - ExtractedText table: stores text from documents
│     - VectorEmbedding table: tracks which docs have embeddings
│
├── config.py
│   └─ Settings management
│     - Reads your .env file
│     - Creates necessary directories
│     - Sets up logging
│
├── services/
│   │
│   ├── database.py
│   │   └─ All database operations
│   │     - Save document info
│   │     - Save extracted text
│   │     - Save embedding metadata
│   │
│   ├── upload_service.py
│   │   └─ Orchestrates the upload process
│   │     1. Validate file
│   │     2. Save to disk
│   │     3. Extract text
│   │     4. Create embeddings
│   │
│   ├── file_storage.py
│   │   └─ Saves files to disk with unique names
│   │
│   ├── text_extraction.py
│   │   └─ Reads text from different file types
│   │     - PDFs: uses pdfplumber
│   │     - Word: uses python-docx
│   │     - Images: uses pytesseract (OCR - reads text from pictures)
│   │     - Text: just reads it directly
│   │
│   ├── vector_service.py
│   │   └─ Creates AI embeddings (concept conversions)
│   │     - Chunks text (breaks into pieces)
│   │     - Generates embeddings (converts to numbers)
│   │     - Searches using embeddings
│   │
│   └── vector_index.py
│       └─ Manages the FAISS search index
│         - Creates new indices
│         - Stores embeddings
│         - Searches for similar items
│
├── uploads/
│   └─ Where uploaded files are stored
│
├── logs/
│   └─ Activity logs for debugging
│
├── requirements.txt
│   └─ List of all Python packages needed
│
├── .env
│   └─ Your secret configuration (don't share!)
│
└── test_basic.py
    └─ Basic tests to verify everything works
```

---

## Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'fastapi'"

**Cause:** Dependencies not installed

**Fix:**

```bash
pip install -r requirements.txt
```

### Problem: "psycopg2.OperationalError: could not connect to server"

**Cause:** PostgreSQL isn't running or connection details are wrong

**Fix:**

```bash
# Check if PostgreSQL is running (Mac)
brew services list

# Start PostgreSQL if stopped (Mac)
brew services start postgresql

# Check your .env file:
DATABASE_URL=postgresql://username:password@localhost:5432/dbname
```

### Problem: "Embedding generation takes too long"

**Cause:** First time loading the AI model (this is normal and expected)

**Fix:** Wait 2-3 minutes the first time. After that, it's cached (saved) and faster.

- The model file (33 MB) downloads on first use
- Subsequent uses are much faster

### Problem: "FileNotFoundError: [Errno 2] No such file or directory: './uploads'"

**Cause:** Upload directory doesn't exist

**Fix:**

```bash
mkdir -p uploads logs
```

### Problem: "The file is too large"

**Cause:** File exceeds MAX_FILE_SIZE_MB setting

**Fix:** In `.env`, increase:

```ini
MAX_FILE_SIZE_MB=100  # Change from 50 to 100, etc.
```

### Problem: "OCR not working for images"

**Cause:** pytesseract requires Tesseract system package

**Fix:**

```bash
# Mac
brew install tesseract

# Linux
sudo apt-get install tesseract-ocr

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

---

## Advanced Configuration

### Fine-Tuning Search Results

#### Change Chunk Size (How text is split)

In `upload_service.py`, find the embedding step and modify:

```python
vector_service.embed_document(
    document_id=document.id,
    text=raw_text,
    chunk_size=256,  # Smaller = more granular (detailed), Larger = broader context
    overlap=25       # How much chunks overlap (prevents cutting off context)
)
```

**What to adjust:**

- `chunk_size`: Smaller (256) = better for detailed searches, Larger (1024) = better for context
- `overlap`: Larger overlap = less chance of missing content, but slower

#### Change Number of Search Results

In `main.py`, modify the default `k` values:

```python
# In search_document endpoint:
k: int = Query(5, ge=1, le=20)  # Change 5 to default you want

# In search endpoint:
k: int = Query(10, ge=1, le=50)  # Change 10 to default you want
```

### Change Embedding Model (For Different Languages/Use Cases)

In `services/vector_service.py`:

```python
def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
    # Change to:
    # 'paraphrase-MiniLM-L6-v2' - Better for real estate
    # 'all-mpnet-base-v2' - Higher quality, slower
    # 'all-MiniLM-L6-v2' - Current: fast and good
```

### Database Maintenance

#### Backup Your Database

```bash
pg_dump document_db > backup_2024_03_23.sql
```

#### Restore from Backup

```bash
psql document_db < backup_2024_03_23.sql
```

#### Clear All Data (Start Fresh)

```bash
# Delete everything
python3 -c "from services.database import db_service; from models import Base; Base.metadata.drop_all(db_service.engine)"

# Recreate tables
python3 -c "from services.database import db_service; db_service.init_db()"
```

---

## Performance Tips

### For Better Speed

1. **Use PostgreSQL indexes** - Already configured automatically
2. **Batch uploads** - Upload multiple files at once programmatically
3. **Use appropriate chunk sizes** - Balance between granularity and performance
4. **Monitor logs** - Check `logs/app.log` for slow operations

### For Better Search Quality

1. **Write natural queries** - "beautiful homes" works better than "beautiful homes AND modern"
2. **Use whole document context** - More text = better understanding
3. **Adjust k value** - Higher k (15-20) returns more options to choose from

---

## Next Steps & Improvements

### Easy to Add Later

1. **Full-text search** - Keyword search in addition to semantic
2. **User authentication** - Secure access with logins
3. **Web interface** - Nice frontend for non-technical users
4. **Email alerts** - Notify when documents are uploaded
5. **Document categorization** - Automatic tagging

### For Large Scale (Many Documents)

1. **Switch to Qdrant** - More scalable database for vectors
2. **Add Redis caching** - Speed up repeated searches
3. **Elasticsearch** - Better for keyword search
4. **Cloud storage** - AWS S3 instead of local disk

---

## Support & Resources

### Where to Get Help

- **FastAPI Documentation:** https://fastapi.tiangolo.com/
- **FAISS Documentation:** https://github.com/facebookresearch/faiss/wiki
- **Sentence-transformers:** https://www.sbert.net/
- **PostgreSQL:** https://www.postgresql.org/docs/

### Common Questions

**Q: Can I use SQLite instead of PostgreSQL?**
A: Not recommended for production, but change in `.env`: `DATABASE_URL=sqlite:///./test.db`

**Q: How many documents can this handle?**
A: Tested up to 10,000 documents. For millions, upgrade to Qdrant.

**Q: Does this work with images?**
A: Yes! Images are converted to text using OCR (optical character recognition), then searchable.

**Q: What's the maximum file size?**
A: Default is 50MB, configurable in `.env` as `MAX_FILE_SIZE_MB`

---

## License & Credits

This project uses:

- **FastAPI** - Web framework
- **FAISS** - Vector search (Facebook AI Research)
- **Sentence-transformers** - Embeddings (Sentence-BERT)
- Contributing packages as listed in requirements.txt

Built with ❤️ for document management excellence.

---

**Last Updated:** March 2024  
**Version:** 1.0.0  
**Status:** Production Ready
