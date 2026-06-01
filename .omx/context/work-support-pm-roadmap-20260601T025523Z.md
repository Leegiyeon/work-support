# Context Snapshot — work-support PM Roadmap

## Task statement
방금 멀티에이전트 검토 결과를 PM 관점에서 통합한다. 목표는 work-support가 다음 3가지 목적을 달성하도록 구현 순서를 재정리하는 것이다.

1. 프로젝트 진척도 및 잔여 업무 관리
2. 프로젝트별 실제 수행 업무 전산화
3. 개선 성과 수치화 및 경력관리

코드 수정 금지. 최종 구현 계획만 작성한다.

## Constraints
- Ralplan planning-only: application/source files must not be edited.
- Personal 업무 관리와 경력 자산화 중심; 과도한 SaaS 확장 금지.
- AI/자동 생성은 실제 저장 데이터 근거 기반이어야 하며 수치 성과는 사용자가 확정해야 한다.
- Current evidence is from repository inspection and the just-completed multi-agent review; prior mailbox file no longer exists after team shutdown.

## Current implementation evidence
- FastAPI only registers health, reports, and work_logs routers (`backend/app/main.py:4-30`). Root/scope text explicitly says upload, AI analysis, and login are not implemented in this slice (`backend/app/main.py:14-17`, `backend/app/main.py:33-39`).
- PostgreSQL schema currently includes `projects`, `documents`, `extracted_items`, and `work_logs` (`infrastructure/postgres/init/002_work_support_schema.sql:4-61`). There are no `project_tasks`, `project_outcomes`, `career_assets`, `document_chunks`, or analysis-run/provenance tables.
- Current FKs are `project_id -> projects(id)` while rows also carry `owner_id`, so owner-scoped relational integrity is not enforced at DB level (`infrastructure/postgres/init/002_work_support_schema.sql:15-61`).
- `create_work_log` inserts `payload.project_id` directly without checking that the project belongs to the request owner (`backend/app/services/work_logs.py:9-28`).
- `list_work_logs` is owner-filtered and left-joins project titles with owner filtering (`backend/app/services/work_logs.py:31-46`).
- Backend reports API has `/reports/weekly` and `/reports/automatic` (`backend/app/api/reports.py:19-64`). Automatic report is built from `fetch_weekly_report_dataset`, so it reuses stored records, not external AI.
- Frontend reports page currently calls `/api/reports/weekly` and stores `WeeklyReportResponse` only (`frontend/app/reports/page.tsx:29-59`). It does not use `/api/reports/automatic` despite the proxy existing (`frontend/app/api/reports/automatic/route.ts:1-7`).
- Frontend work-log proxy exists (`frontend/app/api/work-logs/route.ts:1-11`), but no visible work-log screen/form was found.
- Frontend types already include `AutoReportResponse`, `WorkLogItem`, task alerts, progress candidates, and monthly performance candidates (`frontend/app/reports/types.ts:1-67`).
- Current backend test run: `backend/.venv/bin/python -m pytest -q` => 14 passed, 1 failed. Failing test is `test_weekly_report_query_uses_owner_filter`, which still expects exactly 3 report queries but current implementation executes 5 due added work-log/report data queries (`backend/tests/test_weekly_report.py:159-205`).
- Frontend validation: `npm run lint && npm run typecheck && npm run build` passed. Build routes include `/`, `/reports`, `/api/reports/automatic`, `/api/reports/weekly`, `/api/work-logs`.

## Prior multi-agent review synthesis
- Product/Career: the product is not yet a usable personal work platform because work-log capture is API-only, progress dashboard is missing, and career/outcome assets are transient or absent.
- Data/Backend: owner-safe project linking and tests must precede new features; `project_outcomes`/`career_assets` should come after reliable work-log/task/project evidence exists.
- Frontend/AI/QA: the backend has deterministic automatic-report pieces, but UI exposes only weekly markdown. AI wording should remain “근거 기반 자동 생성” until real OpenAI/provenance is implemented.

## Main planning implication
The next PM-prioritized implementation should not start with broad career export or AI/RAG. It should first close the smallest end-to-end evidence loop: create/list work logs, generate automatic daily/weekly/monthly reports from them, display remaining/delayed/progress candidates, and keep all outputs explicitly grounded in stored records.
