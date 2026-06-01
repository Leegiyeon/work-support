# Team Commit Hygiene Finalization Guide

- team: read-only-review-only-a274bc54
- generated_at: 2026-06-01T02:49:27.531Z
- lore_commit_protocol_required: true
- runtime_commits_are_scaffolding: true

## Suggested Leader Finalization Prompt

```text
Team "read-only-review-only-a274bc54" is ready for commit finalization. Treat runtime-originated commits (auto-checkpoints, merge/cherry-picks, cross-rebases, worker clean rebase scaffolds, leader integration signals, shutdown checkpoints) as temporary scaffolding rather than final history. Do not reuse operational commit subjects verbatim. Completed task subjects: READ-ONLY REVIEW ONLY. Do not create, edit, delete, or format any project files. | worker-2: Data Architect Agent + Backend Agent | worker-3: Frontend Agent + AI Workflow Agent + QA Agent. Final worker output mus. Rewrite or squash the operational history into clean Lore-format final commit(s) with intent-first subjects and relevant trailers. Use task subjects/results and shutdown diff reports to choose semantic commit boundaries and rationale.
```

## Commit Hygiene Vocabulary

### Operational commit kinds

- `auto_checkpoint` (auto-checkpoint) — A worker-local checkpoint commit created by the team runtime to preserve dirty worktree changes.
- `integration_merge` (integration merge) — A leader-side runtime merge commit that integrates a worker branch or checkpoint into the team branch.
- `integration_cherry_pick` (integration cherry-pick) — A leader-side runtime cherry-pick used when the normal worker merge path cannot be used cleanly.
- `cross_rebase` (cross-rebase) — A runtime rebase operation that moves worker work across the current leader branch baseline.
- `worker_clean_rebase` (worker clean rebase) — A runtime rebase that refreshes a clean worker branch onto the current leader branch baseline.
- `leader_integration_attempt` (leader integration attempt) — A leader-side integration attempt recorded for auditability even when it does not create a final semantic commit.
- `shutdown_checkpoint` (shutdown checkpoint) — A shutdown-time checkpoint commit that preserves remaining worker worktree changes before cleanup.
- `shutdown_merge` (shutdown merge) — A shutdown-time runtime merge that preserves worker changes on the leader branch before teardown.

### Operational commit statuses

- `applied` (applied) — The runtime operation changed repository history or preserved worker changes as intended.
- `noop` (no-op) — The runtime operation was unnecessary because there was no relevant change to preserve or integrate.
- `conflict` (conflict) — The runtime operation encountered conflicts that require human or leader-side reconciliation.
- `skipped` (skipped) — The runtime intentionally skipped the operation because prerequisites or safety checks were not met.

## Task Summary

- task-1 | status=completed | owner=worker-1 | subject=READ-ONLY REVIEW ONLY. Do not create, edit, delete, or format any project files.
  - description: READ-ONLY REVIEW ONLY. Do not create, edit, delete, or format any project files. Inspect the current work-support repository and report assigned role reviews. worker-1: Product Agent + Career Agent
  - result_excerpt: ## Metis Analysis: Product Agent + Career Agent Review (Task 1)

### Outcome
READ-ONLY review completed for Product Agent + Career Agent scope. No project files were created, edited, deleted, formatted, or committed. Repository is not a gi…
- task-2 | status=completed | owner=worker-1 | subject=worker-2: Data Architect Agent + Backend Agent
  - description: worker-2: Data Architect Agent + Backend Agent

BLOCKER reported by worker-2: task-2 is the assigned task for worker-2, but lifecycle ownership is inconsistent. Task is pending with owner=worker-1, and worker-2 claim-task returns claim_conflict. Worker-2 completed the read-only Data Architect + Backend analysis and sent it to leader in message ff8901ce-e9cb-4f54-8125-a20f4d7febdf. No project files were edited.
  - result_excerpt: Data Architect+Backend review delivered by worker-2 in mailbox message ff8901ce-e9cb-4f54-8125-a20f4d7febdf. Key findings: no projects/documents/uploads/RAG routes; owner-scoped FK integrity missing; create_work_log accepts unvalidated pro…
- task-3 | status=completed | owner=worker-1 | subject=worker-3: Frontend Agent + AI Workflow Agent + QA Agent. Final worker output mus
  - description: worker-3: Frontend Agent + AI Workflow Agent + QA Agent. Final worker output must include: role findings, gaps, must-have features, priority implementation sequence, first small task. No implementation.

BLOCKER(worker-3): read-only analysis was completed and delivered to leader in message c47a7186-a655-46da-8bb7-9037837c869d, but task owner is worker-1 so worker-3 claim-task returns claim_conflict; transition requires a claim_token. Leader must correct task ownership/claim or complete lifecycle from worker-1.
  - result_excerpt: Completed by worker-3 read-only analyst review; lifecycle closed through existing task owner worker-1 because task-3 was mis-owned and worker-3 claim-task returned claim_conflict.

Result summary:
- Role findings delivered to leader in mes…

## Runtime Operational Ledger

- No runtime-originated commit activity recorded.

## Finalization Guidance

1. Treat `omx(team): ...` runtime commits as temporary scaffolding, not as the final PR history.
2. Reconcile checkpoint, merge/cherry-pick, cross-rebase, and shutdown checkpoint activity into semantic Lore-format final commit(s).
3. Use task outcomes, code diffs, and shutdown diff reports to name and scope the final commits.

## Recommended Next Steps

1. Inspect the current branch diff/log and identify which runtime-originated commits should be squashed or rewritten.
2. Derive semantic commit boundaries from completed task subjects, code diffs, and shutdown reports rather than from omx(team) operational commit subjects.
3. Create final commit messages in Lore format with intent-first subjects and only the trailers that add decision context.
