# AGENTS.md

## Project

This project is PersonalAI.

PersonalAI is a local Python AI assistant that aims to become the user's main work entry point for conversation, memory, safe tool use, Reader features, and future agent execution.

## Read First

Before working, read these docs when relevant:

- `docs/claude_code_start.md`
- `docs/project_handoff.md`
- `docs/development_workflow.md`
- `docs/check_workflow.md`
- `docs/core_principles.md`
- `docs/reader_memory_policy.md`
- `docs/memory_candidate_ui_policy.md`
- `docs/changelog.md`

## Autonomous Work Policy

後から修正できる操作は確認不要。

AI agents may proceed without user confirmation for normal reversible development work:

- code changes
- feature additions
- light refactoring
- tests
- docs updates
- file edits
- `git add`
- `git commit`
- `git push`
- branch creation
- normal merge
- fixup commits

## User Confirmation Required

Ask before 不可逆操作 or high-risk operations:

- force push
- `reset --hard`
- rebase
- Git history rewrite
- operations that may discard work
- DB削除
- DB初期化
- destructive DB schema changes
- Memory物理削除
- large file deletion
- external sending of API keys, personal information, or confidential information
- 課金, contract, purchase
- weakening PermissionManager or safety checks
- hard-to-reverse specification changes

Never delete or initialize `data/personal_ai.db` without explicit user approval.
Never physically delete Memory without explicit user approval.
Do not send API keys, personal information, or confidential information outside the local environment.
課金, contract, and purchase actions always require confirmation.

## User adaptation policy

- For Claude Code migration, start from `docs/claude_code_start.md`, then read `MIGRATION.md` and `README.md`.
- The user prefers action-oriented development once the goal is clear.
- Ask necessary questions proactively, but do not stop progress with excessive confirmations.
- Report completed behavior, checks, and user-facing verification points rather than detailed diffs.
- Prioritize actual usability, natural responses, and portfolio value.

## Cost and failure policy

- Prefer low-cost local development first.
- Avoid wasting API usage or agent quota through blind retry loops.
- Read logs before retrying.
- Do not repeat the same failing command many times without changing the cause.
- Prefer low-cost methods first, but recommend paid tools or stronger models when they clearly improve development speed, quality, stability, or portfolio value.
- Before any paid usage, explain the cost risk, expected benefit, and cheaper alternative, then ask the user.
- On failure, debug logs and fix safely.
- Do not delete or initialize the DB to fix errors.
- Do not use reset --hard, force push, or rebase without user confirmation.
- Do not remove safety checks just to make tests pass.

## Safety priority

- Do not over-block normal reversible development.
- User confirmation is mainly required for fatal risks: PC-breaking operations, large unexpected costs, important data loss, external leakage of sensitive information, destructive DB operations, and Git history destruction.

## Reporting

Report behavior and results to the user, not long code diffs.
Focus on what changed, what now works, checks run, commit hash, git status, and what the user should try.

Use this completion format:

```text
【VerX.X 完了まとめ】

1. 完了した内容
2. 実際にできるようになったこと
3. 実行したチェックと結果
4. commit hash
5. git status
6. ユーザーが確認すべき動作ポイント
7. 次に進めるVer候補
```
