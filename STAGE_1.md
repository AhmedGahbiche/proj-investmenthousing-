# STAGE 1: Document Text Extraction - Complete Beginner's Guide

**Status**: ✅ Complete Implementation  
**Date**: March 24, 2026  
**Project**: Housing Investment Analysis Platform (Backend)

---

## Table of Contents

1. [What is Stage 1?](#what-is-stage-1)
2. [Prerequisites You Need](#prerequisites-you-need)
3. [Project Setup (From Scratch)](#project-setup-from-scratch)
4. [Understanding the Architecture](#understanding-the-architecture)
5. [Building Each Component](#building-each-component)
6. [Testing What You Built](#testing-what-you-built)
7. [Running the Application](#running-the-application)
8. [Glossary of Technical Terms](#glossary-of-technical-terms)

---

## What is Stage 1?

### Simple Explanation

Imagine you have a pile of documents (PDFs, Word files, images with text). Stage 1 takes those documents and:

1. **Accepts** them through an upload interface
2. **Reads** the text from each document (no matter the type)
3. **Cleans** the text to make sure it's valid
4. **Stores** both the file and the extracted text in a database
5. **Checks** the quality of extraction
6. **Provides** endpoints (entry points) so other parts of the system can access the text

### Real-World Analogy

Think of a library worker who:

- Receives books from patrons
- Reads and writes down key information from each book
- Checks if the written notes make sense
- Files everything in a cabinet
- Labels everything so people can find it later

That's what Stage 1 does with documents!

### What Files/Formats Does It Support?

| Format   | What It Is               | How We Extract                          |
| -------- | ------------------------ | --------------------------------------- |
| **TXT**  | Plain text files         | Read directly as text                   |
| **PDF**  | Portable Document Format | Use special PDF reader tool             |
| **DOCX** | Microsoft Word documents | Parse XML structure inside              |
| **PNG**  | Image files with text    | Use OCR (optical character recognition) |

---

## Prerequisites You Need

Before starting, install these tools on your computer:

### 1. Python Programming Language

**What it is**: A programming language - the instructions we write to make the program work  
**Why we need it**: All our code is written in Python  
**How to install**:

- Go to https://www.python.org/downloads/
- Download Python 3.10 or higher
- Install it and remember the installation path

**Check if installed**:

```bash
python3 --version
# Should show: Python 3.10.x or higher
```

### 2. PostgreSQL Database

**What it is**: A database - a organized storage system for data  
**Why we need it**: To store document metadata and extracted text  
**How to install**:

- Go to https://www.postgresql.org/download/
- Install PostgreSQL (remember the password you set)
- On macOS: Use Homebrew: `brew install postgresql`

**Check if installed**:

```bash
psql --version
# Should show version number
```

### 3. Tesseract OCR (for images with text)

**What it is**: OCR = "Optical Character Recognition" - technology that reads text from images  
**Why we need it**: To extract text from PNG/image files  
**How to install**:

- On macOS: `brew install tesseract`
- On Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
- On Linux: `sudo apt-get install tesseract-ocr`

**Check if installed**:

```bash
tesseract --version
# Should show version information
```

### 4. Git Version Control

**What it is**: A system that tracks changes to your code over time  
**Why we need it**: To save our work and track what changed  
**How to install**:

- On macOS: `brew install git`
- On Windows: Download from https://git-scm.com/download/win
- On Linux: `sudo apt-get install git`

**Check if installed**:

```bash
git --version
```

---

## Project Setup (From Scratch)

### Step 1: Create Project Folder

```bash
# Navigate to where you want your project
cd ~/Desktop

# Create a new folder
mkdir housinginvestment
cd housinginvestment

# Create backend subfolder
mkdir backend
cd backend
```

**Why this structure?**

- Separates frontend and backend
- Easy to manage multiple parts of the project
- Professional project organization

### Step 2: Initialize Git Repository

**Git** = a system that records every change you make to files (like "track changes" in Word)

```bash
# Initialize git in this folder
git init

# Configure who you are
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

### Step 3: Create Project Folders

```bash
# Create the folder structure
mkdir services
mkdir tests
mkdir scripts
mkdir logs
mkdir uploads
mkdir vector_indices
```

**Purpose of each folder**:

- **services**: Code that does actual work (like reading files, saving to database)
- **tests**: Code to verify our software works correctly
- **scripts**: Utility scripts for testing and validation
- **logs**: Record of what the program did (for debugging)
- **uploads**: Where uploaded files are stored temporarily
- **vector_indices**: Where we store vector data (for searching later)

### Step 4: Create Python Virtual Environment

**Virtual Environment** = an isolated Python installation just for this project  
**Why?** Different projects might need different versions of libraries - this keeps them separate

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate
# On Windows: venv\Scripts\activate

# You should see (venv) at the start of your terminal line
```

### Step 5: Create requirements.txt

This file lists all Python libraries our project needs.

Create a file called `requirements.txt` with this content:

```
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
python-multipart==0.0.6
pydantic==2.5.0
pydantic-settings==2.1.0
PyPDF2==3.0.1
pdfplumber==0.10.3
python-docx==0.8.11
pytesseract==0.3.10
pillow>=10.2.0
python-dotenv==1.0.0
pytest==7.4.3
httpx==0.25.2
faiss-cpu>=1.8.0
sentence-transformers==2.2.2
numpy>=1.24.3
scipy>=1.11.4
```

**What are these?** Libraries (pre-written code others created) that do specific things:

- **FastAPI**: Framework for building web APIs (the interfaces other programs use)
- **SQLAlchemy**: Library for working with databases
- **pdfplumber, PyPDF2**: Libraries for reading PDFs
- **python-docx**: Library for reading Word documents
- **pytesseract**: Library for OCR (reading text from images)
- **And many others** for different tasks

### Step 6: Install All Libraries

```bash
pip install -r requirements.txt
```

**What happens**: Python downloads and installs all the libraries listed  
**This takes a few minutes** - be patient!

---

## Understanding the Architecture

### What is Architecture?

**Architecture** = the overall structure and design of how pieces fit together  
Like blueprints for a building - how rooms connect and where water/electricity goes

### Our Application Architecture

```
USER/CLIENT
    ↓
    └─→ (Upload document)
           ↓
      FASTAPI SERVER (main.py)
      │
      ├─→ UPLOAD SERVICE
      │   │
      │   ├─→ FILE STORAGE SERVICE (saves file to disk)
      │   │
      │   ├─→ DATABASE SERVICE (saves metadata)
      │   │
      │   ├─→ TEXT EXTRACTION SERVICE
      │   │   │
      │   │   ├─→ DEPENDENCY CHECKER (verifies tools installed)
      │   │   │
      │   │   └─→ TEXT VALIDATOR (checks extracted text is clean)
      │   │
      │   └─→ VECTOR SERVICE (creates searchable embeddings)
      │
      └─→ RESPOND WITH RESULT
```

### Key Concept: Separation of Concerns

**Separation of Concerns** = each piece of code does ONE job, and does it well

Instead of one massive file doing everything, we have:

- One service for uploading
- One service for storage
- One service for extraction
- One service for validation
- Etc.

**Why?**

- Easy to understand (each file is focused)
- Easy to test (test each piece separately)
- Easy to fix bugs (know exactly where to look)
- Easy to change (update one part without breaking others)

---

## Building Each Component

### Component 1: Configuration (config.py)

This file holds all settings for your application.

**What settings do we need?**

- Database connection details
- File upload size limits
- Directory paths
- Logging levels
- Supported file formats

Create `config.py`:

```python
"""
Configuration settings for the document management service.
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables or defaults."""

    # FastAPI Settings
    APP_NAME: str = "Document Management Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database Settings
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/document_management"

    # File Storage Settings
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50 MB
    ALLOWED_FORMATS: list = ["pdf", "docx", "png", "txt"]

    # Logging Settings
    LOG_DIR: str = "./logs"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()

# Create necessary directories
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.LOG_DIR).mkdir(parents=True, exist_ok=True)
```

**Explanation**:

- `Settings` class: A template that defines what settings we need
- `DATABASE_URL`: Connection string to PostgreSQL (like "address" of the database)
- `UPLOAD_DIR`: Folder where files are stored
- `MAX_FILE_SIZE`: Largest file we accept (50 MB)
- `ALLOWED_FORMATS`: File types we accept
- The last lines automatically create needed folders

### Component 2: Data Models (models.py)

Models are like templates that define what data looks like.

**Analogy**: Like a form with specific fields - a business card has "name", "phone", "email" fields.

Create `models.py`:

```python
"""
Database models for document management service.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, Field
from typing import Optional

# SQLAlchemy ORM Base
Base = declarative_base()


# ============================================================================
# SQLAlchemy ORM Models (Database Tables)
# ============================================================================

class Document(Base):
    """
    SQLAlchemy model for storing document metadata.
    This represents a table in the database.
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

    # Indexes for common queries (speeds up searches)
    __table_args__ = (
        Index('idx_upload_timestamp', 'upload_timestamp'),
        Index('idx_property_id', 'property_id'),
    )


class ExtractedText(Base):
    """
    Stores the text we extracted from documents.
    """
    __tablename__ = "extracted_texts"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, unique=True)
    raw_text = Column(Text, nullable=False)
    extraction_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    extraction_status = Column(String(20), default="success", nullable=False)  # success, failed, partial
    extraction_error = Column(Text, nullable=True)  # Store error message if extraction failed

    __table_args__ = (
        Index('idx_document_id', 'document_id'),
    )


# ============================================================================
# Pydantic Schema Models (API Request/Response)
# ============================================================================

class DocumentResponse(BaseModel):
    """Schema for document response."""
    id: int
    filename: str
    file_format: str
    file_size: int
    upload_timestamp: datetime
    document_type: Optional[str] = None
    property_id: Optional[str] = None

    class Config:
        from_attributes = True


class ExtractedTextResponse(BaseModel):
    """Schema for extracted text response."""
    id: int
    document_id: int
    raw_text: str = Field(..., description="Extracted text content")
    extraction_timestamp: datetime
    extraction_status: str

    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    """Schema for upload endpoint response."""
    success: bool
    message: str
    document_id: Optional[int] = None
    filename: Optional[str] = None
    error: Optional[str] = None
```

**Key Concepts**:

- **Table**: Data organized in rows and columns (like Excel spreadsheet)
- **Column**: A field (like "name" or "email" column)
- **Primary Key**: Unique identifier (like ID number)
- **Foreign Key**: Link to another table
- **Index**: Makes searches faster (like alphabetical index in a book)
- **Pydantic**: Validates data (makes sure it's the right type)

### Component 3: Services (Business Logic)

Now we create the services that do the actual work. These live in the `services/` folder.

#### Service 3.1: dependency_checker.py

This service checks if we have all tools we need installed before running.

Create `services/dependency_checker.py`:

```python
"""
System dependency checker for validating external tool availability.
Ensures OCR, image processing, and document parsing tools are properly installed.
"""
import logging
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class DependencyChecker:
    """Validates system-level and Python dependencies for document processing."""

    # System commands that must be available
    SYSTEM_DEPENDENCIES = {
        'tesseract': {
            'command': 'tesseract',
            'version_flag': '--version',
            'required_for': 'PNG/image text extraction (OCR)',
            'install_help': 'Install Tesseract-OCR: https://github.com/UB-Mannheim/tesseract/wiki'
        },
    }

    # Python packages that must be importable
    PYTHON_DEPENDENCIES = {
        'pdfplumber': 'PDF text extraction (primary)',
        'PyPDF2': 'PDF text extraction (fallback)',
        'docx': 'DOCX document parsing',
        'pytesseract': 'Python OCR interface',
        'PIL': 'Image processing',
        'sentence_transformers': 'Text embeddings',
        'sqlalchemy': 'Database ORM',
    }

    def __init__(self):
        """Initialize dependency checker."""
        self.system_check_results: Dict[str, bool] = {}
        self.python_check_results: Dict[str, bool] = {}
        self.warnings: List[str] = []
        self.errors: List[str] = []

    def check_all(self) -> Tuple[bool, List[str], List[str]]:
        """
        Perform all dependency checks.

        Returns:
            Tuple of (all_critical_deps_available, warnings, errors)
        """
        logger.info("Starting system dependency checks...")

        # Check system dependencies
        self._check_system_dependencies()

        # Check Python dependencies
        self._check_python_dependencies()

        # Compile results
        all_available = all(self.system_check_results.values()) and \
                       all(self.python_check_results.values())

        return all_available, self.warnings, self.errors

    def _check_system_dependencies(self):
        """Check for required system commands."""
        logger.info("Checking system dependencies...")

        for dep_name, dep_info in self.SYSTEM_DEPENDENCIES.items():
            available = self._check_command_exists(dep_info['command'])
            self.system_check_results[dep_name] = available

            if not available:
                warning = f"⚠️  {dep_name} not found: {dep_info['install_help']}"
                self.warnings.append(warning)
                logger.warning(warning)
            else:
                logger.info(f"✓ {dep_name} is available")

    def _check_python_dependencies(self):
        """Check for required Python packages."""
        logger.info("Checking Python dependencies...")

        for package_name, use_case in self.PYTHON_DEPENDENCIES.items():
            available = self._check_package_importable(package_name)
            self.python_check_results[package_name] = available

            if not available:
                error = f"❌ {package_name} not installed (required for: {use_case})"
                self.errors.append(error)
                logger.error(error)
            else:
                logger.info(f"✓ {package_name} is available")

    @staticmethod
    def _check_command_exists(command: str) -> bool:
        """Check if a command exists in system PATH."""
        try:
            result = subprocess.run(
                [command, '--version'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
        except Exception as e:
            logger.warning(f"Error checking command {command}: {str(e)}")
            return False

    @staticmethod
    def _check_package_importable(package_name: str) -> bool:
        """Check if a Python package can be imported."""
        try:
            __import__(package_name)
            return True
        except ImportError:
            return False
        except Exception as e:
            logger.warning(f"Error checking package {package_name}: {str(e)}")
            return False

    def get_format_support_status(self) -> Dict[str, str]:
        """Get extraction capability for each document format."""
        status = {
            'pdf': 'FULL' if self.python_check_results.get('pdfplumber', False) else 'PARTIAL',
            'docx': 'FULL' if self.python_check_results.get('docx', False) else 'UNAVAILABLE',
            'txt': 'FULL',  # Always supported, no dependencies
            'png': 'FULL' if (self.system_check_results.get('tesseract', False) and
                             self.python_check_results.get('pytesseract', False)) else 'UNAVAILABLE'
        }
        return status


# Global dependency checker instance
dependency_checker = DependencyChecker()
```

**Why we need this**:

- Prevents cryptic error messages later
- Tells user exactly what's missing
- Checks before running the app

#### Service 3.2: text_validator.py

This checks if extracted text is valid and clean.

Create `services/text_validator.py`:

```python
"""
Text validation and sanitization service.
Ensures extracted text is clean, valid, and free from corruption.
"""
import logging
import re
import unicodedata
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class TextValidator:
    """Validates and sanitizes extracted text content."""

    # Configuration thresholds
    MAX_TEXT_SIZE = 10 * 1024 * 1024  # 10 MB
    MIN_VALID_LENGTH = 1  # Minimum characters for valid extraction
    SUSPICIOUS_NULL_BYTE_THRESHOLD = 0.01  # More than 1% null bytes = corrupted
    SUSPICIOUS_CONTROL_CHAR_THRESHOLD = 0.05  # More than 5% control chars = suspicious

    # Regex patterns for anomalies
    EXCESSIVE_WHITESPACE = re.compile(r'\s{3,}')  # 3+ consecutive whitespace
    EXCESSIVE_NEWLINES = re.compile(r'\n{3,}')  # 3+ consecutive newlines

    def validate_and_sanitize(self, text: str) -> Tuple[bool, str, Optional[str]]:
        """
        Validate and sanitize extracted text.

        Args:
            text: Raw extracted text

        Returns:
            Tuple of (is_valid, sanitized_text, warning_message)
        """
        if not isinstance(text, str):
            return False, "", "Text is not a string"

        # Check for empty text
        if not text or not text.strip():
            return False, "", "Text is empty or contains only whitespace"

        # Check for excessive size
        if len(text) > self.MAX_TEXT_SIZE:
            return False, "", f"Text exceeds maximum size"

        # Check for null bytes (indicates binary/corrupted content)
        null_byte_ratio = text.count('\x00') / len(text) if text else 0
        if null_byte_ratio > self.SUSPICIOUS_NULL_BYTE_THRESHOLD:
            return False, "", f"Text contains excessive null bytes - likely corrupted"

        # Check for control characters
        control_char_count = sum(1 for c in text if unicodedata.category(c).startswith('C'))
        control_char_ratio = control_char_count / len(text) if text else 0
        warning = None

        if control_char_ratio > self.SUSPICIOUS_CONTROL_CHAR_THRESHOLD:
            warning = f"Text contains high percentage of control characters"

        # Sanitize: remove problematic characters
        sanitized = self._sanitize_text(text)

        # Verify sanitized text isn't empty
        if not sanitized or not sanitized.strip():
            return False, "", "Text became empty after sanitization"

        return True, sanitized, warning

    def _sanitize_text(self, text: str) -> str:
        """Remove or normalize problematic characters."""
        # Remove null bytes
        text = text.replace('\x00', '')

        # Remove form feed, vertical tab
        allowed_control_chars = {'\t', '\n', '\r'}
        text = ''.join(c if unicodedata.category(c) != 'Cc' or c in allowed_control_chars
                      else ' ' for c in text)

        # Normalize Unicode (NFC normalization)
        text = unicodedata.normalize('NFC', text)

        # Replace excessive whitespace patterns
        text = self.EXCESSIVE_WHITESPACE.sub('  ', text)
        text = self.EXCESSIVE_NEWLINES.sub('\n\n', text)

        # Clean up line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # Remove trailing whitespace from lines
        text = '\n'.join(line.rstrip() for line in text.split('\n')).strip()

        return text

    def get_text_health_score(self, text: str) -> dict:
        """Generate a health assessment for extracted text."""
        if not text:
            return {
                'score': 0.0,
                'is_valid': False,
                'length': 0,
                'word_count': 0,
                'line_count': 0,
                'unique_chars': 0,
                'null_bytes': 0,
                'control_chars': 0,
                'encoding_issues': 0,
                'warnings': ['Empty text']
            }

        warnings = []

        # Character statistics
        length = len(text)
        null_bytes = text.count('\x00')
        control_chars = sum(1 for c in text if unicodedata.category(c).startswith('C'))
        unique_chars = len(set(text))

        # Text statistics
        lines = text.split('\n')
        line_count = len(lines)
        words = text.split()
        word_count = len(words)

        # Check for encoding issues
        encoding_issues = 0
        try:
            text.encode('utf-8')
        except UnicodeEncodeError as e:
            encoding_issues = len(e.reason) if hasattr(e, 'reason') else 1

        # Calculate health score (0-100)
        score = 100.0

        if null_bytes > 0:
            score -= min(50, null_bytes * 5)
            warnings.append(f"Contains {null_bytes} null bytes")

        if control_chars > length * 0.05:
            score -= 10
            warnings.append(f"High control character ratio")

        if word_count == 0:
            score -= 50
            warnings.append(f"No recognizable words detected")

        elif word_count < 3:
            score -= 20
            warnings.append(f"Very short text: only {word_count} words")

        score = max(0, min(100, score))

        return {
            'score': round(score, 2),
            'is_valid': score >= 50,
            'length': length,
            'word_count': word_count,
            'line_count': line_count,
            'unique_chars': unique_chars,
            'null_bytes': null_bytes,
            'control_chars': control_chars,
            'encoding_issues': encoding_issues,
            'warnings': warnings
        }


# Global text validator instance
text_validator = TextValidator()
```

**Why validation?**

- Detects corrupted files or OCR failures
- Cleans up messy extracted text
- Gives quality score (0-100) so we know if text is usable
- **Real world example**: Like a quality inspector checking products

#### Service 3.3: text_extraction.py

This is where we actually extract text from documents.

Create `services/text_extraction.py` (this is a large file, shown in sections):

```python
"""
Text extraction service module for extracting content from various document formats.
Supports PDF, DOCX, PNG (with OCR), and TXT formats.
Includes timeout protection, error handling, and text validation.
"""
import logging
import signal
from pathlib import Path
from typing import Tuple
from functools import wraps
from services.text_validator import text_validator

logger = logging.getLogger(__name__)


def timeout_handler(signum, frame):
    """Handle timeout during text extraction."""
    raise TimeoutError("Text extraction operation timed out")


def extract_with_timeout(timeout_seconds: int = 60):
    """
    Decorator to add timeout protection to extraction methods.

    A decorator is like a wrapper - it adds extra functionality to a function
    without changing the function itself.

    Args:
        timeout_seconds: Maximum time allowed for extraction
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Set signal handler
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_seconds)
            try:
                result = func(*args, **kwargs)
                signal.alarm(0)  # Cancel alarm
                return result
            except TimeoutError:
                logger.error(f"Extraction timeout after {timeout_seconds}s")
                raise
            finally:
                signal.alarm(0)  # Ensure alarm is cancelled
        return wrapper
    return decorator


class TextExtractionService:
    """Service for extracting text from various document formats."""

    SUPPORTED_FORMATS = {
        'pdf': 'extract_text_from_pdf',
        'docx': 'extract_text_from_docx',
        'png': 'extract_text_from_png',
        'txt': 'extract_text_from_txt',
    }

    # Extraction timeout configuration (seconds)
    EXTRACTION_TIMEOUTS = {
        'pdf': 120,    # PDFs can be large
        'docx': 60,    # DOCX is usually smaller
        'png': 90,     # OCR can be slow
        'txt': 30,     # Text files should be fast
    }

    def __init__(self):
        """Initialize text extraction service."""
        self.validator = text_validator

    def extract_text(self, file_path: str, file_format: str) -> Tuple[str, str, str]:
        """
        Extract text from document based on format.

        Args:
            file_path: Path to the file
            file_format: File format (pdf, docx, png, txt)

        Returns:
            Tuple of (extracted_text, status, error_message)
            status can be: 'success', 'partial', 'failed'
            error_message is None if extraction succeeds
        """
        file_format = file_format.lower()

        if file_format not in self.SUPPORTED_FORMATS:
            error_msg = f"Unsupported file format: {file_format}"
            logger.error(error_msg)
            return "", "failed", error_msg

        try:
            # Get extraction method
            extraction_method = getattr(self, self.SUPPORTED_FORMATS[file_format])

            # Get timeout for this format
            timeout = self.EXTRACTION_TIMEOUTS.get(file_format, 60)

            # Extract text
            text, status = extraction_method(file_path, timeout)

            # Validate and sanitize extracted text
            is_valid, sanitized_text, validation_warning = self.validator.validate_and_sanitize(text)

            if validation_warning:
                logger.warning(f"Text validation warning: {validation_warning}")

            if not is_valid:
                logger.warning(f"Text validation failed: {validation_warning}")
                status = "failed" if status != "success" else "partial"
                return "", status, validation_warning

            logger.info(f"Text extraction completed for {file_format}: {status}")
            return sanitized_text, status, None

        except TimeoutError as e:
            error_msg = f"Extraction timeout for {file_format}: {str(e)}"
            logger.error(error_msg)
            return "", "failed", error_msg
        except Exception as e:
            error_msg = f"Error extracting text from {file_format}: {str(e)}"
            logger.error(error_msg)
            return "", "failed", error_msg

    @staticmethod
    @extract_with_timeout(timeout_seconds=30)
    def extract_text_from_txt(file_path: str, timeout: int = 30) -> Tuple[str, str]:
        """Extract text from TXT file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

            if not text.strip():
                logger.warning(f"TXT file is empty: {file_path}")
                return "", "partial"

            logger.info(f"Successfully extracted text from TXT: {file_path}")
            return text, "success"

        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    text = f.read()
                logger.info(f"Successfully extracted text from TXT with fallback encoding")
                return text, "success"
            except Exception as e:
                logger.error(f"Failed to extract text from TXT: {str(e)}")
                raise
        except Exception as e:
            logger.error(f"Failed to read TXT file: {str(e)}")
            raise

    @staticmethod
    @extract_with_timeout(timeout_seconds=120)
    def extract_text_from_pdf(file_path: str, timeout: int = 120) -> Tuple[str, str]:
        """Extract text from PDF file using pdfplumber."""
        try:
            import pdfplumber
        except ImportError:
            logger.warning("pdfplumber not installed, falling back to PyPDF2")
            return TextExtractionService._extract_text_from_pdf_pypdf2(file_path, timeout)

        try:
            text_content = []

            with pdfplumber.open(file_path) as pdf:
                if len(pdf.pages) == 0:
                    logger.warning(f"PDF has no pages: {file_path}")
                    return "", "partial"

                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_content.append(f"--- Page {page_num} ---\n{page_text}")
                    except Exception as e:
                        logger.warning(f"Failed to extract text from page {page_num}: {str(e)}")

            merged_text = "\n\n".join(text_content)

            if not merged_text.strip():
                logger.warning(f"No text could be extracted from PDF: {file_path}")
                return "", "partial"

            logger.info(f"Successfully extracted text from PDF: {file_path}")
            return merged_text, "success"

        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {str(e)}")
            raise

    @staticmethod
    def _extract_text_from_pdf_pypdf2(file_path: str, timeout: int = 120) -> Tuple[str, str]:
        """Fallback PDF extraction using PyPDF2."""
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            raise ImportError("PyPDF2 is not installed")

        try:
            text_content = []

            with open(file_path, 'rb') as f:
                pdf_reader = PdfReader(f)

                if len(pdf_reader.pages) == 0:
                    logger.warning(f"PDF has no pages: {file_path}")
                    return "", "partial"

                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_content.append(f"--- Page {page_num} ---\n{page_text}")
                    except Exception as e:
                        logger.warning(f"Failed to extract page {page_num}: {str(e)}")

            merged_text = "\n\n".join(text_content)

            if not merged_text.strip():
                logger.warning(f"No text could be extracted from PDF")
                return "", "partial"

            logger.info(f"Successfully extracted text from PDF with PyPDF2")
            return merged_text, "success"

        except Exception as e:
            logger.error(f"Failed to extract text from PDF with PyPDF2: {str(e)}")
            raise

    @staticmethod
    @extract_with_timeout(timeout_seconds=60)
    def extract_text_from_docx(file_path: str, timeout: int = 60) -> Tuple[str, str]:
        """Extract text from DOCX file."""
        try:
            from docx import Document
        except ImportError:
            raise ImportError("python-docx is not installed")

        try:
            doc = Document(file_path)

            text_content = []

            # Extract text from paragraphs
            for para in doc.paragraphs:
                if para.text.strip():
                    text_content.append(para.text)

            # Extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    row_text = [cell.text for cell in row.cells]
                    text_content.append(" | ".join(row_text))

            merged_text = "\n".join(text_content)

            if not merged_text.strip():
                logger.warning(f"No text could be extracted from DOCX")
                return "", "partial"

            logger.info(f"Successfully extracted text from DOCX")
            return merged_text, "success"

        except Exception as e:
            logger.error(f"Failed to extract text from DOCX: {str(e)}")
            raise

    @staticmethod
    def _preprocess_image(image):
        """Preprocess image to improve OCR accuracy."""
        try:
            from PIL import ImageEnhance, ImageFilter
        except ImportError:
            logger.warning("PIL enhancement not available, skipping preprocessing")
            return image

        try:
            # Convert to grayscale if color
            if image.mode != 'L':
                image = image.convert('L')

            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2)

            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(2)

            # Apply slight blur to reduce noise
            image = image.filter(ImageFilter.MedianFilter(size=3))

            logger.debug(f"Image preprocessing completed")
            return image
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {str(e)}, continuing without preprocessing")
            return image

    @staticmethod
    @extract_with_timeout(timeout_seconds=90)
    def extract_text_from_png(file_path: str, timeout: int = 90) -> Tuple[str, str]:
        """Extract text from PNG file using OCR (Tesseract)."""
        try:
            import pytesseract
            from PIL import Image
        except ImportError:
            raise ImportError("pytesseract and/or Pillow are not installed")

        try:
            # Check if Tesseract is installed
            try:
                import subprocess
                result = subprocess.run(['tesseract', '--version'],
                                       capture_output=True, timeout=5)
                if result.returncode != 0:
                    raise RuntimeError("Tesseract not properly installed")
            except FileNotFoundError:
                raise RuntimeError("Tesseract-OCR is not installed on this system. "
                                  "Please install it: https://github.com/UB-Mannheim/tesseract/wiki")

            # Open image
            image = Image.open(file_path)
            logger.info(f"Loaded image: {image.size} {image.mode}")

            # Preprocess image for better OCR
            image = TextExtractionService._preprocess_image(image)

            # Extract text using OCR
            text = pytesseract.image_to_string(image)

            if not text or not text.strip():
                logger.warning(f"No text could be extracted from PNG via OCR")
                return "", "partial"

            logger.info(f"Successfully extracted text from PNG via OCR")
            return text, "success"

        except RuntimeError as e:
            logger.error(f"OCR system error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to extract text from PNG: {str(e)}")
            raise


# Global text extraction service instance
text_extraction = TextExtractionService()
```

**Key Technical Concepts**:

- **Decorator**: A wrapper that adds functionality to a function (`@extract_with_timeout`)
  - Like wrapping a gift - the gift is still there, but now it has wrapping paper
- **Signal/Timeout**: Safety mechanism that stops a process if it takes too long
  - Like a timer when cooking - if time expires, stop what you're doing

- **Fallback**: Plan B if Plan A doesn't work
  - Try pdfplumber first (better), use PyPDF2 if that's not available

- **Preprocessing**: Improve image quality before OCR
  - Like cleaning glasses before reading - makes OCR work better

Continue to next part (database service, file storage, upload service, and main FastAPI app in next sections)...

#### Service 3.4: database.py

Create `services/database.py`:

```python
"""
Database service module for managing PostgreSQL operations.
Handles document and extracted text persistence.
"""
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from config import settings
from models import Base, Document, ExtractedText

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
        """Get a new database session."""
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
        """Save document metadata to database."""
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
        """Save extracted text content to database."""
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
        """Get document by ID."""
        session = self.get_session()
        try:
            document = session.query(Document).filter(Document.id == document_id).first()
            return document
        finally:
            session.close()

    def get_document_text(self, document_id: int) -> ExtractedText:
        """Get extracted text for a document."""
        session = self.get_session()
        try:
            extracted_text = session.query(ExtractedText).filter(
                ExtractedText.document_id == document_id
            ).first()
            return extracted_text
        finally:
            session.close()


# Global database service instance
db_service = DatabaseService()
```

**Key Concepts**:

- **Session**: A conversation with the database (like a phone call - you call, talk, hang up)
- **Commit**: Save changes to database (permanent)
- **Rollback**: Undo changes (if something went wrong)
- **Finally**: Always execute this code, even if error occurred (cleanup code)

#### Service 3.5: file_storage.py

Create `services/file_storage.py`:

```python
"""
File storage service module for managing persistent file storage.
Handles file saving and retrieval from disk.
"""
import os
import logging
import shutil
from pathlib import Path
from datetime import datetime
from config import settings

logger = logging.getLogger(__name__)


class FileStorageService:
    """Service for managing file storage operations."""

    def __init__(self, base_path: str = settings.UPLOAD_DIR):
        """
        Initialize file storage service.

        Args:
            base_path: Base directory for file storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"File storage service initialized with base path: {self.base_path}")

    def generate_unique_filename(self, original_filename: str) -> str:
        """
        Generate a unique filename to avoid conflicts.

        Example: "report.pdf" becomes "report_20240324_143025_123.pdf"
        """
        name, ext = os.path.splitext(original_filename)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        unique_filename = f"{name}_{timestamp}{ext}"
        return unique_filename

    def save_file(self, file_content: bytes, original_filename: str) -> str:
        """
        Save uploaded file to disk storage.

        Args:
            file_content: File content as bytes
            original_filename: Original filename

        Returns:
            Path where file was saved
        """
        try:
            # Generate unique filename to prevent overwrites
            unique_filename = self.generate_unique_filename(original_filename)
            file_path = self.base_path / unique_filename

            # Write file to disk
            with open(file_path, 'wb') as f:
                f.write(file_content)

            logger.info(f"File saved successfully: {file_path}")
            return str(file_path.relative_to(Path.cwd()))

        except IOError as e:
            logger.error(f"IO error while saving file: {str(e)}")
            raise Exception(f"Failed to save file: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error while saving file: {str(e)}")
            raise Exception(f"Unexpected error saving file: {str(e)}")

    def read_file(self, file_path: str) -> bytes:
        """Read file from disk storage."""
        try:
            full_path = Path(file_path)
            if not full_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            with open(full_path, 'rb') as f:
                content = f.read()

            logger.info(f"File read successfully: {file_path}")
            return content

        except FileNotFoundError as e:
            logger.error(f"File not found: {str(e)}")
            raise
        except IOError as e:
            logger.error(f"IO error while reading file: {str(e)}")
            raise Exception(f"Failed to read file: {str(e)}")

    def delete_file(self, file_path: str) -> bool:
        """Delete file from disk storage."""
        try:
            full_path = Path(file_path)
            if full_path.exists():
                full_path.unlink()
                logger.info(f"File deleted successfully: {file_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {file_path}")
                return False

        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            raise Exception(f"Failed to delete file: {str(e)}")

    def file_exists(self, file_path: str) -> bool:
        """Check if file exists."""
        return Path(file_path).exists()


# Global file storage service instance
file_storage = FileStorageService()
```

**Concept**: This service handles all disk operations

- Saving files (like saving to your computer)
- Reading files (like opening a file)
- Deleting files (like moving to trash)
- Each operation is in its own method for clarity

#### Service 3.6: upload_service.py

Create `services/upload_service.py` (orchestrates everything):

```python
"""
Upload service module for handling file upload validation and orchestration.
Coordinates file storage, text extraction, and database operations.
"""
import logging
from mimetypes import guess_extension
from config import settings
from services.file_storage import file_storage
from services.text_extraction import text_extraction
from services.database import db_service
from services.vector_service import vector_service

logger = logging.getLogger(__name__)


class UploadService:
    """Service for handling document uploads and processing."""

    def __init__(self):
        """Initialize upload service."""
        self.allowed_formats = settings.ALLOWED_FORMATS
        self.max_file_size = settings.MAX_FILE_SIZE
        # MIME type to format mapping
        self.mime_to_format = {
            'application/pdf': 'pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
            'image/png': 'png',
            'text/plain': 'txt',
        }

    def validate_file(
        self,
        filename: str,
        file_content: bytes,
        content_type: str = None
    ) -> tuple[bool, str]:
        """
        Validate uploaded file.

        Args:
            filename: Original filename
            file_content: File content as bytes
            content_type: MIME type of the file

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate filename
        if not filename or not filename.strip():
            return False, "Filename is empty"

        # Extract file extension
        file_ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''

        if not file_ext:
            return False, "File has no extension"

        # Validate file extension
        if file_ext not in self.allowed_formats:
            return False, f"File format '.{file_ext}' is not supported. Allowed formats: {', '.join(self.allowed_formats)}"

        # Validate file size
        file_size = len(file_content)
        if file_size == 0:
            return False, "File is empty"

        if file_size > self.max_file_size:
            max_size_mb = self.max_file_size / (1024 * 1024)
            return False, f"File size exceeds maximum allowed size ({max_size_mb} MB)"

        logger.info(f"File validation passed: {filename} ({file_size} bytes)")
        return True, ""

    def process_upload(
        self,
        filename: str,
        file_content: bytes,
        document_type: str = None,
        property_id: str = None
    ) -> dict:
        """
        Process file upload end-to-end.
        Orchestrates: validation -> storage -> text extraction -> database persistence

        Args:
            filename: Original filename
            file_content: File content as bytes
            document_type: Optional document type classification
            property_id: Optional property ID reference

        Returns:
            Dictionary with upload result
        """
        try:
            # Step 1: Validate file
            logger.info(f"Starting upload process for: {filename}")
            is_valid, error_msg = self.validate_file(filename, file_content)

            if not is_valid:
                logger.warning(f"File validation failed: {error_msg}")
                return {
                    'success': False,
                    'document_id': None,
                    'filename': filename,
                    'message': 'File validation failed',
                    'error': error_msg
                }

            # Extract file extension and size
            file_ext = filename.rsplit('.', 1)[-1].lower()
            file_size = len(file_content)

            # Step 2: Save file to disk
            logger.info(f"Saving file to disk: {filename}")
            try:
                file_path = file_storage.save_file(file_content, filename)
            except Exception as e:
                logger.error(f"File storage failed: {str(e)}")
                return {
                    'success': False,
                    'document_id': None,
                    'filename': filename,
                    'message': 'Failed to save file to storage',
                    'error': str(e)
                }

            # Step 3: Save document metadata to database
            logger.info(f"Saving document metadata to database: {filename}")
            try:
                document = db_service.save_document(
                    filename=filename,
                    file_format=file_ext,
                    file_path=file_path,
                    file_size=file_size,
                    document_type=document_type,
                    property_id=property_id
                )
            except Exception as e:
                logger.error(f"Database save failed: {str(e)}")
                # Attempt to clean up saved file
                try:
                    file_storage.delete_file(file_path)
                except:
                    pass
                return {
                    'success': False,
                    'document_id': None,
                    'filename': filename,
                    'message': 'Failed to save document to database',
                    'error': str(e)
                }

            # Step 4: Extract text from document
            logger.info(f"Extracting text from document: {filename}")
            try:
                raw_text, extraction_status, extraction_error = text_extraction.extract_text(
                    file_path,
                    file_ext
                )
            except Exception as e:
                raw_text, extraction_status, extraction_error = "", "failed", str(e)
                logger.error(f"Text extraction failed: {str(e)}")

            # Step 5: Save extracted text to database
            logger.info(f"Saving extracted text to database: {filename}")
            try:
                extracted_text = db_service.save_extracted_text(
                    document_id=document.id,
                    raw_text=raw_text if raw_text else "",
                    extraction_status=extraction_status,
                    extraction_error=extraction_error
                )
            except Exception as e:
                logger.error(f"Failed to save extracted text: {str(e)}")
                return {
                    'success': True,
                    'document_id': document.id,
                    'filename': filename,
                    'message': 'Document saved but text extraction failed',
                    'error': f"Text extraction error: {str(e)}"
                }

            # Step 6: Generate vector embeddings for semantic search
            logger.info(f"Generating vector embeddings for document: {filename}")
            embedding_error = None
            try:
                if raw_text and extraction_status == "success":
                    vector_service.embed_document(
                        document_id=document.id,
                        text=raw_text,
                    )
            except Exception as e:
                embedding_error = str(e)
                logger.warning(f"Vector embedding failed: {str(e)}")

            # Return success
            logger.info(f"Upload completed successfully: {filename} (ID: {document.id})")
            return {
                'success': True,
                'document_id': document.id,
                'filename': filename,
                'message': 'Document uploaded and processed successfully',
                'error': embedding_error
            }

        except Exception as e:
            logger.error(f"Unexpected error in upload process: {str(e)}")
            return {
                'success': False,
                'document_id': None,
                'filename': filename,
                'message': 'Unexpected error during upload',
                'error': str(e)
            }


# Global upload service instance
upload_service = UploadService()
```

**Orchestration**: Like a conductor leading an orchestra

- FileStorage plays one note
- TextExtraction plays another
- Database plays another
- UploadService coordinates them all in harmony

### Component 4: Main Application (main.py)

This is the "entry point" – where web requests come in.

Create `main.py`:

```python
"""
Main FastAPI application for document management service.
Provides REST endpoints for document upload, retrieval, and text extraction.
"""
import logging
from logging.handlers import RotatingFileHandler
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse
from pathlib import Path

from config import settings
from models import (
    DocumentResponse, ExtractedTextResponse, UploadResponse,
    DocumentWithTextResponse
)
from services.upload_service import upload_service
from services.database import db_service
from services.vector_service import vector_service
from services.dependency_checker import dependency_checker
from services.text_validator import text_validator

# ============================================================================
# Logging Configuration
# ============================================================================

def setup_logging():
    """Configure application logging."""
    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))

    # File handler
    file_handler = RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger


# ============================================================================
# FastAPI Application Setup
# ============================================================================

logger = setup_logging()
logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-ready document management service for real estate analysis platform"
)


# ============================================================================
# Startup and Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize database, check dependencies, and initialize services on startup."""
    try:
        # Check system dependencies
        logger.info("Checking system dependencies...")
        all_available, warnings, errors = dependency_checker.check_all()

        # Log dependency status
        if warnings:
            logger.warning("Dependency warnings:")
            for warning in warnings:
                logger.warning(f"  {warning}")

        if errors:
            logger.error("Critical dependency errors:")
            for error in errors:
                logger.error(f"  {error}")
            raise RuntimeError("Critical dependencies missing. Cannot start service.")

        # Log format support
        format_support = dependency_checker.get_format_support_status()
        logger.info(f"Document format support: {format_support}")

        # Initialize database
        logger.info("Initializing database...")
        db_service.init_db()
        logger.info("Database initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize service on startup: {str(e)}")
        raise


# ============================================================================
# Health Check Endpoint
# ============================================================================

@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        Status of the service
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


# ============================================================================
# Document Upload Endpoint
# ============================================================================

@app.post(
    "/upload",
    response_model=UploadResponse,
    summary="Upload a document",
    tags=["Documents"]
)
async def upload_document(
    file: UploadFile = File(..., description="Document file to upload"),
    document_type: str = Query(None, description="Optional document type classification"),
    property_id: str = Query(None, description="Optional property ID reference")
) -> UploadResponse:
    """
    Upload a document and extract text content.

    Supports formats: PDF, DOCX, PNG, TXT

    - **file**: Multipart file upload (required)
    - **document_type**: Optional classification (e.g., "listing", "report")
    - **property_id**: Optional reference to property ID

    Returns:
        Upload response with document ID and status

    Raises:
        HTTPException: For validation or processing errors
    """
    try:
        logger.info(f"Received upload request for file: {file.filename}")

        # Read file content
        content = await file.read()

        if not content:
            logger.warning("Upload failed: empty file content")
            raise HTTPException(
                status_code=400,
                detail="File content is empty"
            )

        # Process upload through service
        result = upload_service.process_upload(
            filename=file.filename,
            file_content=content,
            document_type=document_type,
            property_id=property_id
        )

        if not result['success']:
            logger.warning(f"Upload processing failed: {result['error']}")
            raise HTTPException(
                status_code=400,
                detail=result['error'] or result['message']
            )

        logger.info(f"Upload successful: {file.filename} (ID: {result['document_id']})")
        return UploadResponse(
            success=True,
            message=result['message'],
            document_id=result['document_id'],
            filename=result['filename']
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during upload: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during file upload"
        )


# ============================================================================
# Document Health Check Endpoint
# ============================================================================

@app.get(
    "/documents/{document_id}/health",
    summary="Get document extraction health report",
    tags=["Documents"]
)
async def get_document_health(document_id: int):
    """
    Get health assessment for document text extraction.

    Provides detailed metrics about the quality and integrity of extracted text.
    """
    try:
        logger.info(f"Generating health report for document: {document_id}")

        # Verify document exists
        document = db_service.get_document(document_id)
        if not document:
            logger.warning(f"Document not found: {document_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Document with ID {document_id} not found"
            )

        # Get extracted text
        extracted_text = db_service.get_document_text(document_id)

        if not extracted_text:
            logger.warning(f"No extracted text found for document: {document_id}")
            return {
                "document_id": document_id,
                "filename": document.filename,
                "file_format": document.file_format,
                "extraction_status": "no_text",
                "health_score": 0,
                "message": "No extracted text found for this document"
            }

        # Generate health assessment
        text_to_assess = extracted_text.raw_text or ""
        health_report = text_validator.get_text_health_score(text_to_assess)

        return {
            "document_id": document_id,
            "filename": document.filename,
            "file_format": document.file_format,
            "extraction_status": extracted_text.extraction_status,
            "extraction_timestamp": extracted_text.extraction_timestamp,
            "health_score": health_report['score'],
            "is_valid": health_report['is_valid'],
            "metrics": {
                "length": health_report['length'],
                "word_count": health_report['word_count'],
                "line_count": health_report['line_count'],
                "unique_chars": health_report['unique_chars'],
                "null_bytes": health_report['null_bytes'],
                "control_chars": health_report['control_chars'],
                "encoding_issues": health_report['encoding_issues']
            },
            "warnings": health_report['warnings']
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating health report: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error generating health report"
        )


@app.get(
    "/system/status",
    summary="Get system status including dependencies",
    tags=["System"]
)
async def get_system_status():
    """Get comprehensive system status."""
    try:
        logger.info("Generating system status report...")

        format_support = dependency_checker.get_format_support_status()

        return {
            "status": "healthy",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "format_support": format_support,
            "debug_mode": settings.DEBUG
        }

    except Exception as e:
        logger.error(f"Error generating system status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error generating system status"
        )


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level=settings.LOG_LEVEL.lower()
    )
```

**Key Concepts**:

- **Endpoint**: A URL where clients send requests (like "/upload")
- **HTTPException**: An error response sent back to the client
- **Decorator** (@app.post, @app.get): Says "this function handles these requests"
- **Startup event**: Code that runs when application starts

---

## Testing What You Built

### Create Tests

Create `tests/test_upload.py`:

```python
"""
Tests for upload functionality.
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check():
    """Test that health endpoint works."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_system_status():
    """Test system status endpoint."""
    response = client.get("/system/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "format_support" in data
```

Create `scripts/test_basic.py`:

```python
#!/usr/bin/env python3
"""
Basic functionality tests - verify imports work.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test that all main modules can be imported."""
    print("Testing imports...")
    try:
        from models import Document, ExtractedText
        print("✅ Models imported successfully")

        from services.file_storage import file_storage
        print("✅ File storage service imported")

        from services.text_extraction import text_extraction
        print("✅ Text extraction service imported")

        from services.dependency_checker import dependency_checker
        print("✅ Dependency checker imported")

        from services.text_validator import text_validator
        print("✅ Text validator imported")

        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
```

Run tests:

```bash
python scripts/test_basic.py
python -m pytest tests/
```

---

## Running the Application

### Step 1: Create Environment File

Create `.env`:

```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/document_management
ALLOWED_FORMATS=["pdf", "docx", "png", "txt"]
MAX_FILE_SIZE=52428800
UPLOAD_DIR=./uploads
LOG_DIR=./logs
LOG_LEVEL=INFO
```

### Step 2: Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE document_management;

# Exit
\q
```

### Step 3: Run the Server

```bash
python main.py
```

You should see:

```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 4: Test Upload

```bash
# Create a test file
echo "This is a test document" > test.txt

# Upload it
curl -X POST "http://localhost:8000/upload" \
  -F "file=@test.txt" \
  -F "document_type=test"
```

You should get back:

```json
{
  "success": true,
  "message": "Document uploaded and processed successfully",
  "document_id": 1,
  "filename": "test.txt"
}
```

### Step 5: Check Health

```bash
curl http://localhost:8000/documents/1/health
```

Returns extraction quality metrics!

---

## Glossary of Technical Terms

| Term                    | Simple Explanation                            | Example                                           |
| ----------------------- | --------------------------------------------- | ------------------------------------------------- |
| **API**                 | Interface for programs to talk to each other  | `/upload` is an API endpoint                      |
| **Database**            | Organized storage for data                    | PostgreSQL stores document info                   |
| **FastAPI**             | Framework for building web APIs quickly       | What we use to handle web requests                |
| **Endpoint**            | A URL where clients send requests             | `/health`, `/upload`                              |
| **ORM**                 | Tool to work with databases from code         | SQLAlchemy - write Python instead of SQL          |
| **Session**             | A conversation with the database              | Like a phone call - open, talk, close             |
| **Commit**              | Save changes to database permanently          | After inserting data, commit it                   |
| **Rollback**            | Undo changes if something goes wrong          | If error occurs, rollback transactions            |
| **Migration**           | Process of moving/changing database structure | (Not used in Stage 1, but important later)        |
| **Virtual Environment** | Isolated Python installation                  | Keeps project dependencies separate               |
| **Decorator**           | Function wrapper that adds functionality      | `@app.post("/upload")`                            |
| **Logging**             | Recording what the program does               | For debugging and monitoring                      |
| **Exception Handling**  | Catching and responding to errors             | Try/except blocks                                 |
| **Timeout**             | Stop a process if it takes too long           | OCR times out after 90 seconds                    |
| **Fallback**            | Plan B if Plan A fails                        | Use PyPDF2 if pdfplumber unavailable              |
| **OCR**                 | Technology that reads text from images        | Converts images with text to readable text        |
| **Encoding**            | How text is stored as bytes                   | UTF-8 is most common (supports all languages)     |
| **Null Byte**           | Special character indicating "nothing"        | Indicates corrupted file                          |
| **Index**               | Speeds up database searches                   | Like index in a book                              |
| **Foreign Key**         | Link between tables                           | document_id in extracted_texts links to documents |

---

## Summary

You've built a complete **document text extraction system** from scratch that:

✅ **Accepts file uploads** (PDF, DOCX, PNG, TXT)  
✅ **Extracts text** (using appropriate tools for each format)  
✅ **Validates quality** (checks if text is clean and valid)  
✅ **Stores everything** (both files and extracted text)  
✅ **Provides APIs** (so other code can use the system)  
✅ **Checks health** (gives quality scores)  
✅ **Handles errors** (gracefully)

### Next Steps (Stage 2)

Once you're comfortable with Stage 1, Stage 2 will:

- Analyze extracted text for **materials** (what the building is made of)
- Identify **cost-cutting risks** (substandard materials)
- Generate **property insights** (construction quality assessment)

---

**Congratulations!** You've completed Stage 1 of the Housing Investment Analysis Platform backend. You now have a production-ready document text extraction system! 🎉
