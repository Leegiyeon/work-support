# Context — work-support personal operations plan

Timestamp: 20260601T022934Z

## Task statement
work-support를 개인용 업무 플랫폼으로 실제 운영하기 위한 배포/보안/백업 계획을 수립한다. Docker Compose, PostgreSQL 백업, 업로드 파일 백업, 환경변수 관리, 인증, 로그 관리, 장애 복구 기준을 포함한다.

## Constraints
- Planning only: no application code changes.
- Personal-use MVP, not over-complex SaaS.
- Current stack: Docker Compose, FastAPI, Next.js, PostgreSQL/pgvector, local upload storage, OpenAI API planned/used by future slices.
- Sensitive personal work documents and career data must be treated as private.
- Current repo has active implementation churn from prior ultragoal requests; this plan must be operationally stable and not depend on unfinished code paths.

## Current repo evidence
- `docker-compose.yml` defines db/backend/frontend services and local volumes.
- `infrastructure/postgres/init/` contains bootstrap SQL.
- `storage/uploads/` is local file storage placeholder.
- Existing report access guard is local/personal-MVP only, not real production auth.
- Need canonical operational runbooks before exposing beyond localhost.

## External evidence consulted
- Docker Compose production, environment variables, and secrets docs.
- PostgreSQL `pg_dump`, `pg_basebackup`, and PITR/continuous archiving docs.
- OWASP authentication/session management cheat sheets.

## Output needed
A durable operations plan with phases, runbooks, backup/restore policy, security controls, log/monitoring policy, incident criteria, and acceptance tests. No code implementation.
