# Quick Setup Guide (5 Minutes)

## Prerequisites - What You Must Install First

1. **Python 3.8 or newer**

   ```bash
   python3 --version
   # Should show: Python 3.8.0 or higher
   ```

2. **PostgreSQL** (the database)
   - Mac: `brew install postgresql && brew services start postgresql`
   - Linux (Ubuntu): `sudo apt-get install postgresql postgresql-contrib`
   - Windows: Download from https://www.postgresql.org/download/windows/

3. **Git** (to download the project, optional)

---

## 5-Minute Setup

### 1. Prepare Your Database (PostgreSQL)

Open a terminal and run:

```bash
# Connect to PostgreSQL
psql postgres

# Create database and user (paste these commands one by one)
CREATE DATABASE document_db;
CREATE USER doc_user WITH PASSWORD 'your_password_here';
ALTER ROLE doc_user SET client_encoding TO 'utf8';
ALTER ROLE doc_user SET default_transaction_isolation TO 'read committed';
GRANT ALL PRIVILEGES ON DATABASE document_db TO doc_user;

# Exit PostgreSQL
\q
```

### 2. Download This Project

```bash
# Go to where you want the project
cd ~/Desktop  # or any folder

# Copy this project folder here
# (You may have already done this)
cd proj\ mrama/backend
```

### 3. Create Python Virtual Environment

```bash
# Create isolated Python environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate
# (Windows: .venv\Scripts\activate)

# You should see (.venv) before your prompt now
```

### 4. Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# This takes 2-5 minutes. Wait for it to finish.
```

### 5. Create .env File

Create a file named `.env` in the `backend` folder with:

```ini
DATABASE_URL=postgresql://doc_user:your_password_here@localhost:5432/document_db
LOG_LEVEL=INFO
LOG_DIR=./logs
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=50
ALLOWED_FORMATS=pdf,docx,png,txt
DEBUG=false
```

Replace `your_password_here` with the password you created in step 1.

### 6. Create Directories

```bash
mkdir -p uploads logs vector_indices
```

### 7. Initialize Database

```bash
python3 -c "from services.database import db_service; db_service.init_db()"
```

### 8. Run the Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

You should see:

```
INFO:     Uvicorn running on http://0.0.0.0:8000
Press CTRL+C to quit
```

✅ **Done! Your server is running.**

---

## Test It Works

Open a new terminal (keep the server running in the first one):

```bash
# Test if server responds
curl http://localhost:8000/health

# Should return:
# {"status":"healthy","service":"Document Management Service"}
```

---

## Try Uploading a Document

```bash
# Create a test file
echo "This is a test document about beautiful homes and modern kitchens." > test.txt

# Upload it
curl -X POST "http://localhost:8000/upload?document_type=test" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test.txt"

# You should get back something like:
# {"success":true,"document_id":1,"filename":"test.txt","message":"Document uploaded and processed successfully"}
```

---

## Try Searching

```bash
# Search for something in the document you just uploaded
curl -X POST "http://localhost:8000/search/document/1?query=modern%20kitchen"

# Should return results with similarity scores
```

---

## Troubleshooting Quick Fixes

| Problem                    | Fix                                                                |
| -------------------------- | ------------------------------------------------------------------ |
| `ModuleNotFoundError`      | Run `pip install -r requirements.txt` again                        |
| `connection refused`       | PostgreSQL not running. Run `brew services start postgresql` (Mac) |
| `(.venv) not showing`      | Run `source .venv/bin/activate` again                              |
| `Permission denied`        | Run commands with `python3` not `python`                           |
| `port 8000 already in use` | Change port: `--port 8001` or kill existing process                |

---

## Next Steps

1. **Upload more documents** - Try PDFs, Word docs, images
2. **Test searches** - Try natural language: "expensive homes", "updated bathroom", etc.
3. **Read COMPREHENSIVE_README.md** - For detailed documentation
4. **Configure settings** - Adjust MAX_FILE_SIZE, CHUNK_SIZE, etc.

---

**Stuck?** Check the COMPREHENSIVE_README.md file for detailed explanations!
