# PRD — work-support PM Roadmap for MVP 목적 달성

## 1. Requirements Summary

work-support의 최종 목적 3가지를 달성하기 위해 구현 순서를 재정리한다.

1. **프로젝트 진척도 및 잔여 업무 관리**: 프로젝트 상태, 남은 일, 지연 업무, 진행률 후보를 볼 수 있어야 한다.
2. **프로젝트별 실제 수행 업무 전산화**: 사용자가 매일 수행 업무를 기록하고 프로젝트와 연결할 수 있어야 한다.
3. **개선 성과 수치화 및 경력관리**: 실제 기록과 근거 문서/업무 로그를 기반으로 성과 후보와 경력 문장을 만들고, 수치는 사용자가 확정해야 한다.

## 2. 현재 구현된 것

- Backend 라우터: health, reports, work_logs만 등록됨 (`backend/app/main.py:4-30`).
- Backend 보고서 API: `/reports/weekly`, `/reports/automatic` 존재 (`backend/app/api/reports.py:19-64`).
- Backend 업무 로그 API: `/work-logs` GET/POST 존재. 단, `create_work_log`는 `project_id` 소유자 검증 없이 삽입한다 (`backend/app/services/work_logs.py:9-28`).
- DB: `projects`, `documents`, `extracted_items`, `work_logs` 존재 (`infrastructure/postgres/init/002_work_support_schema.sql:4-61`).
- Frontend: `/reports` 화면은 주간 리포트 생성만 노출하고 `/api/reports/weekly`만 호출한다 (`frontend/app/reports/page.tsx:29-59`).
- Frontend: `/api/reports/automatic`, `/api/work-logs` 프록시와 자동 리포트 타입 정의는 존재한다 (`frontend/app/api/reports/automatic/route.ts:1-7`, `frontend/app/api/work-logs/route.ts:1-11`, `frontend/app/reports/types.ts:1-67`).
- 검증 현황: frontend lint/typecheck/build 통과. backend pytest는 14 passed, 1 failed이며 owner-filter 쿼리 수 기대값이 낡았다 (`backend/tests/test_weekly_report.py:159-205`).

## 3. 부족한 것

### 목적 1: 진척도 및 잔여 업무 관리
- 프로젝트 대시보드/상세 흐름이 현재 코드 기준으로 앱에 노출되어 있지 않다.
- `project_tasks` 같은 관리형 업무 테이블이 없다. 현재 할 일은 `extracted_items(item_type='task')` 기반 후보에 가깝다.
- 진행률 후보는 자동 리포트 타입에는 있으나 UI에서 보이지 않고 사용자 확정/저장 흐름도 없다.

### 목적 2: 실제 수행 업무 전산화
- 업무 로그 API는 있으나 UI 입력 폼/목록이 없다.
- 업무 로그 생성 시 프로젝트 소유자 검증이 없다.
- 기간 범위, 빈 상태, 오류 상태, 프로젝트 연결 UX가 부족하다.

### 목적 3: 성과 수치화 및 경력관리
- `project_outcomes`, `career_assets` 테이블이 없다.
- 성과 후보/경력 문장이 근거·버전·사용자 수정 상태와 함께 저장되는 구조가 없다.
- “AI가 수치를 만들지 않고 사용자가 확정한다”는 제품 규칙이 DB/API/UI에 강제되어 있지 않다.

## 4. RALPLAN-DR Summary

### Principles
1. **Evidence first**: 진행률, 성과, 경력 문장은 `work_logs`, `projects`, `documents`, `extracted_items` 같은 저장 근거와 연결되어야 한다.
2. **Small vertical slice first**: 큰 스키마 확장보다 사용자가 매일 쓸 수 있는 입력→요약→검토 루프를 먼저 완성한다.
3. **User-confirmed metrics**: AI/자동화는 후보를 제안할 수 있지만 수치 성과 확정은 사용자만 한다.
4. **Owner/project integrity before scale**: 개인용이라도 owner/project 관계 무결성을 먼저 막아야 이후 백업·인증·확장에 안전하다.
5. **Visible value in UI**: API만 있는 기능은 MVP 완료로 보지 않는다. 입력과 결과가 같은 제품 흐름에서 보여야 한다.

### Decision Drivers
1. 현재 이미 존재하는 `work_logs` + `/reports/automatic` 축을 가장 적은 변경으로 제품화할 수 있다.
2. 현재 backend 테스트가 red이며 owner 검증 결함이 있어 새 기능보다 안정화가 선행되어야 한다.
3. 경력 자산화는 신뢰 가능한 업무 기록/성과 근거가 쌓인 뒤에야 품질이 올라간다.

### Viable Options

#### Option A — 업무 로그/자동 리포트 vertical slice 우선 (Chosen)
- 접근: red test와 owner validation을 먼저 고치고, 업무 로그 입력 UI와 자동 리포트 UI를 연결한다.
- 장점: 세 목적의 공통 기반인 “실제 수행 기록”을 가장 빨리 만든다. DB 변경이 거의 없고 검증이 명확하다.
- 단점: 성과/경력 저장 테이블은 다음 단계로 미뤄진다.

#### Option B — DB 모델 확장 우선
- 접근: `project_tasks`, `project_outcomes`, `career_assets`를 먼저 설계/마이그레이션한다.
- 장점: 장기 구조가 빨리 고정된다.
- 단점: 입력 UX 없이 빈 테이블만 늘어날 위험이 크고, 현재 red test/owner 결함을 방치한다.

#### Option C — 프로젝트 대시보드 우선
- 접근: 프로젝트 상세/진척도 UI부터 만든다.
- 장점: 목적 1의 가시성이 빨리 생긴다.
- 단점: 실제 수행 기록이 부족하면 진척도와 경력 생성이 다시 추정/수동 입력에 의존한다.

## 5. ADR

### Decision
다음 구현 순서는 **Option A: 업무 로그 기반 자동 리포트 vertical slice**를 1순위로 한다. 이후 관리형 업무, 성과 수치화, 경력 자산화 순서로 확장한다.

### Drivers
- 이미 있는 API/타입/스키마를 활용해 가장 작은 제품 가치를 만들 수 있다.
- 업무 로그가 있어야 진척도·잔여 업무·성과·경력 문장의 근거가 생긴다.
- 현재 테스트 실패와 owner validation 결함을 먼저 고쳐야 후속 기능의 데이터 신뢰성을 확보한다.

### Alternatives considered
- DB 모델 확장 우선: 장기적으로 필요하지만 현재 사용 흐름이 없는 상태에서 복잡도만 키운다.
- 프로젝트 대시보드 우선: 시각적으로 좋지만 실제 기록 입력 루프가 없으면 경력 자산화 목적에 약하다.

### Why chosen
PM 관점에서 MVP는 “매일 기록 → 자동 정리 → 남은 일/지연/진척 후보 확인 → 나중에 성과·경력으로 승격” 루프가 먼저 살아야 한다. 이 루프가 세 목적 모두의 최소 공통분모다.

### Consequences
- 다음 구현은 큰 DB 확장 없이 진행 가능하다.
- 성과/경력 테이블은 Phase 3~4로 명확히 지연된다.
- 자동 생성 결과는 AI가 아니라 “저장 데이터 기반 자동 보고서”로 표시해야 한다.

### Follow-ups
- Phase 2에서 `project_tasks` 또는 `extracted_items` 승격 모델 결정.
- Phase 3에서 `project_outcomes` 추가.
- Phase 4에서 `career_assets` 추가.
- Phase 5에서 OpenAI/문서/RAG provenance hardening.

## 6. Prioritized Implementation Roadmap

### Phase 0 — Stabilization gate (가장 먼저)
**목표**: red test 제거와 owner/project 무결성 보강.

- Backend
  - `test_weekly_report_query_uses_owner_filter`를 “쿼리 수 3개”가 아니라 “모든 report query가 `owner_id` 파라미터와 owner filter를 가진다”로 갱신.
  - `fetch_weekly_report_dataset`의 `work_logs` 중복 조회(`backend/app/services/weekly_report.py:135-146`, `180-191`)는 Phase 0 권장 정리 작업으로 한 번만 조회하도록 단순화한다. 단, 회귀 테스트는 쿼리 수가 아니라 owner-filter semantics를 검증한다.
  - `create_work_log`에서 `project_id`가 제공되면 해당 project가 현재 `owner_id` 소유인지 검증한다. 없는 프로젝트와 타 owner 프로젝트는 모두 **404 `PROJECT_NOT_FOUND`**로 거절해 존재 여부를 누설하지 않는다.
  - `/work-logs` create/list 테스트 추가: null project 허용, owner project 허용, 타 owner project 거절, 기간 필터.
- Frontend
  - 변경 없음 또는 API 에러 메시지 계약만 확인.
- DB 변경 필요 여부
  - 이번 단계는 **DB 변경 없이 서비스 검증으로 가능**.
  - 추후 owner-scoped FK/unique 제약은 별도 migration로 검토.
- Test gate
  - `backend/.venv/bin/python -m pytest -q` green.

### Phase 1 — Smallest vertical slice: 업무 로그 → 자동 리포트 UI
**목표**: 사용자가 실제 업무를 입력하고, 일/주/월 리포트와 잔여·지연·진척 후보를 확인한다.

- Backend/API
  - 기존 `/work-logs` GET/POST 사용.
  - 기존 `/reports/automatic` 사용.
  - report_type별 기간 검증 명확화: daily는 1일, weekly는 최대 7일, monthly는 최대 32일.
  - 자동 리포트 응답의 `work_logs`, `remaining_tasks`, `delayed_tasks`, `progress_candidates`, `monthly_performance_candidates` 테스트 추가.
- Frontend
  - `/reports`를 weekly-only에서 자동 리포트 화면으로 전환.
  - report type selector: daily / weekly / monthly.
  - 업무 로그 작성 폼: 날짜, 제목, 내용, blockers. 현재 프로젝트 목록 API가 없으므로 Phase 1 UI는 **미지정 로그 중심**으로 만들고, 프로젝트 선택 UI는 Phase 2의 프로젝트/업무 관리 화면에서 도입한다.
  - 업무 로그 목록: 기간 내 로그, blockers 표시. API가 기존 데이터의 `project_title`을 반환하면 표시하되, Phase 1 UI에서 새 로그에 프로젝트를 선택시키지는 않는다.
  - 자동 리포트 섹션: Markdown, 업무 로그, 남은 일, 지연 업무, 진척도 후보, 월간 성과 후보.
  - Phase 1의 남은 일/지연 업무/진척도는 **persistent task/progress management가 아니라 후보 노출(candidate surfacing)**로 라벨링한다. 실제 저장·확정 관리는 Phase 2에서 `project_tasks`와 progress confirmation으로 승격한다.
  - “저장된 근거 기반 / 수치 성과는 사용자 확정 필요” 안내 문구 추가.
- DB 변경 필요 여부
  - **없음**. 기존 `work_logs`, `projects`, `extracted_items` 사용.
- Test gate
  - Backend pytest green.
  - Frontend `npm run lint`, `npm run typecheck`, `npm run build` green.
  - 수동 smoke: 업무 로그 생성 → daily 리포트 생성 → Markdown 복사 → 구조화 섹션 표시.

### Phase 2 — 프로젝트 진척도/잔여 업무 관리
**목표**: 목적 1을 제품 기능으로 완성.

- DB 변경 필요
  - `project_tasks` 테이블 추가 권장: `id`, `owner_id`, `project_id`, `title`, `description`, `status`, `priority`, `due_date`, `source_type`, `source_id`, `created_at`, `updated_at`.
  - 대안: `extracted_items(item_type='task')`에 관리 필드를 추가하고 “승격된 task”로 사용. 단, 문서 추출 후보와 사용자가 관리하는 업무가 섞일 위험이 있어 장기적으로는 별도 `project_tasks`가 낫다.
- Backend/API
  - project CRUD/lookup이 현재 앱에 없으면 먼저 최소화해 추가.
  - `/projects/{id}/tasks` CRUD.
  - `/projects/{id}/progress-candidates` 조회/확정.
- Frontend
  - 프로젝트 목록/상세, task board/list, 잔여/지연 필터.
  - 업무 로그 입력 시 프로젝트와 task 연결 가능.
- Test gate
  - task CRUD, owner isolation, status transition, delayed detection.

### Phase 3 — 개선 성과 수치화
**목표**: 목적 3의 “성과 수치화”를 근거 기반으로 구현.

- DB 변경 필요
  - `project_outcomes`: `id`, `owner_id`, `project_id`, `metric_name`, `before_text`, `after_text`, `numeric_value`, `unit`, `qualitative_summary`, `evidence_refs`, `requires_metric_confirmation`, `resume_ready`, `created_at`, `updated_at`.
- Backend/API
  - 성과 후보 생성/등록/수정/확정 API.
  - 수치가 없으면 `numeric_value`를 비워두고 정성 성과로 분리.
  - evidence_refs는 work_log/document/extracted_item/task 참조를 JSONB 또는 join table로 관리.
- Frontend
  - 프로젝트 상세과 경력 화면에 성과 카드 표시.
  - 수치 확정 UI와 근거 문서/업무 로그 연결 UI.
- Test gate
  - AI/자동화가 numeric_value를 임의 확정하지 못하는 테스트.
  - evidence 없는 resume_ready 방지.

### Phase 4 — 경력 자산화 저장/편집/Export
**목표**: 실제 이력서/포트폴리오/면접 문장으로 쓸 수 있는 자산 관리.

- DB 변경 필요
  - `career_assets`: `id`, `owner_id`, `project_id`, `outcome_id`, `asset_type`, `content`, `evidence_refs`, `status`, `generated_by`, `model`, `prompt_version`, `created_at`, `updated_at`.
- Backend/API
  - 이력서/경력기술서/포트폴리오/STAR/기간 요약 생성 및 저장.
  - 사용자 수정 저장.
- Frontend
  - 경력 관리 화면, asset editor, Markdown export, copy button.
- Test gate
  - 수치 없는 성과 임의 생성 금지.
  - 저장된 evidence 기반 문장 생성.

### Phase 5 — 문서/RAG/AI provenance 확장
**목표**: 문서 분석과 프로젝트 Q&A를 신뢰 가능하게 확장.

- DB 변경 필요
  - `document_chunks`, embedding vector, `document_analysis_runs`, source span/page refs.
- Backend/API
  - 업로드/텍스트 추출/분석/RAG 재시도 가능 pipeline.
  - OpenAI prompt/schema versioning.
- Frontend
  - 문서 업로드/분석 상태/출처 기반 Q&A.
- Test gate
  - chunk owner/project isolation, source citation, retry status, schema parse failure handling.

## 7. 이번에 구현할 가장 작은 vertical slice

### Slice name
**업무 로그 → 일일 자동 리포트**

### Scope
1. backend red test 수정: owner-filter 테스트가 현재 5개 쿼리 구조를 허용하도록 변경.
2. `POST /work-logs`에서 `project_id` owner validation 추가. Backend/API는 프로젝트 연결을 검증하지만, Phase 1 UI는 프로젝트 선택 없이 미지정 로그 중심으로 둔다.
3. backend 테스트 추가: 업무 로그 생성/조회/타 owner project 거절, `/reports/automatic` daily 응답에 업무 로그 포함.
4. frontend `/reports`에서 report_type을 daily/weekly/monthly로 선택하고 `/api/reports/automatic` 호출.
5. frontend에서 업무 로그 입력 폼(프로젝트 선택 제외), 기간 내 로그 목록, 자동 리포트 구조화 섹션, Markdown 복사 버튼 표시.

### Explicitly out of scope
- `project_tasks`, `project_outcomes`, `career_assets` 신규 테이블.
- OpenAI 기반 생성, 문서 업로드/RAG, 이메일/n8n 연동.
- 인증 고도화. 기존 owner/token guard 범위 안에서만 진행.

### Acceptance Criteria
- 업무 로그를 프로젝트 없이 생성할 수 있다.
- 현재 owner의 프로젝트에는 업무 로그를 연결할 수 있다.
- 다른 owner의 프로젝트 ID로 업무 로그 생성 시 저장되지 않고 안정적인 에러를 반환한다.
- daily report는 선택한 하루의 work_logs를 Markdown과 구조화 목록에 표시한다.
- weekly/monthly report는 report_type에 맞는 기간 제한을 적용한다.
- UI는 empty/loading/error 상태를 표시한다.
- 자동 생성 문구는 “저장된 근거 기반”과 “수치 성과는 사용자 확정 필요”를 명시한다.
- `backend/.venv/bin/python -m pytest -q`, `npm run lint`, `npm run typecheck`, `npm run build`가 통과한다.

## 8. API/Frontend/DB Change Scope Summary

| Phase | DB 변경 | Backend/API | Frontend |
|---|---:|---|---|
| 0 안정화 | 없음 | 테스트 갱신, work_log owner validation | 없음 |
| 1 업무 로그 자동 리포트 | 없음 | `/work-logs`, `/reports/automatic` 테스트/검증 강화 | `/reports` 자동 리포트화, 업무 로그 폼/목록 |
| 2 진척도/잔여 업무 | 있음 | `project_tasks`, project/task/progress API | 프로젝트/업무 관리 UI |
| 3 성과 수치화 | 있음 | `project_outcomes` API, evidence validation | 성과 카드/수치 확정 UI |
| 4 경력 자산화 | 있음 | `career_assets` API, export API | 경력 편집/export UI |
| 5 문서/RAG | 있음 | chunks/analysis/RAG API | 업로드/분석/Q&A UI |

## 9. Risks and Mitigations

- Risk: 업무 로그 UI만 만들고 프로젝트/업무 관리가 약하게 남을 수 있다.
  - Mitigation: Phase 1 acceptance에 remaining/delayed/progress candidate 표시를 포함해 Phase 2와 연결한다.
- Risk: 자동 리포트가 AI처럼 보이면 사용자가 과신할 수 있다.
  - Mitigation: “저장 데이터 기반 자동 보고서”로 라벨링하고, 수치 확정은 사용자 책임으로 명시한다.
- Risk: owner validation을 서비스 레이어에만 두면 장기적으로 누락 가능하다.
  - Mitigation: Phase 0은 서비스 검증으로 막고, Phase 2~3 migration에서 owner-scoped FK/unique 전략을 재검토한다.
- Risk: `project_tasks`와 `extracted_items` 책임이 겹친다.
  - Mitigation: extracted_items는 AI/문서 추출 후보, project_tasks는 사용자가 관리하는 실행 업무로 분리한다.

## 10. Follow-up Staffing Guidance

### Recommended `$ultragoal` path
- Use `$ultragoal` for Phase 0~1 sequential delivery.
- Suggested lanes: backend stability first, then frontend report/work-log UI, then verification.

### Recommended `$team` path
Use `$team` only if Phase 1 is expanded beyond the small slice.
- Backend Agent: owner validation, work-log/report tests.
- Frontend Agent: report type selector, work-log form/list, structured sections.
- QA Agent: end-to-end smoke checklist and regression verification.

### `$ralph` fallback
Use `$ralph` only if a persistent single-owner fix/verify loop is explicitly wanted after the plan, not as the default.

### Available agent types roster
planner, architect, critic, executor, test-engineer, verifier, designer, code-reviewer, explore, debugger, writer.

## 11. Changelog

- Initial PM-integrated plan created from repository evidence and prior multi-agent review.
- Architect review suggestions applied: duplicate work-log query policy, fixed 404 `PROJECT_NOT_FOUND` cross-owner project policy, and Phase 1 candidate-surfacing boundary.
- Critic review non-blocking suggestions applied: Phase 1 project selection UI deferred to Phase 2, report period validation wording made firm, and duplicate work-log query cleanup marked as Phase 0 recommended simplification.
