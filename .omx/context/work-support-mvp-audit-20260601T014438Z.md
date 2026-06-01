# Context Snapshot — work-support MVP implementation audit

## Task statement
현재 work-support 프로젝트의 MVP 기능 구현 상태를 전체 점검한다. 기준 기능: 프로젝트 관리, 업무 로그, 파일 업로드, AI 분석, RAG, 경력 자산화, 주간 리포트. 중복 코드, 책임 분리 문제, DB 구조 문제, API 일관성 문제, 프론트 UX 문제, 테스트 부족 영역을 정리하고 개선 계획만 작성한다. 코드는 수정하지 않는다.

## Desired outcome
- 현재 구현/미구현 상태를 기능별로 정확히 분류한다.
- 문제를 우선순위와 근거 파일/라인 중심으로 정리한다.
- MVP를 과도한 SaaS로 확장하지 않고 개인 업무 관리/경력 자산화 중심으로 개선할 순서를 제안한다.
- 실행 전 필요한 테스트/검증 계획을 문서화한다.

## Known facts / evidence
- README는 현재 저장소를 “MVP 초기 골격 + 주간 리포트 수직 슬라이스”라고 설명한다: `README.md:6-7`.
- 구현된 백엔드 라우터는 `/health`, `/reports/weekly`뿐이다: `backend/app/main.py:23-24`, `backend/app/api/reports.py:12-31`.
- 프로젝트/문서/추출 항목 테이블 DDL은 Python 문자열과 SQL 파일에 중복 존재한다: `backend/app/db/schema.py:3-70`, `infrastructure/postgres/init/002_work_support_schema.sql:1-66`.
- `projects`, `documents`, `extracted_items`는 존재하지만 프로젝트 CRUD, 문서 업로드, 텍스트 추출, AI 분석, RAG API/UI는 없다: `README.md:147-157`.
- `documents`에는 `extracted_text`, `summary`, `keywords`, `analysis_status` 등의 컬럼이 있으나 이를 채우는 파이프라인/API가 없다: `backend/app/db/schema.py:18-38`.
- `extracted_items`는 task/decision/risk/career_candidate/next_check를 하나의 generic table로 담는다: `backend/app/db/schema.py:40-52`.
- `ObjectStorage`는 Protocol만 있고 구현/업로드 endpoint는 없다: `backend/app/services/storage.py`.
- 주간 리포트는 owner header/token guard, owner_id 필터, 7일 제한, timezone을 포함한다: `backend/app/api/security.py:6-47`, `backend/app/services/weekly_report.py:72-144`, `backend/app/schemas/reports.py:14-20`.
- 프론트엔드는 홈과 `/reports`만 있다: `frontend/app/page.tsx`, `frontend/app/reports/page.tsx`.
- `/reports` 클라이언트는 `NEXT_PUBLIC_WORK_SUPPORT_REPORT_TOKEN`을 브라우저로 노출한다. 로컬 개인 MVP guard로는 허용 가능하지만 auth 대체는 아니다: `frontend/app/reports/page.tsx:25-27`, `README.md:117-118`.
- 테스트는 health와 weekly report 중심이다: `backend/tests/test_health.py`, `backend/tests/test_weekly_report.py`. 프론트 테스트는 없다.

## Constraints
- 계획만 작성. 애플리케이션 코드는 수정하지 않는다.
- 과도한 SaaS/auth/tenant/RBAC로 확장하지 않는다.
- 원본 파일/AI 분석 데이터는 민감 업무 자료로 취급한다.
- 개인 업무 관리와 경력 자산화 흐름을 우선한다.

## Unknowns / open questions
- 실제 사용자가 프로젝트/문서/업무 로그 데이터를 어떤 경로로 입력할지 아직 결정되지 않았다.
- 파일 업로드 후 원본 보관 정책, 허용 용량, 삭제/보존 정책이 세부화되지 않았다.
- AI 모델/비용/재시도/백그라운드 작업 방식이 아직 구현 전이다.
- RAG chunk 크기/embedding model/vector dimension/migration 전략이 아직 없다.

## Likely codebase touchpoints for future execution
- Backend: `backend/app/api/*`, `backend/app/services/*`, `backend/app/db/*`, `backend/app/schemas/*`, `backend/tests/*`
- Frontend: `frontend/app/*`, future shared components/hooks/api client
- Infrastructure: `infrastructure/postgres/init/*`, future migrations
- Docs: `README.md`, future `docs/architecture.md` or `docs/mvp-roadmap.md`
