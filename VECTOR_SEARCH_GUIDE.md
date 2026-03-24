# Vector Search with FAISS - Implementation Guide

## Overview

This document describes the FAISS (Facebook AI Similarity Search) integration for semantic search capabilities in the document management service. The system enables users to search across documents using natural language queries, finding semantically similar content rather than just keyword matches.

## Architecture

### Components

1. **Vector Index Manager** (`services/vector_index.py`)
   - Manages FAISS vector indices
   - Handles persistence (save/load) of indices
   - Performs similarity searches within and across documents

2. **Vector Service** (`services/vector_service.py`)
   - Generates embeddings using sentence-transformers (all-MiniLM-L6-v2)
   - Chunks text into overlapping segments
   - Orchestrates embedding and search operations
   - Works with VectorIndexManager to store and retrieve embeddings

3. **Database Integration** (`services/database.py`)
   - Stores embedding metadata in PostgreSQL
   - Tracks which documents have been embedded
   - Records embedding parameters (chunk size, model, etc.)

4. **Upload Pipeline** (`services/upload_service.py`)
   - Automatically generates embeddings after text extraction
   - Integrates seamlessly into existing upload workflow

5. **Search Endpoints** (`main.py`)
   - `/search/document/{document_id}` - Search within a single document
   - `/search` - Search across all documents or subset

## Technical Specifications

### Embedding Model

- **Model**: `all-MiniLM-L6-v2` (from sentence-transformers)
- **Embedding Dimension**: 384 dimensions
- **Model Size**: ~33 MB (lightweight, suitable for MVP)
- **Performance**: ~100 embeddings/second on CPU

### Vector Index

- **Type**: FAISS IndexFlatL2
- **Distance Metric**: Euclidean (L2) distance
- **Similarity Score**: `1 / (1 + distance)` for normalized comparison

### Text Chunking

- **Default Chunk Size**: 512 characters
- **Default Overlap**: 50 characters
- **Purpose**: Preserve context while creating focused search units

## Database Schema

### VectorEmbedding Table

```sql
CREATE TABLE vector_embeddings (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL UNIQUE REFERENCES documents(id),
    num_chunks INTEGER NOT NULL,
    embedding_model VARCHAR(100) NOT NULL,
    chunk_size INTEGER NOT NULL DEFAULT 512,
    chunk_overlap INTEGER NOT NULL DEFAULT 50,
    embedding_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Fields:**

- `id`: Primary key
- `document_id`: Reference to documents table (unique - one embedding per doc)
- `num_chunks`: Number of chunks created for this document
- `embedding_model`: Model used for embeddings (tracking version)
- `chunk_size`: Characters per chunk (for reproducibility)
- `chunk_overlap`: Character overlap between chunks
- `embedding_timestamp`: When embeddings were generated

## Workflow

### 1. Document Upload & Embedding

```
User Upload
    ↓
File Validation & Storage
    ↓
Text Extraction (PDF/DOCX/PNG/TXT)
    ↓
Save Extracted Text to DB
    ↓
[NEW] Generate Vector Embeddings
    │
    ├─ 1. Split text into chunks (512 chars, 50-char overlap)
    ├─ 2. Generate embeddings for all chunks (384-dim vectors)
    ├─ 3. Store in FAISS index (in-memory)
    ├─ 4. Save index to disk (./vector_indices/)
    └─ 5. Save metadata to PostgreSQL
    ↓
Document Ready for Search
```

### 2. Single-Document Search

```
User Query: "Find information about bedrooms"
    ↓
Generate Query Embedding (384-dim vector)
    ↓
FAISS Search in Document Index
    ├─ k=5: Return 5 most similar chunks
    └─ Distance metric: L2 (Euclidean)
    ↓
Convert Distance to Similarity Score
    └─ similarity = 1 / (1 + distance)
    ↓
Return Ranked Results [chunk_id, text, similarity_score]
```

### 3. Cross-Document Search

```
User Query: "Find properties with modern amenities"
    ↓
Generate Query Embedding
    ↓
Search All Document Indices
    ├─ For each document: Get top 10 results
    ├─ Collect all results
    └─ Sort by distance (best matches first)
    ↓
Return Top k Results Across All Documents
    └─ Format: [document_id, chunk_id, text, similarity_score]
```

## API Endpoints

### Search Within Document

```
POST /search/document/{document_id}?query=<query>&k=<k>

Parameters:
  - document_id (path): Document to search in
  - query (query): Search query text (required, min 1 char)
  - k (query): Number of results (default: 5, max: 20)

Response:
{
  "success": true,
  "query": "bedrooms",
  "num_results": 3,
  "results": [
    {
      "rank": 1,
      "document_id": null,
      "chunk_id": "chunk_5",
      "distance": 0.245,
      "similarity_score": 0.803
    },
    ...
  ]
}
```

### Search Across Documents

```
POST /search?query=<query>&document_ids=<ids>&k=<k>

Parameters:
  - query (query): Search query text (required, min 1 char)
  - document_ids (query): Comma-separated doc IDs to limit search (optional)
  - k (query): Number of results (default: 10, max: 50)

Examples:
  /search?query=modern%20kitchen&k=5
  /search?query=bedrooms&document_ids=1,2,3&k=10

Response:
{
  "success": true,
  "query": "modern kitchen",
  "num_results": 2,
  "results": [
    {
      "rank": 1,
      "document_id": 3,
      "chunk_id": "chunk_12",
      "distance": 0.156,
      "similarity_score": 0.865
    },
    ...
  ]
}
```

## File Structure

```
backend/
├── services/
│   ├── vector_index.py          # FAISS index management
│   ├── vector_service.py         # Embedding & search orchestration
│   ├── upload_service.py         # Updated with embedding integration
│   └── database.py               # Updated with vector metadata methods
├── models.py                     # Updated with VectorEmbedding table
├── main.py                       # Updated with search endpoints
├── tests/__init__.py             # Updated with vector search tests
└── vector_indices/               # Directory for FAISS indices (created at runtime)
    ├── document_1.index          # FAISS index file
    ├── document_1.pkl            # Metadata (chunk IDs and texts)
    └── ...
```

## Performance Characteristics

### Embedding Generation

- ~0.5-2 seconds per document (depending on text length)
- CPU-based processing (no GPU required)
- Documents up to 50,000 characters: <5 seconds
- 300 pages (typical property doc): ~2-3 seconds

### Search Performance

- Single-document search: <100ms (typical)
- Cross-document search: <500ms (up to 100 documents)
- Results are not real-time indexed (indices are in-memory)

### Storage

- Per document: ~2.4-3.6 MB (for 300-page property)
- N documents: N × 3 MB (typical)
- Indices stored as .index + .pkl files on disk

## Limitations & Considerations

### Current Limitations

1. **In-Memory Indices**: All indices loaded in memory on startup
   - Works fine for <1GB of embeddings
   - Scale limit: ~10,000 documents on typical hardware

2. **No Real-Time Indexing**: Changes to documents require re-generation

3. **Single Model**: Using all-MiniLM-L6-v2
   - Good general-purpose model (384-dim)
   - Can be upgraded to larger models later

### Future Improvements

1. **Persistent Vector DB**: Migrate to Qdrant/Weaviate for production
2. **Batch Processing**: Queue embeddings during upload surge
3. **Multi-Model Support**: Allow different embedding models
4. **Lazy Loading**: Load indices on-demand instead of full memory
5. **Incremental Updates**: Update embeddings for modified documents

## Configuration

### Environment Variables

```bash
# In .env
VECTOR_INDEX_DIR=./vector_indices    # Directory for FAISS indices
EMBEDDING_MODEL=all-MiniLM-L6-v2     # Sentence-transformers model
CHUNK_SIZE=512                       # Text chunk size in characters
CHUNK_OVERLAP=50                    # Overlap between chunks
```

### Customization

Modify in `vector_service.py`:

```python
class VectorService:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        # Change model_name to use different embeddings
        # Options: all-mpnet-base-v2, all-distilroberta-v1, etc.
```

## Testing

### Run Vector Search Tests

```bash
# Run all vector tests
pytest tests/__init__.py::TestVectorEmbedding -v
pytest tests/__init__.py::TestVectorService -v

# Run specific test
pytest tests/__init__.py::TestVectorEmbedding::test_search_within_document -v

# Full test suite
pytest tests/__init__.py -v
```

### Manual Testing

#### 1. Upload Document

```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@property.txt" \
  -F "document_type=property_listing"
# Response:
# {"success": true, "document_id": 1, ...}
```

#### 2. Search Within Document

```bash
curl -X POST "http://localhost:8000/search/document/1?query=bedrooms&k=5"
# Response:
# {"success": true, "num_results": 3, "results": [...]}
```

#### 3. Search All Documents

```bash
curl -X POST "http://localhost:8000/search?query=modern%20kitchen&k=10"
# Response:
# {"success": true, "num_results": 5, "results": [...]}
```

#### 4. Search Specific Documents

```bash
curl -X POST "http://localhost:8000/search?query=price&document_ids=1,3,5&k=5"
```

## Troubleshooting

### 1. Embeddings Not Generated

**Symptom**: Upload succeeds but search returns no results
**Solution**:

- Check logs for embedding errors
- Verify text was extracted (check `/documents/{id}/text` endpoint)
- Re-generate embeddings or re-upload document

### 2. Out of Memory

**Symptom**: Service crashes with memory error
**Solution**:

- Reduce document size or chunk overlap
- Implement lazy loading of indices
- Scale to persistent vector DB (Qdrant)

### 3. Search Returns Poor Results

**Symptom**: Results don't match query semantically
**Possible causes**:

- Document text is too short (less context)
- Topic mismatch (query vs document domain)
- Embedding model limitations (try larger model)
  **Solution**: Increase chunk overlap or use larger embedding model

### 4. Slow Search Performance

**Symptom**: Search takes >1 second
**Solution**:

- Reduce k parameter
- Filter documents with `document_ids` parameter
- Migrate to GPU-enabled setup

## Integration Examples

### Example 1: Property Search

```python
# User wants to find properties with "modern kitchen"
query = "modern kitchen with updated appliances"
results = POST /search?query={query}&k=10

# Returns top 10 results across all property documents
# with similarity scores showing best matches first
```

### Example 2: Document Analysis

```python
# Extract summary from document
doc_id = 42
queries = ["price", "location", "features", "condition"]

for query in queries:
    results = POST /search/document/{doc_id}?query={query}&k=3
    # Process top 3 results for each aspect
```

### Example 3: Duplicate Detection

```python
# Find similar properties
query = document_1.extract_section("description")
results = POST /search?query={query}&document_ids=2,3,4,5&k=5

# If similarity_score > 0.85, likely similar/duplicate
```

## Dependencies

```
faiss-cpu==1.7.4
sentence-transformers==2.2.2
numpy==1.24.3
scipy==1.11.4
```

## Related Documentation

- [Main README](README.md)
- [API Documentation](API_DOCUMENTATION.md)
- [Deployment Guide](DEPLOYMENT_GUIDE.md)
- [Database Schema](DATABASE_SCHEMA.md)
