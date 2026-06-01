# Context Snapshot: work-support platform planning

## Task statement
Plan a new `work-support` project before writing code. The service is a personal work automation platform: users upload files, AI analyzes documents, and the system manages work by project/business unit, connecting progress status, decisions, todos, risks, and career-asset summaries.

## Desired outcome
A consensus planning artifact in Korean covering: service purpose, MVP scope, recommended stack, directory structure, database schema, upload/AI pipeline, project management screens, career management design, development sequence, and first implementation unit.

## Known facts / evidence
- Repository currently has no application code; only `.omx/` state exists.
- User explicitly requested planning only and no code modifications.
- Product should avoid overbuilt SaaS complexity and focus on personal work management plus career assetization.
- Required flow: original file storage, text extraction, AI summary, structured data extraction, project linking, search/Q&A.
- Current external references gathered for planning:
  - Next.js App Router docs: https://nextjs.org/docs/app
  - Supabase docs for Postgres, Storage, full-text search, pgvector: https://supabase.com/docs/
  - Drizzle migrations docs: https://orm.drizzle.team/docs/migrations
  - OpenAI Responses API / File Search / Structured Outputs / Embeddings docs: https://platform.openai.com/docs/

## Constraints
- No source code implementation in ralplan.
- Keep MVP small: single-user/personal-first, avoid premature enterprise SaaS features.
- Store originals, extracted text, summaries, structured entities, project links, search index, and Q&A traceability.
- Korean-first product language is acceptable.

## Unknowns / open questions
- Final hosting/provider preference and budget are not specified.
- Whether uploaded documents can include confidential corporate information; plan should assume privacy-sensitive handling.
- Whether the first release is local-only, private cloud, or public web app; plan should default to private single-user web app.
- Exact document formats are unspecified; MVP should prioritize PDF/DOCX/TXT/MD and allow image/OCR later.

## Likely codebase touchpoints
No code yet. Planned future touchpoints will be app scaffold, database schema/migrations, upload/storage service, extraction worker, AI analysis service, search/Q&A service, project UI, career UI, and tests.
