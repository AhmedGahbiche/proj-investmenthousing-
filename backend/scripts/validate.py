#!/usr/bin/env python3
"""Quick import validation"""
import sys

print("=" * 60)
print("IMPORT VALIDATION TEST")
print("=" * 60)

errors = []

try:
    print("\n1. Testing model imports...")
    from models import (
        Document, ExtractedText, VectorEmbedding,
        SearchResult, SemanticSearchResponse
    )
    print("✅ Models imported successfully")
except Exception as e:
    errors.append(f"Model import failed: {e}")
    print(f"❌ {errors[-1]}")

try:
    print("\n2. Testing service imports...")
    from services.file_storage import file_storage
    from services.text_extraction import text_extraction
    from services.upload_service import upload_service
    from services.database import db_service
    print("✅ Services imported successfully")
except Exception as e:
    errors.append(f"Service import failed: {e}")
    print(f"❌ {errors[-1]}")

try:
    print("\n3. Testing vector imports...")
    from services.vector_index import vector_index_manager
    # Don't import vector_service yet (slow due to model loading)
    print("✅ Vector index manager imported successfully")
except Exception as e:
    errors.append(f"Vector import failed: {e}")
    print(f"❌ {errors[-1]}")

try:
    print("\n4. Testing FastAPI...")
    from main import app
    print("✅ FastAPI app imported successfully")
except Exception as e:
    errors.append(f"FastAPI import failed: {e}")
    print(f"❌ {errors[-1]}")

print("\n" + "=" * 60)
if errors:
    print(f"❌ {len(errors)} ERROR(S) FOUND")
    print("=" * 60)
    for error in errors:
        print(f"  - {error}")
    sys.exit(1)
else:
    print("✅ ALL IMPORTS SUCCESSFUL!")
    print("=" * 60)
    print("\nSystem is ready to run.")
    sys.exit(0)
