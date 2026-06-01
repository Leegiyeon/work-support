# Context Snapshot: work-support MVP stack

- Task statement: Bounded dependency/stack evaluation for `$ralplan` planning only; no source-code edits.
- Desired outcome: concise MVP stack recommendation for a Korean personal-first work automation platform.
- Known requirements: upload files, store originals, extract text, AI summaries + structured extraction, project/business-unit linkage, search/Q&A, progress/decisions/todos/risks/career assetization.
- Constraints: empty new repo; avoid overbuilt SaaS; favor minimal MVP dependency boundaries; personal-first usage; planning only.
- Options under evaluation: Next.js full-stack + Supabase/Postgres/Storage + Drizzle + OpenAI APIs; Firebase; custom Express/FastAPI; LangChain-heavy stack; hosted OpenAI File Search only.
- Evidence sources: official docs, npm/PyPI registry metadata, GitHub API, OSV API quick vulnerability checks gathered on 2026-06-01 KST.
- Unknowns/open questions: exact deployment target, Korean OCR volume/file types, privacy/compliance posture, budget, single-user vs small-team timeline.
- Likely codebase touchpoints if implemented later: app routes/server actions, database schema/migrations, storage buckets/RLS, extraction jobs, embeddings/search tables, Q&A endpoint, Korean UI.
