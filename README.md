# Taqim Backend - Document and Due Diligence Service

Backend service for real-estate document ingestion, semantic retrieval, and asynchronous AI-powered due diligence analysis.

## 1. What this service does

This backend currently supports:

- Document upload and storage
- Text extraction from PDF, DOCX, PNG (OCR), and TXT
- Text sanitization and validation
- Chunking and embedding into FAISS
- Metadata and analysis persistence in PostgreSQL
- Asynchronous analysis jobs via Celery + Redis
- OpenAI-powered legal, risk, valuation, and final due-diligence synthesis

## 2. Architecture overview

### Runtime components

- API: FastAPI application
- Database: PostgreSQL
- Queue broker/result backend: Redis
- Worker: Celery worker processing analysis tasks
- Vector stores:
  - Document vectors: `./vector_indices`
  - Regulation corpus vectors: `./regulation_indices`

### High-level flow

1. Client uploads a document via `/upload`.
2. Service stores file, extracts text, validates text, and saves metadata to PostgreSQL.
3. Service chunks text and stores embeddings in FAISS.
4. Client triggers analysis via `/analyze`.
5. Celery worker loads document text, retrieves top-k regulation context from dedicated FAISS corpus, and runs AI analysis modules in parallel.
6. Worker persists module outputs and final decision in PostgreSQL and marks analysis status as `done` or `failed`.
7. Client polls `/analyze/{analysis_id}` for status and outputs.

### Architecture diagram

![Taqim Backend Architecture](docs/architecture.svg)

The diagram source file is available at [docs/architecture.svg](docs/architecture.svg).

## 3. Project structure

- `main.py`: FastAPI app and HTTP endpoints
- `config.py`: configuration settings from environment
- `models.py`: SQLAlchemy and Pydantic models
- `celery_app.py`: Celery app configuration
- `worker.py`: Celery worker entrypoint
- `services/database.py`: DB persistence and query methods
- `services/upload_service.py`: upload orchestration
- `services/text_extraction.py`: extraction handlers
- `services/text_validator.py`: text validation/sanitization
- `services/vector_service.py`: chunking/embedding/search orchestration
- `services/vector_index.py`: FAISS index storage/search
- `services/regulation_retrieval.py`: dedicated regulation corpus retrieval
- `services/analysis_intelligence.py`: OpenAI-driven analysis intelligence
- `services/analysis_tasks.py`: async analysis task pipeline
- `docker-compose.yml`: API + Postgres + Redis + Worker stack

## 4. Data model (current)

### Core ingestion tables

- `documents`
  - `id`, `filename`, `file_format`, `file_path`, `file_size`, `upload_timestamp`, `document_type`, `property_id`
- `extracted_texts`
  - `id`, `document_id`, `raw_text`, `extraction_timestamp`, `extraction_status`, `extraction_error`
- `vector_embeddings`
  - `id`, `document_id`, `num_chunks`, `embedding_model`, `chunk_size`, `chunk_overlap`, `embedding_timestamp`

### Analysis tables

- `analyses`
  - `id`, `document_id`, `status`, `started_at`, `finished_at`, `error`, `model_version`
- `analysis_outputs`
  - `analysis_id`, `legal_json`, `risk_json`, `valuation_json`, `final_json`
- `analysis_events`
  - `id`, `analysis_id`, `stage`, `timestamp`, `payload`

## 5. Implemented APIs

### Health and system

- `GET /health`
- `GET /system/status`

### Documents

- `POST /upload`
- `GET /documents`
- `GET /documents/{document_id}`
- `GET /documents/{document_id}/text`
- `GET /documents/{document_id}/full`
- `GET /documents/{document_id}/health`

### Search

- `POST /search/document/{document_id}`
- `POST /search`

### Analysis

- `POST /analyze`
  - Creates an `analyses` row with `queued` status
  - Enqueues Celery task `run_analysis_task(document_id, analysis_id)`
- `GET /analyze/{analysis_id}`
  - Returns status and outputs (when available)

### Reports

- `POST /reports/{analysis_id}`
- `GET /reports/{analysis_id}/html`
- `GET /reports/{analysis_id}/txt`
- `GET /reports/{analysis_id}/pdf`

## 5.1 Frontend/Backend Contract Matrix

Frontend pages are expected to call the production backend (`main.py`) unless explicitly running a mock flow.

| Frontend flow | Route used | Production backend support |
|---|---|---|
| Upload document | `POST /upload` | Yes |
| Start single-doc analysis | `POST /analyze` | Yes |
| Start property analysis | `POST /analyze/property` | Yes |
| Poll analysis status | `GET /analyze/{analysis_id}` | Yes |
| HTML report | `GET /reports/{analysis_id}/html` | Yes |
| TXT report | `GET /reports/{analysis_id}/txt` | Yes |
| PDF report | `GET /reports/{analysis_id}/pdf` | Yes |

If you run the frontend against `mock_backend.py`, behavior can differ from production and should only be used for isolated UI prototyping.

## 6. Analysis intelligence layer (implemented)

The worker now uses real OpenAI calls (not placeholder heuristics):

- Legal analysis module
- Risk analysis module
- Valuation analysis module
- Final synthesis module

Each module returns structured JSON and is persisted in `analysis_outputs`.

Current implementation details:

- Parallel execution for legal/risk/valuation modules in the Celery task
- Dedicated prompt strategy for Tunisian real-estate due diligence
- Regulation context included in prompts from dedicated FAISS corpus retrieval
- Final synthesis combines module outputs into overall go/no-go style decision payload

## 7. Environment variables

Use `.env` (copy from `.env.example`) and set at least:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/document_management
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1

OPENAI_API_KEY=YOUR_KEY_HERE
OPENAI_MODEL=gpt-5
OPENAI_BASE_URL=
OPENAI_TIMEOUT_SECONDS=120
```

## 8. Run with Docker (recommended)

```bash
docker compose up --build
```

Services:

- API: http://localhost:8000
- Postgres: localhost:5432
- Redis: localhost:6379

## 9. Run locally (manual)

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Start API:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

3. Start worker:

```bash
celery -A worker.celery_app worker --loglevel=info
```

## 9.1 Frontend Local Run (Recommended)

1. Create frontend env file from `frontend/.env.example`.
2. Set `NEXT_PUBLIC_BACKEND_URL` to `http://localhost:8000`.
3. Ensure `AUTH_SECRET` matches backend `.env` value.
4. Start frontend:

```bash
cd frontend
npm install
npm run dev
```

Use the production backend (`main.py`) for end-to-end verification. Keep `mock_backend.py` only for controlled mock-only UI checks.

## 10. Example requests

### Upload document

```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@sample.txt" \
  -F "document_type=listing" \
  -F "property_id=PROP-001"
```

### Trigger analysis

```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"document_id": 1, "model_version": "v1"}'
```

### Check analysis status

```bash
curl "http://localhost:8000/analyze/1"
```

## 11. What is complete vs pending

### Complete

- Document ingestion and extraction pipeline
- FAISS indexing and semantic search
- Analysis persistence model
- Async analysis orchestration with Celery
- OpenAI-backed analysis intelligence layer
- Status tracking and output retrieval endpoints
- Report generation and download endpoints (HTML/TXT/PDF)
- Authentication and authorization on protected routes (JWT, admin role gate, and property ownership checks)

### Pending

- User notification on analysis completion
- Regulation corpus ingestion API (service exists, endpoint not added yet)
- Stronger schema validation/guardrails for model outputs

## 12. Notes

- Keep API keys in `.env` only; do not commit secrets.
- Configure `CLIENT_ALLOWED_PROPERTY_IDS` in `.env` to scope client-role access by property.
- Ensure regulation corpus is indexed in `regulation_indices` for meaningful retrieval context.
- For production, add observability, rate limits, auth, and stricter validation before enabling public traffic.
