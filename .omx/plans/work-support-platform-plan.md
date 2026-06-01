# work-support 초기 합의형 계획

## 0) 계획 경계
- 이 문서는 **구현 전 설계 문서**다. 현재 단계에서는 애플리케이션 코드를 작성하지 않는다.
- 목표는 처음부터 SaaS 플랫폼을 만드는 것이 아니라, **개인 업무 관리와 경력 자산화**에 필요한 최소 제품을 명확히 정의하는 것이다.
- 기본 가정은 **단일 사용자/private cloud 또는 로컬에 가까운 개인용 웹앱**이다. 다중 사용자 SaaS는 후순위다.

## 1) 서비스 핵심 목적
`work-support`는 사용자가 업로드한 문서와 업무 기록을 AI로 분석하여, 단순 파일 저장소가 아니라 **프로젝트/사업 단위의 업무 기억 시스템**으로 전환하는 서비스다.

핵심 목적은 세 가지다.

1. **업무 맥락 회수**
   - 산재한 문서, 회의록, 보고서, 메모, 산출물을 다시 찾고 이해하는 시간을 줄인다.
   - “이 프로젝트에서 어떤 결정이 있었나?”, “남은 할 일은 무엇인가?”, “리스크는 무엇인가?”를 바로 확인할 수 있게 한다.

2. **프로젝트 운영 지원**
   - 문서에서 추출된 요약, 결정사항, 할 일, 리스크, 관련 조직/사업부를 프로젝트에 연결한다.
   - 진행 현황을 사용자가 수동으로만 관리하는 것이 아니라, 업로드된 자료에서 지속적으로 보강한다.

3. **경력 자산화**
   - 프로젝트별 기여, 성과, 사용 기술, 문제 해결 사례를 축적한다.
   - 월간/분기/프로젝트 단위로 이력서·포트폴리오·면접 답변에 활용 가능한 경력 요약을 만든다.

## 2) RALPLAN-DR 요약

### 원칙
1. **개인 MVP 우선**: 다중 사용자 SaaS, 결재, 과금, 조직 관리자 기능은 배제한다.
2. **원본 보존 + 파생물 분리**: 원본 파일, 추출 텍스트, 청크, 요약, 구조화 결과, 임베딩, 검색 색인을 분리 관리한다.
3. **관계형 업무 맥락 우선**: 문서보다 프로젝트, 사업부, 결정, 할 일, 리스크, 경력 포인트의 연결을 1급 객체로 둔다.
4. **검색 가능성과 근거 추적성**: Q&A와 요약은 문서/청크/페이지 또는 span 수준 근거를 함께 제공한다.
5. **AI 결과는 재생성 가능해야 함**: AI 산출물은 모델, 프롬프트 버전, 스키마 버전, 원본 해시를 기록해 재처리할 수 있게 한다.

### 주요 의사결정 동인 Top 3
1. **개인 생산성**: 업로드된 자료를 빠르게 이해하고 다시 찾을 수 있어야 한다.
2. **장기 데이터 소유권**: 경력 자산과 업무 기록은 서비스 내부 DB에서 직접 통제해야 한다.
3. **신뢰 가능한 AI**: 요약/추출/Q&A는 출처와 버전이 남아야 나중에 검증할 수 있다.

### 실행 옵션
| 옵션 | 설명 | 장점 | 단점 |
|---|---|---|---|
| A. **권장: 자체 업무 그래프 + 자체 검색/RAG** | Supabase Storage에 원본 저장, Postgres에 메타/파생물/관계 저장, FTS+pgvector로 검색, OpenAI로 요약/구조화/임베딩 수행 | 프로젝트/사업부/경력 연결이 자연스럽고, 데이터 소유권·근거·재처리가 명확함 | 청킹, 색인, 재처리, 검색 품질 관리가 필요 |
| B. OpenAI File Search 중심 | OpenAI File Search/vector store를 Q&A 중심으로 사용하고, 앱 DB에는 최소 메타데이터만 저장 | Q&A MVP가 빠름 | 업무 맥락·경력 자산화·근거/버전 관리가 약해질 수 있음 |
| C. LangChain/LangGraph 중심 agent stack | 문서 처리와 추론 흐름을 프레임워크 중심으로 구성 | 복잡한 agent workflow 확장에 유리 | 개인 MVP에는 추상화가 과하고 디버깅/운영 부담이 큼 |

### 결정
**옵션 A를 채택**한다. 이 서비스의 핵심은 “파일에게 질문하기”가 아니라 “업무 맥락을 구조화하고 장기적으로 재사용하기”이기 때문이다. 단, 첫 구현은 얇은 vertical slice로 제한하고, OpenAI File Search는 나중에 검색 품질 보강용 옵션으로만 남긴다.

## 3) MVP 범위

### 포함 범위
1. **파일 업로드 및 원본 저장**
   - PDF, DOCX, TXT, MD 우선.
   - 원본 파일은 private storage에 보관.
   - 파일 해시와 저장 경로를 DB에 기록.

2. **텍스트 추출**
   - 디지털 PDF/DOCX/TXT/MD에서 텍스트 추출.
   - 페이지/섹션 단위 메타데이터를 가능한 범위에서 보존.
   - 스캔 PDF/OCR은 MVP 제외 또는 “처리 불가/후순위”로 명확히 표시.

3. **AI 요약 및 구조화 추출**
   - 문서 요약.
   - 프로젝트 후보, 사업부 후보, 결정사항, 할 일, 리스크, 경력 포인트 추출.
   - JSON Schema 기반 구조화 결과 저장.

4. **프로젝트/사업부 연결**
   - AI가 연결 후보와 confidence를 제안.
   - 사용자가 수동으로 확정/수정.
   - 자동 추정과 사용자 확정을 구분해 기록.

5. **검색 및 Q&A**
   - 키워드 검색: Postgres full-text search.
   - 의미 검색: pgvector embedding.
   - Q&A는 근거 문서, 청크, page/span 정보를 함께 표시.

6. **프로젝트 관리 화면**
   - 프로젝트별 개요, 진행상태, 관련 문서, 결정사항, 할 일, 리스크, 경력 포인트 표시.

7. **경력 관리 화면**
   - 프로젝트/기간별 성과 요약.
   - 역량 키워드, 기여 내용, 수치 성과, 사례집 초안 생성.

### 제외 범위
- 다중 사용자 협업, 조직 초대, RBAC, 관리자 콘솔.
- 과금/구독/공개 SaaS 운영.
- 결재/승인 workflow.
- 외부 공유 포털.
- 고급 OCR/이미지 문서 처리.
- LangChain/LangGraph 기반 복잡한 agent 자동화.
- 별도 vector DB, data warehouse, BI 대시보드.
- 모바일 앱.

## 4) 추천 기술 스택

### App
- **Next.js App Router**
  - 화면, 서버 액션, Route Handler를 한 프로젝트에서 관리하기 쉽다.
  - 개인 MVP에서 별도 백엔드 서버를 초기에 분리하지 않아도 된다.

### Database / Storage / Auth
- **Supabase Postgres**
  - 업무 객체 간 관계가 많으므로 relational DB가 적합하다.
  - full-text search와 pgvector를 함께 사용할 수 있다.
- **Supabase Storage**
  - 원본 파일 private bucket 저장.
- **Supabase Auth**
  - 로컬/개인 배포라면 초기에는 단순 보호 장치로만 사용한다.
  - “제품 기능”이 아니라 “접근 경계”로 취급한다.

### Schema / Migration
- **Drizzle ORM + drizzle-kit**
  - TypeScript-first schema와 migration 관리.
  - DB 구조가 제품의 핵심이므로 migration을 처음부터 둔다.

### AI
- **OpenAI Responses API**
  - 새 구현 기준 API로 사용.
- **Structured Outputs / JSON Schema**
  - 요약과 추출 결과를 DB에 넣기 위해 schema-constrained output 사용.
- **Embeddings**
  - document chunk 의미 검색용.

### Search
- **Postgres FTS + pgvector**
  - FTS는 키워드·정확도 검색.
  - pgvector는 의미 검색.
  - 두 결과를 병합하고 프로젝트/사업부/기간 필터를 결합한다.

### Job 처리
- MVP: **`ingest_jobs` 테이블 + server-side worker/cron**.
- 업로드 요청 경로에서는 파일 저장과 job 등록까지만 수행하고, 추출/AI/임베딩은 비동기로 처리한다.
- BullMQ, Temporal, dedicated queue는 후순위.

## 5) 추천 디렉터리 구조

```text
work-support/
├─ app/
│  ├─ (workspace)/
│  │  ├─ dashboard/
│  │  ├─ inbox/                  # 업로드/처리 상태
│  │  ├─ documents/
│  │  │  └─ [id]/
│  │  ├─ projects/
│  │  │  └─ [id]/
│  │  ├─ business-units/
│  │  ├─ search/
│  │  ├─ career/
│  │  └─ settings/
│  ├─ api/
│  │  ├─ uploads/
│  │  ├─ ingest/
│  │  └─ qna/
│  ├─ layout.tsx
│  └─ page.tsx
├─ components/
│  ├─ documents/
│  ├─ projects/
│  ├─ career/
│  └─ ui/
├─ lib/
│  ├─ ai/                        # prompts, schemas, OpenAI client wrappers
│  ├─ db/                        # drizzle client/schema exports
│  ├─ storage/                   # Supabase storage helpers
│  ├─ parse/                     # PDF/DOCX/TXT/MD text extraction
│  ├─ search/                    # FTS/vector retrieval
│  ├─ ingest/                    # pipeline step functions
│  └─ domain/                    # project/career mapping logic
├─ server/
│  ├─ actions/
│  └─ jobs/
├─ drizzle/
│  └─ migrations/
├─ tests/
│  ├─ unit/
│  ├─ integration/
│  └─ e2e/
├─ docs/
│  ├─ product/
│  └─ architecture/
└─ scripts/
```

## 6) 데이터베이스 테이블 설계

### 사용자/설정
#### `profiles`
- `id`
- `email`
- `display_name`
- `default_language`
- `timezone`
- `created_at`, `updated_at`

초기 단일 사용자라도 사용자 소유권 컬럼을 두면 나중에 확장과 private access 제어가 쉽다.

### 업무 구조
#### `business_units`
- `id`
- `owner_id`
- `parent_id`
- `name`
- `description`
- `created_at`, `updated_at`

#### `projects`
- `id`
- `owner_id`
- `business_unit_id`
- `name`
- `description`
- `status` (`planned`, `active`, `paused`, `done`, `archived`)
- `priority`
- `start_date`, `end_date`
- `summary`
- `created_at`, `updated_at`

### 문서 원본/추출/색인
#### `documents`
- `id`
- `owner_id`
- `title`
- `original_filename`
- `mime_type`
- `file_size`
- `storage_bucket`
- `storage_path`
- `content_hash`
- `processing_status` (`uploaded`, `extracting`, `analyzing`, `indexed`, `failed`)
- `unsupported_reason` (예: `unsupported_needs_ocr`, `unsupported_file_type`) — 별도 status가 아니라 실패/미지원 사유로 기록
- `failure_reason`
- `created_at`, `updated_at`

#### `document_texts`
- `id`
- `document_id`
- `source_blob_checksum`
- `extraction_method`
- `extraction_version`
- `language`
- `full_text`
- `page_count`
- `created_at`

#### `document_chunks`
- `id`
- `document_id`
- `document_text_id`
- `chunk_index`
- `content`
- `page_start`
- `page_end`
- `source_span_start`
- `source_span_end`
- `fts` generated `tsvector`
- `embedding`
- `embedding_model`
- `created_at`

#### `document_ai_runs`
- `id`
- `document_id`
- `run_type` (`summary`, `structured_extract`, `project_linking`, `career_extract`, `qna`)
- `status` (`queued`, `running`, `succeeded`, `failed`)
- `model`
- `prompt_version`
- `schema_version`
- `input_content_hash`
- `rerun_of`
- `output_json`
- `error_message`
- `token_input`
- `token_output`
- `estimated_cost`
- `created_at`, `completed_at`

### 연결/업무 객체
#### `document_links`
- `id`
- `document_id`
- `target_type` (`project`, `business_unit`)
- `target_id`
- `link_source` (`ai_suggested`, `user_confirmed`, `manual`)
- `confidence`
- `evidence_chunk_id`
- `created_at`, `confirmed_at`

#### `decisions`
- `id`
- `project_id`
- `document_id`
- `title`
- `description`
- `decision_date`
- `evidence_chunk_id`
- `created_at`

#### `todos`
- `id`
- `project_id`
- `document_id`
- `title`
- `description`
- `status` (`open`, `doing`, `done`, `dropped`)
- `due_date`
- `evidence_chunk_id`
- `created_at`, `updated_at`

#### `risks`
- `id`
- `project_id`
- `document_id`
- `title`
- `description`
- `severity`
- `mitigation`
- `status` (`open`, `mitigating`, `closed`)
- `evidence_chunk_id`
- `created_at`, `updated_at`

### 경력 자산
#### `career_highlights`
- `id`
- `owner_id`
- `project_id`
- `document_id`
- `title`
- `situation`
- `action`
- `result`
- `metrics`
- `skills`
- `evidence_chunk_id`
- `confidence`
- `created_at`, `updated_at`

#### `career_summaries`
- `id`
- `owner_id`
- `period_type` (`monthly`, `quarterly`, `project`, `custom`)
- `period_start`, `period_end`
- `summary_md`
- `highlights_json`
- `prompt_version`
- `model`
- `created_at`

### 검색/Q&A/파이프라인
#### `qna_sessions`
- `id`
- `owner_id`
- `question`
- `answer_md`
- `filters_json`
- `retrieved_chunk_ids`
- `citations_json`
- `model`
- `prompt_version`
- `created_at`

#### `ingest_jobs`
- `id`
- `document_id`
- `job_type` (`extract_text`, `chunk`, `summarize`, `structured_extract`, `embed`, `link_project`)
- `status` (`queued`, `running`, `succeeded`, `failed`, `skipped`)
- `dedupe_key`
- `attempt_count`
- `max_attempts`
- `last_error`
- `available_at`
- `started_at`
- `completed_at`
- `created_at`

### 검색 인덱스
- `document_chunks.fts`: GIN index.
- `document_chunks.embedding`: pgvector index.
- 주요 필터 인덱스: `documents.owner_id`, `projects.status`, `document_links.target_type/target_id`, `ingest_jobs.status/available_at`.

## 7) 파일 업로드 및 AI 분석 파이프라인

### 파이프라인 개요
1. **Upload**
   - 사용자가 파일 업로드.
   - 파일 크기, MIME type, 확장자 검증.
   - 원본 파일을 private storage에 저장.
   - `documents` row 생성.
   - `content_hash`로 중복 여부를 확인.
   - **중복 업로드 정책**: 동일 `owner_id + content_hash` 재업로드는 기존 `documents`를 재사용하고 새 ingest job을 만들지 않는다. 파일명만 다른 같은 원본은 기존 문서 상세로 안내한다.

2. **Job enqueue**
   - `ingest_jobs`에 `extract_text` job 생성.
   - 업로드 요청은 여기서 종료한다.

3. **Text extraction**
   - PDF/DOCX/TXT/MD 텍스트 추출.
   - 추출 결과를 `document_texts`에 저장.
   - 스캔 문서/OCR 필요 문서는 `processing_status='failed'`와 `unsupported_reason='unsupported_needs_ocr'`로 기록한다. 별도 `unsupported_needs_ocr` status enum은 만들지 않는다.
   - `unsupported_needs_ocr`는 자동 재시도 대상이 아니며, UI는 OCR 후순위/미지원 안내를 표시한다.

4. **Chunking**
   - 페이지/문단 기준으로 chunk 생성.
   - `document_chunks`에 content, page/span, FTS 대상 저장.

5. **AI summary**
   - OpenAI Responses API로 문서 요약 생성.
   - `document_ai_runs(run_type='summary')`에 output 저장.

6. **Structured extraction**
   - JSON Schema 기반으로 다음을 추출한다:
     - 프로젝트 후보
     - 사업부 후보
     - 결정사항
     - 할 일
     - 리스크
     - 경력 포인트
   - 결과는 `document_ai_runs`와 각 domain table에 저장하되, evidence chunk를 연결한다.

7. **Embedding / indexing**
   - chunk별 embedding 생성.
   - FTS/vector 검색 가능 상태로 전환.

8. **Project linking**
   - 기존 프로젝트/사업부와 유사도·키워드·AI 판단으로 연결 후보 생성.
   - `document_links`에 `ai_suggested`로 저장.
   - 사용자가 확인하면 `user_confirmed`로 확정.

9. **Review UI**
   - 문서 상세에서 원문, 추출 텍스트, 요약, 구조화 결과, 연결 상태, 실패/재시도 버튼을 확인한다.

### Idempotency / retry 원칙
- 문서 중복 기준: `owner_id + content_hash`. 같은 사용자가 같은 원본을 다시 올리면 기존 `documents` row를 재사용하고 신규 ingest chain은 만들지 않는다.
- job 중복 기준: `dedupe_key = document_id + job_type + input_content_hash + prompt_version/schema_version`.
- 같은 입력과 같은 버전은 중복 실행하지 않는다.
- 실패 job은 `attempt_count < max_attempts`일 때 재시도 가능.
- prompt/schema/model이 바뀌면 새 `document_ai_runs`를 만들고 `rerun_of`로 이전 실행을 연결한다.

### Citation 원칙
- MVP 최소 기준: chunk-level citation.
- 가능하면 `page_start/page_end`와 `source_span_start/source_span_end`를 함께 표시한다.
- Q&A 답변은 retrieved chunk와 answer citation을 분리해 저장한다.

## 8) 프로젝트별 관리 화면 구성

### Dashboard
- 최근 업로드 문서.
- 처리 실패/대기 상태.
- 진행 중 프로젝트.
- 오늘/이번 주 할 일.
- 열린 리스크.
- 이번 달 경력 하이라이트 초안.

### Inbox / Upload
- 파일 업로드.
- 처리 상태 timeline.
- 추출 실패 원인.
- 재시도.
- 자동 프로젝트 연결 추천 목록.

### Document Detail
- 원본 파일 메타데이터.
- 추출 텍스트.
- AI 요약.
- 구조화 추출 결과.
- 연결된 프로젝트/사업부.
- 결정/할일/리스크/경력 포인트 후보.
- 근거 chunk/page/span.
- 재분석 버튼.

### Project Detail
- 프로젝트 목표와 상태.
- 연결 문서 목록.
- 최근 변경/업로드.
- 결정사항 timeline.
- 할 일 Kanban 또는 list.
- 리스크 목록과 완화책.
- 관련 경력 하이라이트.
- “이 프로젝트 요약 생성” 버튼.

### Business Unit View
- 사업부별 프로젝트 목록.
- 진행 상태 요약.
- 사업부 관련 문서/리스크/성과.

### Search & Q&A
- 전체 검색창.
- 필터: 프로젝트, 사업부, 기간, 문서 타입, 상태.
- FTS 결과와 semantic result를 통합 표시.
- Q&A 답변에는 근거 chunk/document 링크 표시.

### Career Center
- 기간별 성과 요약.
- 프로젝트별 기여 요약.
- 스킬/도메인 키워드.
- STAR 형식 사례 초안.
- 이력서 bullet 초안.
- Markdown export.

### Settings
- 기본 언어/시간대.
- storage/export 정책.
- AI prompt/schema version 표시.
- 초기에는 복잡한 설정 최소화.

## 9) 경력 관리 기능 설계

### 기본 방향
경력 관리는 별도 수기 이력서 작성 도구가 아니라, 프로젝트와 문서에서 자연스럽게 파생되는 **career asset layer**로 설계한다.

### Career Highlight 생성 기준
문서/프로젝트에서 다음 신호를 추출한다.
- 완료한 일.
- 문제와 해결 방식.
- 의사결정 기여.
- 수치 지표 또는 정성 성과.
- 사용 기술/역량.
- 협업/리더십/운영 개선 사례.

### Career Summary 생성 단위
- 월간.
- 분기.
- 프로젝트 종료 시점.
- 사용자 지정 기간.

### 출력 형식
- 업무 회고 요약.
- 이력서 bullet.
- STAR 면접 답변 초안.
- 포트폴리오 프로젝트 설명.
- 역량 키워드 목록.

### 신뢰성 원칙
- 모든 career highlight는 근거 문서/chunk를 연결한다.
- AI가 만든 문장은 사용자가 편집/확정할 수 있게 한다.
- 지표가 없으면 “정량 지표 없음”으로 남기고 임의 수치를 만들지 않는다.

## 10) 개발 순서

1. **프로젝트 스캐폴딩**
   - Next.js App Router.
   - TypeScript, lint/test 기본값.
   - Supabase/Drizzle 환경 연결.

2. **DB/Storage 기반**
   - 핵심 schema/migration.
   - private storage bucket.
   - 최소 Auth 또는 개인 접근 보호.

3. **첫 번째 vertical slice**
   - 업로드.
   - 원본 저장.
   - `documents` row 생성.
   - `ingest_jobs` 생성.
   - 문서 상세/상태 화면.

4. **텍스트 추출**
   - TXT/MD 먼저.
   - 그다음 PDF/DOCX.
   - 실패/unsupported 상태 관리.

5. **AI 요약**
   - 문서 1건 요약.
   - `document_ai_runs` 저장.
   - 문서 상세에 표시.

6. **구조화 추출**
   - 결정/할일/리스크/경력 포인트 schema.
   - evidence chunk 연결.

7. **프로젝트/사업부 연결**
   - 수동 프로젝트 생성.
   - AI 추천 연결.
   - 사용자 확정 흐름.

8. **검색/Q&A**
   - FTS 검색.
   - embedding/vector 검색.
   - Q&A with citations.

9. **경력 센터**
   - career_highlights 목록.
   - 기간별 career_summaries 생성.
   - Markdown export.

10. **품질 보강**
   - 재처리/재시도 UX.
   - 비용/토큰 로그.
   - e2e 및 통합 테스트.
   - 데이터 export/backup.

## 11) 첫 번째 구현 단위

**문서 업로드 → 원본 저장 → 텍스트 추출 → AI 요약 저장 → 문서 상세 화면 표시**를 첫 구현 단위로 한다.

### 첫 구현 단위에 포함할 것
- 단일 사용자 접근 전제.
- 파일 업로드 UI.
- private storage 저장.
- `documents`, `document_texts`, `document_ai_runs`, `ingest_jobs` 최소 schema.
- TXT/MD 텍스트 추출부터 시작.
- AI 요약 1개 생성.
- 문서 상세에서 원본 메타데이터, 추출 텍스트, 요약, 처리 상태 표시.

### 첫 구현 단위에서 제외할 것
- 프로젝트 자동 연결.
- 검색/Q&A.
- 경력 요약.
- PDF/DOCX 전체 지원.
- OCR.

이렇게 시작하면 DB, storage, AI, job 상태, 화면을 모두 연결하면서도 범위를 과도하게 넓히지 않는다.

## 12) 수용 기준

### MVP 전체 수용 기준
1. PDF/DOCX/TXT/MD 중 지원 대상 파일 업로드 시 원본이 private storage에 저장되고 `documents` row가 생성된다.
2. 텍스트 추출 결과가 `document_texts`에 저장되고 실패 상태와 원인이 표시된다.
3. 문서 요약과 구조화 JSON이 schema에 맞게 저장된다.
4. 문서가 프로젝트/사업부 후보와 연결되고, 사용자가 확정/수정할 수 있다.
5. 키워드 검색과 의미 검색이 모두 동작한다.
6. Q&A 답변은 최소 chunk-level citation을 포함한다.
7. 프로젝트 화면에서 문서, 결정사항, 할 일, 리스크, 경력 포인트를 함께 볼 수 있다.
8. Career Center에서 기간별 경력 요약과 이력서 bullet 초안을 생성할 수 있다.
9. 핵심 파이프라인 실패 job은 재시도 가능하다.
10. 사용자는 원본/요약/경력 데이터의 Markdown 또는 JSON export를 받을 수 있다.

### 첫 구현 단위 수용 기준
1. TXT/MD 파일을 업로드하면 storage path, content hash, processing status가 저장된다.
2. 업로드 후 `ingest_jobs`가 생성된다.
3. TXT/MD 텍스트가 추출되어 `document_texts.full_text`에 저장된다.
4. AI 요약 결과가 `document_ai_runs.output_json`에 저장된다.
5. 문서 상세 화면에서 원본 메타, 처리 상태, 추출 텍스트, 요약을 확인할 수 있다.
6. 같은 `owner_id + content_hash` 재업로드 시 기존 `documents` row를 재사용하고 신규 ingest job을 만들지 않는다.
7. 요약 실패 시 실패 원인과 재시도 버튼이 표시된다.
8. 비로그인 요청은 document detail과 storage object를 읽을 수 없고, storage bucket은 public이 아니다.
9. 스캔/OCR 필요 문서는 `processing_status='failed'`, `unsupported_reason='unsupported_needs_ocr'`로 표시되고 자동 재시도 대상이 아니다.

## 13) 리스크와 완화책

| 리스크 | 영향 | 완화 |
|---|---|---|
| 범위가 SaaS로 커짐 | MVP 지연 | 단일 사용자/private-first 원칙 유지, 협업/RBAC/과금 제외 |
| OCR/스캔 PDF 난이도 | 추출 실패 증가 | MVP에서는 디지털 문서만 지원, OCR 후순위 |
| AI 비용/지연 | 업로드마다 비용 발생 | chunk 최소화, 캐시, 재처리 버전 관리, 토큰 로그 |
| 잘못된 구조화 추출 | 프로젝트/경력 데이터 품질 저하 | confidence, evidence chunk, 사용자 확정/수정 |
| 검색 품질 부족 | 자료 회수 실패 | FTS+vector 병행, 필터, 샘플 질의 평가 |
| 기밀 문서 노출 | 심각한 개인정보/업무 리스크 | private bucket, 접근 보호, export/삭제 정책, public sharing 제외 |
| 파이프라인 부분 실패 | 문서가 중간 상태에 멈춤 | `ingest_jobs` 상태머신, idempotency, retry, failure reason |
| AI 산출물 신뢰 문제 | 요약/경력 내용 검증 어려움 | 모델/prompt/schema/content hash/evidence 저장 |

## 14) 검증 계획

### Unit
- MIME/확장자 검증.
- content hash 계산.
- TXT/MD parser.
- chunk 생성.
- structured output schema validation.
- ingest job state transition.

### Integration
- upload API → storage → DB row → job 생성.
- job 실행 → text extraction → AI summary row 저장.
- FTS/vector indexing 함수.
- project link suggestion 저장/확정.

### E2E
- 사용자가 파일 업로드.
- 처리 완료까지 상태 확인.
- 문서 상세에서 요약 확인.
- 프로젝트 연결 확정.
- 검색/Q&A에서 근거가 포함된 답변 확인.
- Career Center에서 요약 생성.

### Observability / 운영 확인
- 실패 job count.
- 평균 처리 시간.
- AI token/cost.
- unsupported file count.
- 재시도 성공률.

## 15) ADR

### Decision
MVP는 **Next.js App Router + Supabase Postgres/Storage/Auth + Drizzle + OpenAI Responses/Structured Outputs/Embeddings + Postgres FTS/pgvector**로 설계한다. 데이터의 source of truth는 Supabase Postgres/Storage이며, AI 검색/요약 결과는 버전이 있는 파생 데이터로 저장한다.

### Drivers
- 개인 업무 기록을 장기적으로 소유하고 재사용해야 한다.
- 프로젝트/사업부/결정/할일/리스크/경력 포인트 간 관계가 중요하다.
- AI 결과의 근거와 재처리 가능성이 중요하다.
- 초기 구현은 작아야 하지만, 데이터 모델은 나중에 경력 자산화까지 버틸 수 있어야 한다.

### Alternatives considered
- OpenAI File Search 중심: 빠르지만 업무 그래프와 장기 데이터 소유권이 약하다.
- Firebase: 빠른 앱 개발은 가능하지만 관계형 업무 그래프와 provenance 질의가 약하다.
- FastAPI/Express 별도 백엔드: 확장성은 있으나 개인 MVP에는 운영 표면이 커진다.
- LangChain/LangGraph 중심: 복잡한 agent workflow에는 유리하나 현재는 과하다.

### Why chosen
이 제품은 파일 검색 도구가 아니라 **업무 맥락과 경력 자산을 축적하는 개인 데이터 제품**이다. 따라서 원본, 파생물, 관계, 근거, 재처리 이력을 DB 중심으로 통제하는 구조가 더 적합하다.

### Consequences
- 초기 구현에서 schema와 pipeline 설계를 신중히 해야 한다.
- 검색/Q&A를 직접 품질 관리해야 한다.
- 대신 프로젝트 연결, 경력 요약, export, 감사 가능성은 장기적으로 강해진다.

### Follow-ups
- 첫 구현 단위 완료 후 PDF/DOCX parser를 추가한다.
- 검색 품질 평가용 샘플 질문 세트를 만든다.
- Career Center는 프로젝트 연결과 구조화 추출이 안정된 뒤 구현한다.
- 데이터 export/backup 정책을 MVP 후반에 추가한다.

## 16) 합의 리뷰 반영 changelog
- Architect 제안 반영: provenance/version 필드 추가.
- Architect 제안 반영: `ingest_jobs` idempotency/retry semantics 추가.
- Architect 제안 반영: Q&A citation granularity를 chunk-level 이상으로 명시.
- Architect 제안 반영: OCR/scanned docs는 MVP 제외로 명확화.
- Architect 제안 반영: Supabase Auth는 제품 기능이 아닌 접근 경계로 정의.
- Dependency review 반영: LangChain, Firebase, custom backend, File Search 중심 구조는 후순위/대안으로 정리.
- Critic 제안 반영: 중복 업로드 정책, unsupported/OCR 상태 모델, private/Auth 검증 기준 추가.

## 17) Available Agent Types Roster
- `planner`: 작업 분해, 일정/순서 계획.
- `architect`: 데이터 모델, 파이프라인, 경계 검토.
- `critic`: 수용 기준, 리스크, 검증 가능성 심사.
- `executor`: 실제 구현.
- `test-engineer`: 테스트 전략과 테스트 작성.
- `verifier`: 완료 증거 확인.
- `dependency-expert`: SDK/패키지 선택 검토.
- `researcher`: 공식 문서/버전 확인.
- `designer`: 화면/UX 구조 설계.
- `code-reviewer`: 구현 후 코드 리뷰.

## 18) Follow-up Staffing Guidance

### 권장 기본 실행: `$ultragoal`
- 이유: 계획을 단계별 durable goal로 쪼개고, 첫 vertical slice부터 순차적으로 완료 증거를 남기기 적합하다.
- 추천 lane:
  - planner: goal ledger와 milestone 분해.
  - executor: 스캐폴딩/DB/upload 구현.
  - test-engineer: upload/extraction/AI mock 테스트.
  - verifier: 수용 기준별 증거 확인.

### 병렬 실행이 필요할 때: `$team` + `$ultragoal`
- Team은 병렬 구현 lane을 담당하고, Ultragoal은 durable checkpoint/ledger를 유지한다.
- 추천 team lane:
  1. DB/Storage lane: schema, migrations, bucket 정책.
  2. Upload/UI lane: inbox, document detail, status UI.
  3. Ingest/AI lane: extraction, summary, job 상태.
  4. Test/QA lane: integration/e2e, mock OpenAI.

### `$ralph` fallback
- Ralph는 기본 추천이 아니다.
- 단일 소유자가 끝까지 한 vertical slice를 고집스럽게 완료/검증해야 할 때만 명시적으로 선택한다.

## 19) Launch Hints

```bash
# 기본 durable goal 실행
$ultragoal ".omx/plans/work-support-platform-plan.md 기준으로 첫 vertical slice 구현"

# 병렬 팀 실행이 필요할 때
$team ".omx/plans/work-support-platform-plan.md 기준으로 DB/Storage, Upload/UI, Ingest/AI, Test lane 병렬 실행"

# tmux runtime에서 직접 실행 힌트
omx team "work-support 첫 vertical slice 구현: DB/Storage, Upload/UI, Ingest/AI, Test lane"
```

## 20) Team Verification Path
Team이 종료되기 전에 증명해야 할 것:
1. DB migration과 storage 정책이 적용 가능하다.
2. TXT/MD 파일 업로드가 DB/storage/job을 생성한다.
3. job 처리로 텍스트와 AI 요약이 저장된다.
4. 문서 상세 화면에서 상태/텍스트/요약이 보인다.
5. 실패 job 재시도와 에러 표시가 동작한다.
6. 테스트가 통과하고, OpenAI 호출은 mock 또는 test double로 검증된다.

Ultragoal checkpoint에는 각 항목의 테스트 로그, 변경 파일, 남은 리스크를 기록한다.

## 21) Goal-Mode Follow-up Suggestions
- **기본 추천: `$ultragoal`** — 이 계획을 구현 가능한 durable goals로 전환하고 순차 완료한다.
- **병렬 구현: `$team` + `$ultragoal`** — 여러 lane을 동시에 구현하되, 완료 증거는 Ultragoal에 checkpoint한다.
- **연구형 후속: `$autoresearch-goal`** — 현재 계획에는 필요 없다. OCR/문서 parser 품질 비교 같은 별도 연구가 생길 때만 사용한다.
- **성능 최적화 후속: `$performance-goal`** — MVP 후 처리 속도/비용/검색 latency를 측정 최적화할 때 사용한다.
