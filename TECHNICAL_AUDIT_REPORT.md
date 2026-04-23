# Technical Audit Report

Scope covered: Python backend, Next.js frontend, test suite layout, and dependency/security tooling.
Runtime checks executed: pytest -q (10 passed), frontend npm audit --omit=dev (0 vulnerabilities), frontend npm run build (Next.js 16.2.4 successful), and pip_audit -r requirements.txt (no known vulnerabilities).

## 1. Architecture & Design - High

### Issue 1: API contract split between production backend and mock backend
- Status: Resolved
- Evidence:
  - [frontend/app/analysis/page.tsx](frontend/app/analysis/page.tsx#L69)
  - [frontend/app/client/page.tsx](frontend/app/client/page.tsx#L146)
  - [frontend/app/report/[analysisId]/page.tsx](frontend/app/report/%5BanalysisId%5D/page.tsx#L115)
  - [main.py](main.py#L158)
  - [main.py](main.py#L820)
  - [main.py](main.py#L882)
  - [main.py](main.py#L899)
  - [mock_backend.py](mock_backend.py#L1273)
  - [mock_backend.py](mock_backend.py#L1372)
- Recommendation:
  - Define one canonical API contract (OpenAPI first).
  - Generate typed frontend client from the contract.
  - Remove mock-only frontend dependencies or add parity routes in production backend.

### Issue 2: Oversized modules with mixed responsibilities
- Status: Resolved
- Evidence:
  - [main.py](main.py#L1) handles startup, document APIs, search, analysis, reports, and exception handlers.
  - [mock_backend.py](mock_backend.py#L953) includes very large report generation and broad unrelated logic.
- Recommendation:
  - Split by bounded contexts: documents, search, analysis, reports, system.
  - Move shared response/error handling to common utilities.

### Issue 3: Import-time singleton initialization increases coupling
- Status: Resolved
- Evidence:
  - [services/database.py](services/database.py#L486)
  - [services/vector_service.py](services/vector_service.py#L276)
  - [services/upload_service.py](services/upload_service.py#L244)
  - [services/file_storage.py](services/file_storage.py#L150)
- Recommendation:
  - Use dependency injection and lazy initialization.
  - Avoid infra-heavy side effects at import time.

### Issue 4: Circular dependency status
- Status: Resolved
- Evidence:
  - Core import graph appears one-directional in current scan (e.g., [services/analysis_tasks.py](services/analysis_tasks.py#L8), [services/regulation_retrieval.py](services/regulation_retrieval.py#L7), [services/vector_service.py](services/vector_service.py#L9)).
- Recommendation:
  - Add import-linter checks in CI to prevent future cycles.

## 2. Code Quality - High

### Issue 1: DRY violations in frontend upload/analysis flows
- Status: Resolved
- Evidence:
  - Upload loops duplicated in [frontend/app/analysis/page.tsx](frontend/app/analysis/page.tsx#L30) and [frontend/app/client/page.tsx](frontend/app/client/page.tsx#L83).
  - Property analysis handlers duplicated in [frontend/app/analysis/page.tsx](frontend/app/analysis/page.tsx#L61) and [frontend/app/client/page.tsx](frontend/app/client/page.tsx#L140).
- Recommendation:
  - Extract shared hooks/services (e.g., useDocumentUpload, useAnalysisPolling).

### Issue 2: Large functions/files reduce maintainability
- Status: Resolved
- Evidence:
  - [mock_backend.py](mock_backend.py#L953)
  - [services/upload_service.py](services/upload_service.py#L77)
  - [frontend/app/client/page.tsx](frontend/app/client/page.tsx#L42)
  - [frontend/app/analysis/page.tsx](frontend/app/analysis/page.tsx#L9)
- Recommendation:
  - Refactor into smaller pure functions and focused modules.

### Issue 3: Dead code / unused imports
- Status: Resolved
- Evidence:
  - [services/upload_service.py](services/upload_service.py#L6)
  - [services/upload_service.py](services/upload_service.py#L27)
  - [services/file_storage.py](services/file_storage.py#L7)
  - [services/text_validator.py](services/text_validator.py#L9)
  - [services/vector_index.py](services/vector_index.py#L6)
  - [services/dependency_checker.py](services/dependency_checker.py#L7)
- Recommendation:
  - Enforce lint rules (ruff/flake8/eslint) with no-unused checks in CI.

### Issue 4: Deprecated patterns in active code
- Status: Resolved
- Evidence:
  - [models.py](models.py#L6)
  - [models.py](models.py#L85)
  - [models.py](models.py#L97)
  - [models.py](models.py#L106)
  - [models.py](models.py#L209)
  - [main.py](main.py#L364)
  - [frontend/tsconfig.json](frontend/tsconfig.json#L17)
- Recommendation:
  - Migrate to SQLAlchemy 2 style APIs.
  - Migrate Pydantic config and model validation style.
  - Update tsconfig deprecation handling.

## 3. Security - Critical

### Issue 1: Hardcoded credentials and fallback auth secrets
- Status: Resolved
- Evidence:
  - [frontend/app/api/auth/login/route.ts](frontend/app/api/auth/login/route.ts#L7)
  - [frontend/app/api/auth/login/route.ts](frontend/app/api/auth/login/route.ts#L11)
  - [frontend/lib/auth.ts](frontend/lib/auth.ts#L12)
  - [frontend/app/login/page.tsx](frontend/app/login/page.tsx#L10)
  - [frontend/app/login/page.tsx](frontend/app/login/page.tsx#L104)
- Recommendation:
  - Remove hardcoded defaults.
  - Require env secrets at startup.
  - Store users in DB and hash passwords.

### Issue 2: Missing backend authz/authn protections
- Status: Resolved
- Evidence:
  - JWT middleware and role gate in [main.py](main.py#L130).
  - Ownership checks across document/analysis/search routes in [main.py](main.py#L264).
  - Report-route ownership checks in [routes/report_routes.py](routes/report_routes.py#L18).
  - Property-scope configuration via [config.py](config.py#L29) and [.env.example](.env.example#L29).
- Recommendation:
  - Expand from property-scope ownership to per-user ownership records when multi-user identity is introduced.

### Issue 3: Upload filename path traversal risk
- Status: Resolved
- Evidence:
  - [services/file_storage.py](services/file_storage.py#L39)
  - [services/file_storage.py](services/file_storage.py#L61)
- Recommendation:
  - Strip path components from filename.
  - Validate allowed characters.
  - Enforce storage path containment checks.

### Issue 4: Potential stored XSS in generated HTML reports
- Status: Resolved
- Evidence:
  - [services/report_generator.py](services/report_generator.py#L67)
  - [services/report_generator.py](services/report_generator.py#L72)
  - [services/report_generator.py](services/report_generator.py#L77)
  - [services/report_generator.py](services/report_generator.py#L82)
- Recommendation:
  - Escape all dynamic output.
  - Use safe template rendering with autoescape.

### Issue 5: Internal exception leakage to clients
- Status: Resolved
- Evidence:
  - [main.py](main.py#L879)
  - [main.py](main.py#L896)
  - [main.py](main.py#L913)
- Recommendation:
  - Return generic client-safe errors.
  - Log full internal details server-side only.

## 4. Performance - Medium

### Issue 1: Unbounded in-memory vector index growth
- Status: Resolved
- Evidence:
  - [services/vector_index.py](services/vector_index.py#L34)
  - [services/vector_index.py](services/vector_index.py#L101)
- Recommendation:
  - Add eviction and memory caps.
  - Consider external vector storage.

### Issue 2: Linear scan across document indices
- Status: Resolved
- Evidence:
  - Global centroid cache and candidate prefilter added in [services/vector_index.py](services/vector_index.py#L140).
  - Cross-document search now routes through candidate selection before per-document scan in [services/vector_index.py](services/vector_index.py#L307).
  - Prefilter tuning is configurable via [config.py](config.py#L42) and [.env.example](.env.example#L41).
- Recommendation:
  - Consider external vector DB sharding when corpus size materially exceeds single-node FAISS limits.

### Issue 3: Analysis tasks can block on external calls
- Status: Resolved
- Evidence:
  - [services/analysis_tasks.py](services/analysis_tasks.py#L40)
  - [services/analysis_tasks.py](services/analysis_tasks.py#L57)
- Recommendation:
  - Add explicit per-module timeouts and partial-failure handling.

### Issue 4: Sequential multi-file uploads in frontend
- Status: Resolved
- Evidence:
  - [frontend/app/analysis/page.tsx](frontend/app/analysis/page.tsx#L30)
  - [frontend/app/client/page.tsx](frontend/app/client/page.tsx#L83)
- Recommendation:
  - Use controlled concurrency and progress UI.

### Issue 5: Embedding model loads at import-time
- Status: Resolved
- Evidence:
  - [services/vector_service.py](services/vector_service.py#L276)
- Recommendation:
  - Lazy-load model on first use or isolate model loading in worker process.

## 5. Error Handling & Resilience - High

### Issue 1: Overly broad exception handling
- Status: Resolved
- Evidence:
  - Broad catch-all endpoint handlers were replaced with typed exception tuples in [main.py](main.py#L1).
  - Upload orchestration now maps typed storage/database/runtime failures in [services/upload_service.py](services/upload_service.py#L1).
  - File storage now raises a dedicated typed error instead of generic `Exception` wrappers in [services/file_storage.py](services/file_storage.py#L1).
- Recommendation:
  - Extend the same typed-mapping pattern to remaining non-core modules over time.

### Issue 2: Bare except block in cleanup path
- Status: Resolved
- Evidence:
  - [services/upload_service.py](services/upload_service.py#L154)
- Recommendation:
  - Replace with explicit exception handling and logging.

### Issue 3: Silent PDF generation failures
- Status: Resolved
- Evidence:
  - [services/report_generator.py](services/report_generator.py#L122)
- Recommendation:
  - Log failure details and return explicit partial-success state.

### Issue 4: Frontend/Backend status enum mismatch
- Status: Resolved
- Evidence:
  - Backend sets done in [services/analysis_tasks.py](services/analysis_tasks.py#L79)
  - Frontend waits for completed in [frontend/app/client/page.tsx](frontend/app/client/page.tsx#L196)
- Recommendation:
  - Standardize status enum and share typed contract between FE/BE.

## 6. Testing - Critical

### Issue 1: Test collection was broken in default pytest flow
- Status: Resolved
- Evidence:
  - Latest run: pytest -q reports 10 passed.
  - Tests now execute from dedicated module files in [tests/test_upload.py](tests/test_upload.py#L1).
- Recommendation:
  - Keep test collection in CI as a required gate.

### Issue 2: Tests stored in package init file
- Status: Resolved
- Evidence:
  - [tests/__init__.py](tests/__init__.py#L1) is now package scaffolding only.
  - [tests/test_upload.py](tests/test_upload.py#L1) contains active endpoint tests.
- Recommendation:
  - Continue splitting tests by domain as coverage grows.

### Issue 3: Weak/conditional assertions
- Status: Resolved
- Evidence:
  - Assertion-based test flow is now in [tests/test_upload.py](tests/test_upload.py#L1).
  - Scripted checks in [scripts/test_basic.py](scripts/test_basic.py#L1) now use assert in pytest-collected tests.
- Recommendation:
  - Keep assertion style strict and deterministic.

### Issue 4: Timing-based test synchronization
- Status: Resolved
- Evidence:
  - Legacy sleep-based tests were removed from [tests/__init__.py](tests/__init__.py#L1).
- Recommendation:
  - Use bounded polling helpers if async wait logic is reintroduced.

## 7. Documentation & Maintainability - Medium

### Issue 1: README does not capture FE/BE API divergence
- Status: Resolved
- Evidence:
  - [README.md](README.md#L92)
  - [README.md](README.md#L106)
  - [README.md](README.md#L109)
  - [frontend/app/report/[analysisId]/page.tsx](frontend/app/report/%5BanalysisId%5D/page.tsx#L115)
- Recommendation:
  - Add API contract matrix for production vs mock routes.

### Issue 2: Critical pending item documented but unresolved
- Status: Resolved
- Evidence:
  - Auth/authz milestone moved to complete section in [README.md](README.md#L252).
- Recommendation:
  - Keep ownership checks and auth validation as CI release gates.

### Issue 3: New-developer onboarding friction due dual backends
- Status: Resolved
- Evidence:
  - [main.py](main.py#L1)
  - [mock_backend.py](mock_backend.py#L1)
- Recommendation:
  - Publish one clear full-stack local run guide, including which backend to use.

## 8. Dependency Health - Critical

### Issue 1: Critical Next.js vulnerability in current frontend version
- Status: Resolved
- Evidence:
  - [frontend/package.json](frontend/package.json#L11) is on a patched Next.js 16.x line.
  - Latest run: frontend npm audit --omit=dev reports 0 vulnerabilities.
- Recommendation:
  - Keep npm audit in CI and during release preparation.

### Issue 2: Frontend dependencies significantly outdated
- Status: Resolved
- Evidence:
  - Major dependency upgrades are reflected in [frontend/package.json](frontend/package.json#L10).
  - Latest run: frontend npm run build completes successfully.
- Recommendation:
  - Continue staged upgrades with build and smoke-test validation.

### Issue 3: Backend dependency CVEs present
- Status: Resolved
- Evidence:
  - [requirements.txt](requirements.txt#L1) has patched pinned versions.
  - Latest run: pip_audit -r requirements.txt reports no known vulnerabilities.
- Recommendation:
  - Keep pip audit in CI and pin upgrades intentionally.

### Issue 4: Requirements are partially unpinned
- Status: Resolved
- Evidence:
  - All active backend dependencies in [requirements.txt](requirements.txt#L1) are pinned with exact versions.
- Recommendation:
  - Preserve strict pinning for reproducible environments.

### Issue 5: Heavy dependencies appear unused
- Status: Resolved
- Evidence:
  - Removed unused Jinja2 from [requirements.txt](requirements.txt#L1).
  - Remaining report dependency WeasyPrint is retained for PDF generation.
- Recommendation:
  - Periodically prune unused dependencies.

### Issue 6: No formal license compliance workflow
- Status: Resolved
- Evidence:
  - License/SBOM compliance checks are defined in [.github/workflows/license-compliance.yml](.github/workflows/license-compliance.yml#L1).
- Recommendation:
  - Keep policy checks enforced in CI.

## Post-Closure Follow-up Plan (Optional Top 4)

1. Add automated authz regression tests.
  - Why: ownership checks are high-risk and require explicit negative/positive test coverage before release.
  - Start with [tests/test_upload.py](tests/test_upload.py#L1) and add dedicated API authz tests.

2. Keep dependency hygiene in CI as a release gate.
  - Why: the current dependency baseline is clean and should stay that way.
  - Keep checks active in [.github/workflows/dependency-audit.yml](.github/workflows/dependency-audit.yml#L1) and [requirements.txt](requirements.txt#L1).

3. Move ownership model from property-scope to user-identity linkage.
  - Why: current controls are effective for scoped client accounts but not yet tied to per-user resource ownership tables.
  - Start with [models.py](models.py#L14) and auth payload claims in [frontend/app/api/auth/login/route.ts](frontend/app/api/auth/login/route.ts#L43).

4. Apply typed exception mapping in report/vector edge modules.
  - Why: core API paths now use typed mapping; extending this closes the remaining consistency gap.
  - Start with [routes/report_routes.py](routes/report_routes.py#L48) and [services/vector_service.py](services/vector_service.py#L102).
