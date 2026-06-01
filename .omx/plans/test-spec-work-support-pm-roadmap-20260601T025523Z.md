# Test Spec — work-support PM Roadmap Next Slice

## Scope
Test strategy for the next implementation slice: “업무 로그 → 일일 자동 리포트”. This is a planning artifact only; no application code is modified in ralplan.

## Backend Tests

### Existing regression to fix
- `test_weekly_report_query_uses_owner_filter`
  - Replace brittle `len(captured) == 3` expectation with assertions that every report query has `owner_id` param and owner filtering.
  - Reason: automatic reports now include work-log related queries, raising captured query count to 5.

### Work-log owner/project integrity
- `POST /work-logs` with `project_id = null` returns 200/201 and stores a log for current owner.
- `POST /work-logs` with a project owned by current owner succeeds.
- `POST /work-logs` with a project owned by another owner returns 404 `PROJECT_NOT_FOUND` and does not insert a row.
- `POST /work-logs` with a nonexistent project returns 404 `PROJECT_NOT_FOUND` and does not reveal whether another owner has that ID.
- `GET /work-logs` returns only current owner logs in date range.
- `GET /work-logs` does not leak another owner’s project title.

### Automatic report API
- `POST /reports/automatic` with `report_type=daily` and one-day range returns `work_logs` and markdown containing the log title/content.
- `report_type=weekly` rejects periods longer than 7 days.
- `report_type=monthly` rejects periods longer than 32 days.
- Response includes stable arrays for `remaining_tasks`, `delayed_tasks`, `progress_candidates`, `monthly_performance_candidates` even when empty.
- UI/API copy treats `remaining_tasks`, `delayed_tasks`, and `progress_candidates` as candidate surfacing only; no persistent progress/task mutation occurs in Phase 1.
- Monthly performance candidates have `requires_user_metric_confirmation=true` when no confirmed metric exists.

## Frontend Tests / Verification

### Static checks
- `npm run lint`
- `npm run typecheck`
- `npm run build`

### UI behavior checks
- Reports page can select daily/weekly/monthly.
- Daily selection auto-aligns start/end date or clearly validates one-day range.
- Generate button calls `/api/reports/automatic`, not `/api/reports/weekly`, for the new unified flow.
- Loading, error, and empty states are visible.
- Work-log form validates required date/title/content and does not require a project selector in Phase 1.
- Work-log list renders project title when the API returns one and an unassigned label when project is null.
- Markdown copy button still works.
- UI labels clarify that outputs are stored-record based and metric numbers require user confirmation.

## Manual Smoke Scenario
1. Start backend/frontend with local env.
2. Create a work log for today without project.
3. Generate daily automatic report for today.
4. Confirm markdown includes the log.
5. Confirm work-log structured list includes the same log.
6. Confirm no fabricated numeric performance appears.
7. Copy markdown.

## Done Criteria
- Backend pytest green.
- Frontend lint/typecheck/build green.
- Owner isolation covered by automated tests.
- Report UI exposes input and output loop.
- No new DB table is introduced in this slice unless implementation discovers an unavoidable blocker.
