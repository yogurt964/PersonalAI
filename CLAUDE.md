# CLAUDE.md

## Project

PersonalAI is a local personal AI assistant project.

It uses Python, SQLite, Ollama/Qwen, long-term memory, Web Reader, Memory Candidate, confirmation flows, ToolRunner, and PermissionManager.

The project is also intended as a job-hunting portfolio.

## Read first

Read these files before making substantial changes:

1. CLAUDE.md
2. AGENTS.md
3. MIGRATION.md
4. README.md
5. docs/claude_code_start.md
6. docs/development_workflow.md
7. docs/project_handoff.md
8. docs/check_workflow.md
9. docs/changelog.md

## Current development mode

The project is moving from Codex-based development to Claude Code-centered development.

Claude Code should work autonomously per version.

Do not ask the user to review code diffs for normal reversible changes.
Report behavior, checks, commit hash, git status, and user-facing verification points.

## User preferences

The user prefers:

- action-oriented development once the goal is clear
- proactive suggestions before the user has to point out missing requirements
- concrete implementation over repeated clarification
- copy-pasteable commands when user action is needed
- reports focused on what became possible, checks, and what to verify
- practical behavior tests over internal implementation details
- portfolio value and usability

## Autonomous development rules

For normal reversible development, Claude Code may proceed without asking:

- code edits
- docs updates
- test/check additions
- small refactors
- fake tests
- git add
- git commit
- git push
- fix commits
- updating version docs
- updating check scripts

Claude Code should:

1. understand the goal
2. inspect relevant files
3. implement
4. run targeted checks
5. run broader checks when appropriate
6. fix failures
7. commit
8. push
9. report in the required format

## Confirmation rules

Ask the user before fatal or hard-to-recover operations:

- PC-breaking operations
- OS / registry / driver / PATH major changes
- large unexpected costs
- paid contracts / purchases / subscriptions
- API key setup or external transmission of private data
- deleting data/personal_ai.db
- DB initialization
- destructive DB schema changes
- physical Memory deletion
- mass file deletion
- reset --hard
- force push
- rebase
- Git history rewrite
- weakening PermissionManager or major safety checks

Normal reversible mistakes and minor rework do not require confirmation.

## Cost rules

Avoid wasting API usage or Claude Code quota.

Do not blindly retry failing commands.
Read logs before retrying.
Do not run large loops or broad checks repeatedly without changing the cause.

The user is willing to pay when it clearly improves development speed, AI performance, quality, stability, or portfolio value.

Before paid usage, API usage, API key setup, or external transmission:

- explain cost risk
- explain expected benefit
- explain cheaper alternative
- ask the user

## Failure handling

On failure:

1. read the log
2. identify likely cause
3. make a small fix
4. rerun only necessary checks first
5. avoid infinite retries
6. do not delete or initialize the DB
7. do not remove safety checks just to pass tests
8. report honestly

## Checks

Use:

```powershell
venv\Scripts\python.exe -B scripts\check_verXXXX.py
venv\Scripts\python.exe -B scripts\run_ver2_checks.py
git diff --check
git status
```

CRLF warnings are acceptable.

SQLite disk I/O error or timeout may occur in normal runs.
Do not delete or initialize the DB.
If elevated rerun succeeds, treat it as a known environment issue.

## Git rules

Allowed without confirmation:

- git status
- git log
- git diff
- git add
- git commit
- git push
- normal fix commits

Require confirmation:

- reset --hard
- force push
- rebase
- history rewrite
- operations that may lose work

## Report format

```text
【VerX.XX 完了まとめ】

1. 完了した内容
2. 実際にできるようになったこと / 整ったこと
3. 実行したチェックと結果
4. commit hash
5. git status
6. ユーザーが確認すべきポイント
7. 次に進めるVer候補
```

## Next version policy

After each version, propose the next best version proactively.

If the next step is obvious and safe, prepare a concrete plan.

Do not start a new version automatically in the same report unless the user explicitly asked for continuous multi-version work.

For now, prefer one version per user instruction to avoid wasted usage and runaway loops.
