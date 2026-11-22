# Cloud Development (claude.ai/code)

クラウドセッション（Linux VM、`CLAUDE_CODE_REMOTE=true`）から開発するときの実測メモ。
守るべきルール（DB・APIキー・OpenAI・pushブランチ）は `CLAUDE.md` の「Cloud sessions」を正とし、ここでは繰り返さない。

## 確認済みの動作状況（2026-11-22, commit 43b85c9 時点）

- ブランチ `feature/conversation-v0.1` がcloneされ、origin と一致
- Python 3.13.18
- `core/` `ai/` `database/` の71ファイルは `ast.parse` で構文エラー0件
- システムPythonには `sqlalchemy` `ollama` `openai` `youtube-transcript-api` が無い → venv に `requirements.txt` を入れて実行する
- `data/` は存在しない（`database/models.py` は相対パス `sqlite:///data/personal_ai.db` を使う）
- Ollama・OpenAIキーは無い
- feature ブランチへの commit / push ができることを確認済み

## テスト分類（`scripts/*.py` 132本を実行して確認）

| 区分 | 本数 | 対象 |
|---|---|---|
| クラウドでそのまま通る | 89 | DB不要の fake テスト |
| 空スキーマDBがあれば通る | 20 | `check_ver013/015/016/017/018/019/022/023/230/240/250/280/2380/2420/2430/2470/2490/2500`, `list_memories`, `show_memory_context` |
| Ollama必須（cloud-unverified） | 3 | `check_ver2530`, `check_ver2610`, `benchmark_capability_classification` |
| 本番DB必須（cloud-unverified） | 1 | `diagnose_conversation_context` |
| DB書き込み検知でNG（要ローカル確認） | 12 | `check_ver2110/2130/2160/2170/2180/2190/2200/2290/2310/2320/2330/2360` |
| Windowsパス前提でLinuxではNG | 3 | `check_ver2370/2410/2480`（スペース入りパス抽出がドライブレター形式のみ対応） |
| 対象外 | 4 | `manage_memory_status`（引数必須）, `run_ver1_checks` / `run_ver2_checks` / `run_pre_v1_checks`（上記NGを含むため常に失敗） |

そのため、クラウドでは `run_ver2_checks.py` の結果で合否判断しない。変更に関係する個別 check を実行する。

## ローカルPCが必要な作業

- Ollama / Qwen を使う動作確認・check
- 本番DB（`data/personal_ai.db`）を使う確認、DB書き込み系 check（上表の12本）
- Windowsパス前提の check（上表の3本）と `run_ver2_checks.py` の最終確認
- OpenAI API の実接続（月額上限の合意後）

## クラウドからの開発手順

1. `git branch --show-current` で `feature/conversation-v0.1` を確認
2. 必要なら作業用 venv を作る（リポジトリ外が望ましい）
   ```bash
   python3 -m venv /tmp/venv && /tmp/venv/bin/pip install -q -r requirements.txt
   ```
3. 実装し、関係する check を個別に実行（`-B` を付けて `__pycache__` を作らない）
   ```bash
   /tmp/venv/bin/python -B scripts/check_verXXXX.py
   ```
4. DBが必要な check を試す場合は、リポジトリのコピー内で `create_db.py` により空DBを作って実行する（リポジトリ内に `data/` を作らない・commitしない）
5. `git diff --check` → commit → `git push -u origin feature/conversation-v0.1`
6. cloud-unverified の check は docs（changelog 等）に明記し、ローカルで実行する

## ローカルPCへの取り込み

```powershell
git fetch origin
git switch feature/conversation-v0.1
git pull --ff-only origin feature/conversation-v0.1
```
