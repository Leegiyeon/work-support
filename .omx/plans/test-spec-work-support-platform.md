# Test Spec: work-support MVP

## Scope
Planning-only test specification for the future MVP. No implementation is performed in ralplan.

## First Vertical Slice Acceptance Tests
1. Upload TXT/MD file creates a private storage object and `documents` row.
2. Upload creates an `ingest_jobs` row with deterministic `dedupe_key`.
3. Text extraction writes `document_texts.full_text` and marks extraction success.
4. AI summary writes `document_ai_runs` with `model`, `prompt_version`, `schema_version`, `input_content_hash`, and JSON output.
5. Document detail displays original metadata, status, extracted text, and summary.
6. Re-upload with the same `owner_id + content_hash` reuses the existing `documents` row and does not create a new ingest chain.
7. Failed extraction/summary stores failure reason and exposes retry.
8. Scanned/OCR-needed documents are represented as `processing_status='failed'` plus `unsupported_reason='unsupported_needs_ocr'`, and are not auto-retried.
9. Unauthenticated requests cannot read uploaded objects or document detail.
10. Storage bucket is non-public.
11. Owner-scoped query and storage path policy exists even for single-user MVP.
12. AI summary tests use mock/test double in CI; live OpenAI calls are not required for deterministic CI.

## Later MVP Acceptance Tests
1. PDF/DOCX digital documents are extracted or explicitly marked unsupported with a clear reason.
2. Structured extraction produces decisions, todos, risks, and career highlights with evidence chunk links.
3. AI project/business-unit suggestions can be confirmed or manually changed.
4. FTS search returns keyword matches with document/chunk references.
5. Vector search returns semantic matches with citations.
6. Q&A stores retrieved chunks and answer citations.
7. Career Center generates period summaries and Markdown export from confirmed highlights.

## Verification Layers
- Unit: validators, hash, parsers, chunker, schema validation, job state transitions.
- Integration: upload/storage/DB/job, extraction, AI summary with mock, indexing.
- E2E: upload-to-document-detail, project linking, search/Q&A, career summary.
- Observability: failed job count, processing duration, token/cost metadata, retry success rate.
