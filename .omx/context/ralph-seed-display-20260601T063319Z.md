# Ralph Context Snapshot: user project seed display verification

## Task statement
Verify that the newly added user project seed data is displayed correctly in the actual work-support UI: project list, project detail, task board/list, work logs, outcomes, and career assets. Fix only seed-data display/mapping issues; do not add new features.

## Desired outcome
Seeded projects created by `scripts/seed_local.py --user-projects` are visible and correctly mapped across existing screens/APIs, with no duplicate creation on repeated seed runs.

## Known facts/evidence
- Existing backend Docker services are running: db and backend.
- `--user-projects` seed was added with `[user_project_seed]` marker and `generation_method=user_project_seed`.
- First seed run created 3 projects, 15 tasks, 9 logs, 6 outcomes, 3 career assets; second run created 0 of each.
- API `/projects` returns the three seed projects with task counts and progress.

## Constraints
- No new features.
- Fix only display/mapping problems for seed data.
- Existing data must not be deleted.
- Seed must remain local/dev only and idempotent.

## Unknowns/open questions
- Whether frontend pages fetch and render career assets/outcomes/logs correctly for these seeded projects.
- Whether task board/list tabs use backend task fields consistently.

## Likely codebase touchpoints
- `backend/scripts/seed_local.py`
- `frontend/app`, `frontend/src` pages/components/services
- `README.md`
- backend seed tests
