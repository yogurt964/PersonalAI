# CLAUDE.md

## Project

PersonalAI is a local personal AI assistant (Python, SQLite, Ollama/Qwen, OpenAI API trial, long-term memory, Readers, Memory Candidate, confirmation flows, ToolRunner, PermissionManager).
It is also a job-hunting portfolio.

## Read first

Normally read only:

1. `CLAUDE.md` (this file)
2. `docs/current_status.md` (current focus, decisions, open issues, next work)

Do NOT read other docs by default. Open them only when the task needs them, and prefer the relevant section (grep / heading search) over the whole file.

| Need | Read |
|---|---|
| Conversation v0.1 spec / history | `docs/conversation_v01.md` |
| Memory / thinking design | `docs/memory_thinking_architecture.md`, `docs/memory.md` |
| Which checks exist | `docs/check_workflow.md` (relevant section only) |
| Cloud session details | `docs/cloud_development.md` |
| Past versions | `docs/changelog.md` — top entries or grep only |
| Implemented features / file map | `docs/project_handoff.md` — relevant section only |
| Safety / permission design | `docs/permission_manager.md`, `docs/tool_permission_design.md` |
| Product vision, portfolio | `docs/final_product_vision.md`, `README.md`, `docs/portfolio_readme_policy.md` |
| Migration background (historical) | `MIGRATION.md`, `AGENTS.md`, `docs/claude_code_start.md` |

If an older doc tells you to read many files or run all checks first, this file takes precedence.

## User preferences

Action once the goal is clear, proactive suggestions, concrete implementation over repeated clarification, copy-pasteable commands, reports on what became possible, practical behavior tests, portfolio value and usability.

## Autonomous development

Work autonomously per version. Do not ask the user to review diffs for normal reversible changes.
Report behavior, checks, commit hash, git status, and user-facing verification points.

Without asking: code/docs/check edits, small refactors, fake tests, git add, git commit, git push, fix commits.
Flow: understand goal → inspect relevant files → implement → targeted checks → broader checks when appropriate → fix → commit → push → report.

## Confirmation rules

Ask before fatal or hard-to-recover operations:

- PC-breaking operations; OS / registry / driver / PATH major changes
- large unexpected costs; paid contracts / purchases / subscriptions
- API key setup or external transmission of private data
- deleting `data/personal_ai.db`, DB initialization, destructive DB schema changes, physical Memory deletion
- mass file deletion
- reset --hard, force push, rebase, Git history rewrite, operations that may lose work
- weakening PermissionManager or major safety checks

## Cost rules

Avoid wasting API usage or Claude Code quota: do not blindly retry, read logs first, do not repeat broad checks without changing the cause, and do not load docs you do not need.
Task/answer accuracy is the top priority — do not starve quality to save cost.

OpenAI runs on a monthly budget cap, not per-call confirmation:

- agree the cap with the user before the first real connection; within it, routine OpenAI calls do not need per-call confirmation
- ask again when nearing/exceeding the cap or to raise it
- API key setup/changes always require confirmation
- external transmission of private/confidential data always requires confirmation, independent of the cap

Other paid usage / new API integration / external transmission: explain cost risk, benefit, cheaper alternative, then ask.

## Checks

Default: run the checks related to the changed code (version check, related `scripts/check_*.py`; see `docs/current_status.md`), plus `git diff --check` and `git status`.

Run the full suite (`scripts/run_ver2_checks.py`) before release/merge, for changes to shared core paths (PersonalAI, router, ToolRunner, PermissionManager, DB layer), or when targeted checks cannot cover the risk. Never skip verification that quality requires.

```powershell
venv\Scripts\python.exe -B scripts\check_verXXXX.py
venv\Scripts\python.exe -B scripts\run_ver2_checks.py
git diff --check
git status
```

CRLF warnings are acceptable. SQLite disk I/O error or timeout may occur: do not delete or initialize the DB; if an elevated rerun succeeds, treat it as a known environment issue.

## Failure handling

Read the log → identify the cause → small fix → rerun only the necessary checks first. No infinite retries, no DB deletion/initialization, no removing safety checks to pass tests. Report honestly.

## Keeping docs current

At the end of each version, overwrite `docs/current_status.md` (≤100 lines: focus, confirmed facts, open/unverified items, next work, base commit) in the same commit, and add history to `docs/changelog.md`. Never mark unverified progress as confirmed.

## Cloud sessions (claude.ai/code, mobile)

Linux VM cloned from GitHub (`CLAUDE_CODE_REMOTE=true`); `~/.claude/CLAUDE.md`, hooks and the local venv are not available.

- Respond in Japanese (technical terms/identifiers in English).
- Use `python3`; install deps (`pip install -r requirements.txt`) into a venv only when needed.
- `data/personal_ai.db`, DB backups, `.env`, API keys and personal data are not in the repo and must never be added or committed.
- Ollama / local models are unavailable. Prefer fake tests; report checks needing the real DB or Ollama as "cloud-unverified" and leave them for a local run (classification: `docs/cloud_development.md`).
- Do not call the OpenAI API unless the user explicitly agrees.
- Push only to the current feature branch, never to `main`. Record progress in docs so work can resume locally.

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

After each version, propose the next best version (with a concrete plan if obvious and safe). Do not start it automatically unless the user asked for continuous multi-version work.
