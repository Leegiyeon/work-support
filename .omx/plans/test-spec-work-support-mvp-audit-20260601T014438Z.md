# Test Spec — work-support MVP improvement plan

## Purpose
현재 MVP 점검 결과를 기반으로 후속 구현 시 필요한 검증 범위를 정의한다. 이번 ralplan에서는 코드를 수정하지 않고, 향후 실행 lane의 성공 기준을 고정한다.

## Current verification baseline
- Existing backend tests: `backend/tests/test_health.py`, `backend/tests/test_weekly_report.py`.
- Existing frontend checks: lint/typecheck/build scripts exist, but no component tests.
- No DB integration test or E2E test currently exists.

## Test gaps by area

### Projects
- API: create/list/get/update/delete, invalid status, owner isolation, updated_at sorting.
- UI: list loading/error/empty, create form validation, status badge labels.
- DB: owner_id index usage, cascade behavior with documents/items.

### Work logs / extracted items
- API: direct work log creation vs AI extracted item creation separation.
- Validation: item_type-specific required fields and status transitions.
- Report integration: logs/items appear in weekly report only for selected period and owner.

### File upload
- API: allowed extensions, max file size, empty file, duplicate filename handling, owner-scoped storage path.
- Storage: local path traversal prevention, no public URL exposure, deletion cleanup.
- Deletion/retention: project/document delete removes or marks original file, extracted text, chunks, embeddings, and AI outputs according to the retained policy; cleanup failure is observable and retryable.
- UI: upload progress, error messages, document list refresh.

### Text extraction / AI analysis
- Unit: MVP parser adapters are limited to TXT, MD, digital PDF, and DOCX fixture files.
- Backlog: XLSX/PPTX parser fixtures are explicitly out of the 1차 MVP test gate unless a later plan approves them.
- API/job: upload request only creates document/job; worker handles extraction/analysis; status transitions pending→processing→completed/failed are persisted.
- Retry/idempotency: repeated job execution with the same idempotency key does not duplicate extracted_items/chunks; attempt_count and last_error are updated.
- AI: JSON schema validation, malformed response handling, no fabricated metrics.
- Provenance: persisted AI outputs include model, prompt_version, schema_version, input_content_hash, rerun_of, and evidence chunk/page/span refs.

### RAG
- DB: `document_chunks` vector dimension, project/owner filters, source references.
- Search: similarity threshold, no cross-project leakage, empty result behavior.
- Deletion: document/project deletion removes chunks/embeddings or marks them unavailable before search.
- Answer: cited sources required, “근거 없음” response when insufficient context.

### Career assetization
- Generation: uses role + stored evidence only, no unsupported numeric outcomes.
- Provenance: generated career records keep source evidence refs and AI provenance fields before becoming reusable assets.
- Persistence: user can edit/save, source evidence remains traceable.
- UI: resume/portfolio/STAR sections distinguish generated draft vs user-edited content.

### Weekly report
- Already covered: stored-data-only output, access headers, owner filtering, invalid period.
- Add later: real Postgres integration, timezone boundary around midnight, frontend error/copy tests, report history if persisted.

## Suggested command matrix for future execution
- Backend unit/API: `pytest -q backend/tests`
- Backend compile: `python -m compileall -q backend/app backend/tests`
- Frontend lint/typecheck/build: `npm --prefix frontend run lint && npm --prefix frontend run typecheck && npm --prefix frontend run build`
- Compose config: `docker compose config`
- DB smoke: start Postgres, run canonical SQL init, seed owner/project/document/item, call API.
- Migration drift check: verify backend init reads the same canonical SQL as Docker bootstrap or compare checksums.
- E2E smoke: frontend `/reports` creates report from seeded DB.
- Security scan: secret pattern scan excluding generated dependency/build dirs.
- Local-token boundary: verify default report token is rejected outside `APP_ENV=local`; document replacement/removal path before non-local exposure.

## Acceptance gates
1. No business endpoint returns another owner’s data.
2. DB schema has one canonical source; Python init and Docker bootstrap cannot drift.
3. Project/document deletion has tests for original file cleanup, derived text cleanup, chunks/embeddings cleanup, and observable cleanup failure.
4. Upload/extract/analyze/embed jobs are idempotent and retryable; duplicate worker execution does not duplicate derived rows.
5. MVP parser tests cover TXT/MD/digital PDF/DOCX only; XLSX/PPTX are marked backlog unless explicitly approved later.
6. All persisted AI-derived outputs have status, source, failure evidence, model, prompt_version, schema_version, input_content_hash, rerun_of, and evidence refs.
7. RAG responses include source document/chunk references or explicitly state insufficient evidence.
8. Browser-visible report token is documented as local-only and has a replacement/removal path before real auth or non-local deployment.
9. Frontend empty/loading/error states exist for each MVP screen.
10. README/runbook matches actual commands and env variables.


## Stabilization-only verification

Immediate `$ultragoal` stabilization must pass:

- `pytest -q backend/tests`
- `python -m compileall -q backend/app backend/tests`
- `npm --prefix frontend run lint`
- `npm --prefix frontend run typecheck`
- `npm --prefix frontend run build`
- `docker compose config`
- README/env consistency check: documented env vars match `.env.example`, `backend/.env.example`, `frontend/.env.example`, and Docker Compose usage.
- API error shape tests for local guard/database errors use `{detail: {code, message}}` while FastAPI validation remains default 422.
- DB init test proves backend init reads the canonical SQL file instead of maintaining a duplicate DDL string.

Out-of-scope assertions for this stabilization run:

- No new Projects CRUD endpoint/screen.
- No file upload endpoint/screen.
- No OpenAI, text extraction, RAG, embedding, or career-generation execution path.
- No new dependency for migrations or frontend type generation.

### Stabilization clarification tests

- Canonical SQL resolver test:
  - Assert `app.db.schema.load_schema_sql()` returns byte-for-byte contents of `infrastructure/postgres/init/002_work_support_schema.sql` in the local repo.
  - Assert `backend/app/db/schema.py` no longer embeds `CREATE TABLE IF NOT EXISTS projects` as a multiline duplicate.
  - Assert `docker-compose.yml` mounts `./infrastructure/postgres/init:/app/infrastructure/postgres/init:ro` for backend.
- Frontend error parsing:
  - The reports page helper must convert `{ detail: { code, message } }` to `message`, string `detail` to that string, and malformed responses to the default Korean failure message.
  - This can be covered by a small exported pure helper and TypeScript typecheck; no new frontend test framework dependency is required in this stabilization slice.
- Verification commands are exactly the ones listed in PRD section 8.1. If a tool is not installed, record the exact blocker and use the next-best smoke check rather than adding a new dependency.
