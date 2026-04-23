#!/usr/bin/env python3
"""
Basic functionality tests for the document management system.
This script validates that all core components work without requiring pytest.
"""
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))


def _check_imports() -> bool:
    """Test that all main modules can be imported."""
    print("Testing imports...")
    try:
        from models import (
            Document, ExtractedText, VectorEmbedding,
            SearchResult, SemanticSearchResponse
        )
        print("✅ Models imported successfully")
        
        from services.file_storage import file_storage
        print("✅ File storage service imported")
        
        from services.text_extraction import text_extraction
        print("✅ Text extraction service imported")
        
        from services.upload_service import upload_service
        print("✅ Upload service imported")
        
        from services.vector_service import vector_service
        print("✅ Vector service imported")
        
        from services.vector_index import vector_index_manager
        print("✅ Vector index manager imported")
        
        from services.database import db_service
        print("✅ Database service imported")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def test_imports() -> None:
    assert _check_imports()


def _check_vector_service() -> bool:
    """Test vector service basic functionality."""
    print("\nTesting vector service...")
    try:
        from services.vector_service import vector_service
        
        # Test text chunking
        text = "word " * 50  # Create text longer than default chunk size
        chunks = vector_service.chunk_text(text, chunk_size=30, overlap=5)
        
        if len(chunks) > 0:
            print(f"✅ Text chunking works (created {len(chunks)} chunks)")
        else:
            print("❌ Text chunking failed - no chunks created")
            return False
        
        # Test embedding generation
        test_texts = ["hello world", "this is a test", "semantic search"]
        embeddings = vector_service.generate_embeddings(test_texts)
        
        if embeddings.shape == (3, 384):
            print(f"✅ Embedding generation works (shape: {embeddings.shape})")
        else:
            print(f"❌ Embedding generation failed (expected (3, 384), got {embeddings.shape})")
            return False
        
        # Test single text embedding
        single_embedding = vector_service.get_embedding_for_text("test text")
        if single_embedding.shape == (384,):
            print(f"✅ Single text embedding works (shape: {single_embedding.shape})")
        else:
            print(f"❌ Single text embedding failed (expected (384,), got {single_embedding.shape})")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Vector service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_vector_service() -> None:
    assert _check_vector_service()


def _check_vector_index() -> bool:
    """Test vector index manager."""
    print("\nTesting vector index manager...")
    try:
        import numpy as np
        from services.vector_index import vector_index_manager
        
        # Create test embeddings
        doc_id = 999  # Use high ID to avoid conflicts
        embeddings = np.random.randn(5, 384).astype(np.float32)
        chunk_ids = [f"chunk_{i}" for i in range(5)]
        chunk_texts = [f"text {i}" for i in range(5)]
        
        # Test index creation and vector addition
        vector_index_manager.create_index(doc_id)
        vector_index_manager.add_vectors(doc_id, embeddings, chunk_ids, chunk_texts)
        
        # Test search
        query_embedding = embeddings[0]
        result_ids, distances = vector_index_manager.search(doc_id, query_embedding, k=3)
        
        if len(result_ids) == 3 and len(distances) == 3:
            print(f"✅ Vector index creation, insertion, and search work")
        else:
            print(f"❌ Vector index search failed (expected 3 results, got {len(result_ids)})")
            return False
        
        # Test cross-document search
        doc_id2 = 1000
        vector_index_manager.create_index(doc_id2)
        vector_index_manager.add_vectors(doc_id2, embeddings, chunk_ids, chunk_texts)
        
        cross_results = vector_index_manager.search_across_documents(query_embedding, k=5)
        if len(cross_results) > 0:
            print(f"✅ Cross-document search works (found {len(cross_results)} results)")
        else:
            print("❌ Cross-document search failed")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Vector index test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_vector_index() -> None:
    assert _check_vector_index()


def _check_file_storage() -> bool:
    """Test file storage functionality."""
    print("\nTesting file storage...")
    try:
        from services.file_storage import file_storage
        import tempfile
        
        # Test file saving
        test_content = b"This is test file content"
        filename = "test_document.txt"
        
        file_path = file_storage.save_file(test_content, filename)
        
        if file_path and Path(file_path).exists():
            print(f"✅ File storage works (saved to {file_path})")
            # Clean up
            Path(file_path).unlink()
            return True
        else:
            print("❌ File storage failed")
            return False
    except Exception as e:
        print(f"❌ File storage test failed: {e}")
        return False


def test_file_storage() -> None:
    assert _check_file_storage()


def _check_text_extraction() -> bool:
    """Test text extraction service."""
    print("\nTesting text extraction...")
    try:
        from services.text_extraction import text_extraction
        from pathlib import Path
        import tempfile
        
        # Create a temporary TXT file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is test content for text extraction.\nIt has multiple lines.\n")
            temp_file = f.name
        
        try:
            # Test text extraction
            text, status, error = text_extraction.extract_text(temp_file, 'txt')
            
            if status == 'success' and 'test content' in text:
                print(f"✅ Text extraction works (extracted {len(text)} characters)")
                return True
            else:
                print(f"❌ Text extraction failed: {error}")
                return False
        finally:
            Path(temp_file).unlink()
    except Exception as e:
        print(f"❌ Text extraction test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_text_extraction() -> None:
    assert _check_text_extraction()

def main():
    """Run all tests."""
    print("=" * 60)
    print("DOCUMENT MANAGEMENT SYSTEM - BASIC FUNCTIONALITY TESTS")
    print("=" * 60)
    
    tests = [
        ("Module Imports", _check_imports),
        ("File Storage", _check_file_storage),
        ("Text Extraction", _check_text_extraction),
        ("Vector Service", _check_vector_service),
        ("Vector Index Manager", _check_vector_index),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! System is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
