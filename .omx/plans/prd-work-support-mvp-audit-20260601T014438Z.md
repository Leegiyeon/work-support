# PRD — work-support MVP 구현 상태 점검 및 개선 계획

## 1. 목표
현재 work-support의 실제 구현 상태를 기능별로 점검하고, MVP를 안정적으로 확장하기 위한 개선 계획을 정의한다. 이번 산출물은 실행 계획이며 코드 변경은 포함하지 않는다.

## 2. RALPLAN-DR Summary

### Principles
1. 개인 업무 관리와 경력 자산화를 우선한다.
2. 구현된 근거와 저장 데이터만 기반으로 판단한다.
3. 기능을 “입력 → 저장 → 보기 → 자동화”의 작은 vertical slice로 확장한다.
4. 로그인/멀티테넌트/SaaS 추상화보다 owner-scoped local MVP 경계를 유지한다.
5. DB schema source of truth와 API 일관성을 먼저 정리해 후속 기능 부채를 줄인다.

### Decision drivers
1. 현재 구현과 계획의 괴리: 여러 기능을 요청했지만 실제 repo는 scaffold + weekly report 위주다.
2. 데이터 흐름 부재: 프로젝트/문서/업무 로그 입력 API/UI가 없어서 주간 리포트 외 기능이 고립되어 있다.
3. 민감 데이터 안전성: 업무 문서/AI 요약/경력 기록은 owner scope와 로컬 guard가 필요하다.

### Viable options
#### Option A — Schema/API foundation first (recommended)
- 내용: migrations/source-of-truth, project CRUD, document metadata/upload, extracted_items/work log boundary를 먼저 정리한다.
- 장점: 이후 AI/RAG/리포트가 실제 저장 데이터 위에서 일관되게 작동한다.
- 단점: 사용자가 바로 보는 AI 기능은 늦어진다.

#### Option B — UI dashboard first
- 내용: 현재 weekly report UI 주변에 프로젝트/업무 로그 화면을 먼저 만든다.
- 장점: 사용 흐름이 빨리 보인다.
- 단점: API/DB 경계가 덜 정리된 상태에서 프론트 중복과 임시 데이터가 늘 수 있다.

#### Option C — AI/RAG first
- 내용: 업로드/텍스트 추출/embedding/RAG를 먼저 붙인다.
- 장점: 제품 차별 기능이 빨리 드러난다.
- 단점: project/document/work log 입력·상태·재시도·비용 경계가 없어서 실패 상태와 데이터 무결성 부채가 커진다.

### Chosen option
Option A. 이유: 현재 repo에는 주간 리포트가 있지만 리포트가 의존해야 할 프로젝트/문서/업무 로그 입력 계층이 없다. DB/API foundation을 먼저 정리해야 파일 업로드, AI 분석, RAG, 경력 자산화가 중복 없이 연결된다.

## 3. 기능별 현재 구현 상태

| 기능 | 상태 | 근거 | 판단 |
|---|---:|---|---|
| 프로젝트 관리 | 부분 DB만 있음 | `projects` table: `backend/app/db/schema.py:7-16`; CRUD API/UI 없음 | 미완성 |
| 업무 로그 | generic extracted_items만 있음 | `extracted_items.item_type`: `backend/app/db/schema.py:40-52`; 별도 업무 로그 API/UI 없음 | 미완성 |
| 파일 업로드 | boundary만 있음 | `ObjectStorage` Protocol only: `backend/app/services/storage.py`; upload route 없음 | 미구현 |
| AI 분석 | 컬럼만 있음 | `documents.summary/keywords/analysis_status`: `backend/app/db/schema.py:27-35`; OpenAI 호출 없음 | 미구현 |
| RAG | pgvector extension만 있음 | `CREATE EXTENSION vector`: `backend/app/db/schema.py:4`; chunks/embedding 없음 | 미구현 |
| 경력 자산화 | 리포트 파생 요약만 있음 | `career_candidate` item type, weekly summary: `backend/app/services/weekly_report.py:212-217` | 매우 초기 |
| 주간 리포트 | 수직 슬라이스 구현 | API/UI/tests 존재: `backend/app/api/reports.py`, `frontend/app/reports/page.tsx`, `backend/tests/test_weekly_report.py` | 구현됨, 단 foundation 의존 |

## 4. 주요 문제 진단

### 4.1 중복 코드
- DB DDL이 `backend/app/db/schema.py`와 `infrastructure/postgres/init/002_work_support_schema.sql`에 중복된다.
  - 위험: 컬럼/인덱스 drift, prod/local bootstrap 차이.
  - 개선: Alembic 등 migration source-of-truth 도입. 당장 과하면 SQL 파일을 canonical로 두고 Python init은 파일을 읽게 한다.
- 상태값/타입 정의가 DB CHECK, Python Literal, UI union에 분산되어 있다.
  - 예: project status는 DB, `backend/app/schemas/reports.py:6`, `frontend/app/reports/page.tsx:9`에 반복.
  - 개선: 백엔드 enum schema를 canonical로 두고 프론트 타입 생성 또는 API response 중심으로 정리.

### 4.2 책임 분리 문제
- `weekly_report.py`가 DB 조회, 도메인 DTO, group-by, Markdown 렌더링, 경력 요약 파생을 모두 담당한다.
  - 개선: repository/query, report assembler, markdown renderer로 3분리.
- `security.py`의 report-specific guard는 현재는 적절하지만 이후 API가 늘면 공통 owner context dependency로 확장해야 한다.
- `documents` table이 원본 파일 metadata, 추출 텍스트, AI 요약/상태를 한 테이블에 모두 담는다.
  - MVP 초기는 허용 가능하지만 텍스트/분석 이력이 커지면 `document_texts`, `document_analyses` 분리가 필요하다.

### 4.3 DB 구조 문제
- schema migration 체계가 없다. `CREATE TABLE IF NOT EXISTS` + `ALTER TABLE IF NOT EXISTS`는 초기 MVP에만 적합하다.
- `owner_id TEXT DEFAULT 'local-owner'`는 local MVP guard로는 충분하지만 future auth 연동 시 users/owners table 또는 config-owned local profile로 전환해야 한다.
- `extracted_items` generic table은 MVP에는 간단하지만 task/decision/risk/career_candidate의 상태/필드가 달라질 때 validation이 약하다.
- `document_chunks`/embedding/vector dimension 컬럼이 없어 RAG 구현 기반이 없다.
- 업무 로그용 `work_logs` 또는 `project_updates`가 없어 사람이 직접 남기는 진행 기록과 AI 추출 항목이 구분되지 않는다.

### 4.4 API 일관성 문제
- 현재 business API는 `/reports/weekly`뿐이다. projects/documents/items CRUD가 없어 REST shape가 정해지지 않았다.
- error response는 FastAPI 기본 형태와 custom detail 문자열이 혼재될 가능성이 있다.
- report access header가 프론트 `NEXT_PUBLIC_*`로 노출된다. local guard로는 acceptable하지만 API 확장 전에는 owner context, token rotation, local-only warning이 필요하다.
- 모든 API가 sync psycopg 직접 호출 구조라, 이후 파일/AI 작업이 들어오면 background job boundary를 별도로 마련해야 한다.

### 4.5 프론트 UX 문제
- 홈과 리포트 화면만 있고 프로젝트 목록/상세/문서/업무 로그 입력 화면이 없다.
- `/reports`는 Markdown만 보여주며 프로젝트별 항목을 구조적으로 탐색하거나 빈 DB에서 샘플/온보딩을 제공하지 않는다.
- report token/owner 설정 실패 시 사용자가 무엇을 수정해야 하는지 안내가 부족하다.
- CSS가 전역 단일 파일에 누적되고 있어 화면이 늘면 유지보수성이 떨어진다.

### 4.6 테스트 부족 영역
- 백엔드: 주간 리포트 unit/API 중심. 실제 Postgres integration, schema migration, date boundary, owner isolation, DB unavailable case가 제한적이다.
- 프론트: 테스트 없음. form validation, fetch error, copy fallback, empty report rendering이 미검증.
- E2E: Docker Compose 부팅 후 `/reports` → API → DB flow 검증 없음.
- 보안/민감정보: secret scan은 수동 수준. local guard가 public exposure에서 차단되는지 config test가 일부만 있다.

## 5. 개선 우선순위

### P0 — 기반 안정화 (다음 실행 1순위)
1. DB schema source-of-truth 정리 — **canonical SQL 우선**
   - 새 dependency를 추가하지 않는 MVP 원칙에 따라 첫 실행은 Alembic이 아니라 `infrastructure/postgres/init/002_work_support_schema.sql`을 canonical로 둔다.
   - `backend/app/db/schema.py`는 같은 SQL 파일을 읽어 실행하도록 바꾸어 Python 문자열 DDL 중복을 제거한다.
   - 이후 schema 변경이 잦아지는 시점에만 Alembic 도입을 별도 의사결정으로 검토한다.
   - status/item_type enum 정의 위치를 backend schema/response contract 중심으로 정리한다.
2. 공통 DB access layer 도입
   - `db/session.py` 또는 `db/connection.py`에서 psycopg 연결/row factory/error mapping 통일.
3. 공통 owner context dependency 정리
   - report guard를 `get_owner_context`로 일반화하되 full login은 아직 만들지 않음.
4. 백그라운드 작업 경계 초안 고정
   - 파일 업로드 요청은 원본 저장 + metadata 저장 + `ingest_jobs` 생성까지만 담당한다.
   - worker는 extraction → AI analysis → chunk/embedding 생성 단계를 처리한다.
   - 모든 job은 `pending/processing/completed/failed`, `attempt_count`, `last_error`, `idempotency_key`, `started_at`, `finished_at`를 가진다.
   - 동기 API는 장시간 파일/AI 처리를 직접 수행하지 않는다.

### P1 — 실제 데이터 입력 vertical slice
4. Projects CRUD API/UI
   - `/projects` list/create/detail/update/delete.
   - 상태값: idea/review/in_progress/on_hold/done.
5. Work logs / extracted items 입력 API/UI
   - 사람이 직접 남기는 진행 로그는 `work_logs` 또는 `project_updates`로 분리.
   - AI 추출 항목은 `extracted_items`로 유지.
6. Documents metadata + upload slice
   - local storage implementation, file validation, metadata 저장.

### P2 — 자동화 파이프라인
7. Text extraction pipeline
   - document extraction status, error, retry boundary.
8. AI analysis pipeline
   - prompts 분리, JSON schema validation, item extraction 저장.
   - 모든 AI 산출물은 `model`, `prompt_version`, `schema_version`, `input_content_hash`, `rerun_of`, evidence chunk/page/span references를 함께 저장한다.
   - 근거가 없는 수치 성과/요약은 생성하지 않는다.
9. RAG foundation
   - `document_chunks`, embedding model/dimension, chunk source refs, project-scoped search.
   - chunk에는 source document, page/slide/sheet 또는 character span, text hash, embedding model/version을 남긴다.

### P3 — 자산화/리포트 고도화
10. Career assetization
    - project role, evidence-backed resume/portfolio/STAR drafts, user edit/save.
11. Weekly report UX enhancement
    - generated report history, project drill-down, empty-state onboarding.


## 5.5 보존/삭제 정책 초안

파일 업로드, 텍스트 추출, AI 분석, RAG 실행 전 다음 정책을 먼저 고정한다.

### 대상 데이터
- 원본 파일: local storage path, original filename, content type, size.
- 문서 metadata: `documents` row.
- 추출 텍스트: 현재는 `documents.extracted_text`, 추후 `document_texts` 분리 가능.
- AI 분석 결과: summary, keywords, extracted_items, career candidates.
- RAG 데이터: document_chunks, embeddings, source offsets/page/slide/sheet references.
- 리포트/경력 결과: 저장형 리포트를 만들 경우 source snapshot/reference를 별도 보존.

### 기본 방침
- MVP 기본은 **hard delete with best-effort cleanup**: 프로젝트 삭제 시 DB cascade 후 owner-scoped 원본 파일과 파생 산출물을 삭제한다.
- 실패한 파일 삭제는 조용히 무시하지 않고 cleanup job/error log로 남긴다.
- AI/RAG 산출물은 원본 문서 삭제 시 함께 삭제한다. 출처가 사라진 경력/리포트 문장은 “orphaned evidence” 상태를 갖거나 재생성 대상이 된다.
- public URL은 만들지 않는다. 파일 접근은 owner context를 통과한 backend API를 통해서만 허용한다.

### 실행 전 결정해야 할 점
- project delete가 즉시 hard delete인지, 확인 prompt 후 hard delete인지.
- 사용자가 수동으로 정리한 경력 문장을 원본 삭제 후에도 보존할지 여부.
- local storage cleanup 실패 재시도 횟수와 표시 위치.

## 5.6 백그라운드 작업/파이프라인 경계

파일/AI/RAG는 다음 경계를 따른다.

1. Upload API
   - validate file → owner-scoped local storage 저장 → documents row 생성 → ingest_jobs row 생성.
   - response는 document id/job id/status를 반환하고 AI 분석을 동기 수행하지 않는다.
2. Worker/service
   - job lease 획득 → 텍스트 추출 → AI 분석 → extracted_items 저장 → chunk/embedding 생성.
   - 각 단계는 idempotency_key와 status transition으로 재실행 가능해야 한다.
3. Failure handling
   - 실패 단계, error message, attempt_count를 저장한다.
   - 사용자는 document/job 단위로 재시도할 수 있다.
4. Report/RAG/Career consumers
   - 완료된 분석 산출물만 기본 사용한다.
   - 미완료/실패 문서는 UI와 리포트에 status로 드러내되 근거 없는 요약을 생성하지 않는다.

## 5.7 AI provenance/versioning 정책

AI 분석, RAG 답변, 경력 문장 생성 전에 다음 provenance 필드를 저장 대상으로 고정한다.

- `model`: 사용한 AI/embedding model 이름.
- `prompt_version`: prompt 파일 또는 template version.
- `schema_version`: JSON schema/parser version.
- `input_content_hash`: 원문/청크 입력의 hash.
- `rerun_of`: 재분석/재생성인 경우 이전 분석 id.
- `evidence_refs`: document id, chunk id, page/slide/sheet/row 또는 character span.
- `generated_at`, `analysis_status`, `analysis_error`: 생성 시각과 실패 근거.

이 필드가 없는 AI 산출물은 경력 자산화나 RAG 답변의 authoritative source로 쓰지 않는다.

## 5.8 Local token boundary and removal path

현재 `NEXT_PUBLIC_WORK_SUPPORT_REPORT_TOKEN`은 로컬 개인 MVP guard이며 보안 인증 수단이 아니다.

- 허용 범위: `APP_ENV=local`, loopback-bound Docker/local dev, 단일 owner.
- 금지 범위: LAN/public 배포, 다중 사용자, 민감 문서 공유 환경.
- 제거 경로: Projects/Documents/Reports 공통 owner context가 정착된 뒤, 실제 로그인 또는 backend-only session token으로 교체한다.
- 실행 전 gate: `APP_ENV != local`에서는 기본 dev token이 거부되어야 하며, README/runbook에 non-production boundary를 명시한다.

## 5.9 MVP file type scope

1차 파일 처리 MVP는 TXT, MD, digital PDF, DOCX로 제한한다. XLSX/PPTX는 사용자 요청이 다시 들어오거나 1차 업로드/추출 안정화 후 backlog에서 별도 계획한다.

## 6. Acceptance criteria for future improvement execution
- 모든 새 business API는 owner-scoped query/filter를 포함한다.
- `NEXT_PUBLIC_WORK_SUPPORT_REPORT_TOKEN`은 local-only로 명시되고, non-local 기본 토큰 거부 및 제거 경로가 문서화된다.
- DB schema는 `infrastructure/postgres/init/002_work_support_schema.sql` canonical source에서 재현 가능하며 Python init과 drift가 없다.
- 파일 업로드/AI/RAG는 `ingest_jobs`류의 작업 경계, 상태값, 재시도/실패 이유, idempotency key가 저장된다.
- 프로젝트/문서 삭제는 원본 파일, 추출 텍스트, chunks, embeddings, AI 산출물의 cleanup 정책을 따른다.
- 리포트/경력 문장은 저장된 근거 없이 성과 수치를 만들지 않는다.
- AI 산출물은 model/prompt/schema/input hash/rerun/evidence refs가 없으면 downstream authoritative source로 쓰지 않는다.
- MVP 파일 처리 범위는 TXT/MD/digital PDF/DOCX로 제한하고 XLSX/PPTX는 backlog로 둔다.
- 최소 테스트: backend unit + API + DB integration, frontend form/error/render tests, docker compose smoke.

## 7. ADR

### Decision
MVP 개선은 “DB/API foundation → 프로젝트/업무 로그 입력 → 파일 업로드 → 텍스트/AI/RAG → 경력/리포트 고도화” 순서로 진행한다.

### Drivers
- 현재 구현된 주간 리포트가 의존하는 입력 데이터 계층이 없다.
- schema/API shape가 정리되지 않은 상태에서 AI/RAG를 붙이면 중복과 재작업이 커진다.
- 개인 업무 기록은 민감 데이터이므로 owner-scoped boundary를 모든 기능에 일관 적용해야 한다.

### Alternatives considered
- UI부터 확장: 빠르지만 임시 데이터와 중복 client logic 위험이 큼.
- AI/RAG부터 구현: 제품가치가 빨리 보이나, 파일/문서/상태/비용/재시도 기반이 없어 부채가 큼.

### Consequences
- 초기에는 눈에 보이는 AI 기능보다 기반 정리에 시간이 쓰인다.
- 이후 기능은 더 작은 vertical slice로 안정적으로 붙일 수 있다.
- 첫 migration 실행은 새 dependency 없이 canonical SQL 방식으로 제한되어 migration history 기능은 후속 의사결정으로 남는다.
- AI provenance 필드와 local-token 제거 경로를 먼저 고정하므로 후속 AI/RAG/경력 기능이 감사 불가능한 임시 산출물에 의존하지 않는다.

### Follow-ups
- `$ultragoal`: P0 기반 안정화부터 순차 실행하는 기본 후속 경로. 첫 story는 canonical SQL source-of-truth + 공통 DB/owner context + pipeline/delete policy 문서화로 제한한다.
- `$team`: P0/P1을 병렬로 나눌 때 사용. 예: DB/migration lane, backend API lane, frontend UI lane, test lane.
- `$ralph`: 긴 단일 소유 검증 루프가 필요할 때만 explicit fallback.

## 8. Stabilization-only execution scope for immediate `$ultragoal`

이번 실행은 기능 추가가 아니라 안정화 전용이다.

### Explicitly out of scope
- Projects CRUD/API/UI 구현 금지.
- 업무 로그 입력 화면/API 구현 금지.
- 파일 업로드 구현 금지.
- 텍스트 추출/AI 분석/RAG/embedding 구현 금지.
- 경력 자산화 UI/history/persistence 구현 금지.
- 주간 리포트 history 저장 또는 새 AI 기능 추가 금지.

### Allowed changes only
- 중복 DDL 정리: canonical SQL을 단일 source로 두고 backend init이 이를 읽도록 정리.
- DB/access helper 정리: psycopg 연결/row factory/error translation의 최소 공통 helper 추가.
- owner context 정리: report-specific guard를 향후 API가 재사용 가능한 local owner context dependency로 정리하되 full login은 만들지 않음.
- API/error response consistency: FastAPI validation error는 기본 형태 유지, app/database/local guard error는 stable `{detail, code}` shape로 매핑.
- 타입 정리: backend Pydantic/Literal을 현재 canonical로 두고, frontend는 현재 쓰는 status union만 별도 local type으로 모으거나 response type과 중복을 줄인다. codegen/new dependency는 금지.
- README/runbook 업데이트: canonical SQL, local token boundary, 안정화 범위, test commands 반영.
- 기본 테스트 보강: response shape, DB init canonical source, owner context, README/env consistency.

### API/error response convention for stabilization
- Success response는 현재 `WeeklyReportResponse` payload를 유지한다. 별도 envelope는 도입하지 않는다.
- Request validation은 FastAPI/Pydantic 기본 422 응답을 유지한다.
- Application/auth/config/database errors는 `HTTPException(detail={"code": "...", "message": "..."})` 형식으로 통일한다.
- Error code 예시: `REPORT_ACCESS_HEADERS_REQUIRED`, `REPORT_OWNER_FORBIDDEN`, `REPORT_TOKEN_INVALID`, `REPORT_TOKEN_NOT_CONFIGURED`, `REPORT_DEFAULT_TOKEN_NOT_ALLOWED`, `DATABASE_UNAVAILABLE`.

### Type cleanup convention for stabilization
- Backend: `ProjectStatus`, `ItemType` Literal은 `backend/app/schemas/reports.py` 또는 가까운 schema module에 유지한다.
- Frontend: 현재 `/reports`에서 필요한 타입만 `frontend/app/reports/page.tsx` 내부 또는 인접 `types` 파일로 정리한다. 기능이 늘기 전까지 codegen/OpenAPI client는 도입하지 않는다.
- DB enum/check constraint와 앱 Literal의 drift는 이번 실행에서 문서/test로 감시하고, 대규모 enum abstraction은 만들지 않는다.

### Stabilization verification commands
- `pytest -q backend/tests`
- `python -m compileall -q backend/app backend/tests`
- `npm --prefix frontend run lint`
- `npm --prefix frontend run typecheck`
- `npm --prefix frontend run build`
- `docker compose config`
- README/env consistency check
- secret pattern scan excluding dependency/build/cache directories

### 8.1 Execution clarifications required by final Critic review

- Canonical SQL path strategy:
  - `infrastructure/postgres/init/002_work_support_schema.sql` remains the single canonical table/index DDL source.
  - Backend schema initialization reads SQL through a small path resolver:
    1. optional `WORK_SUPPORT_SCHEMA_SQL_PATH` env override,
    2. Docker path `/app/infrastructure/postgres/init/002_work_support_schema.sql`,
    3. repo-root relative path from `backend/app/db/schema.py` to `../../.. / infrastructure/postgres/init/002_work_support_schema.sql` without the spaces,
    4. current-working-directory relative `infrastructure/postgres/init/002_work_support_schema.sql`.
  - Docker Compose must mount `./infrastructure/postgres/init:/app/infrastructure/postgres/init:ro` into the backend service so `python backend/scripts/init_db.py` also uses the canonical SQL inside the backend container.
  - Do not copy the SQL into `backend/`; that would recreate duplicate DDL ownership.
- Frontend error detail handling:
  - The `/reports` page must parse both legacy string `detail` and stabilized object `detail: { code, message }`.
  - User-facing text should display `message`; the `code` may remain developer/debug context and does not require a new UI feature.
- Verification commands for this stabilization slice:
  - Backend tests: `cd backend && source .venv/bin/activate && pytest -q`
  - Backend syntax: `cd backend && source .venv/bin/activate && python -m compileall -q app tests`
  - Frontend lint: `npm --prefix frontend run lint`
  - Frontend typecheck: `npm --prefix frontend run typecheck`
  - Frontend build: `npm --prefix frontend run build`
  - Frontend dependency audit: `npm --prefix frontend audit --audit-level=moderate`
  - Compose validation: `docker compose config`
  - Markdown smoke lint: `python - <<'PY'` script that checks README/tracked markdown for trailing whitespace and hard tabs; do not introduce a markdownlint dependency.
  - Secret smoke scan: `grep -RInE '(sk-[A-Za-z0-9_-]{20,}|OPENAI_API_KEY=.+[^[:space:]]|postgresql://[^[:space:]]+:[^[:space:]]+@)' --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=.venv .` with documented false positives for local sample credentials.
