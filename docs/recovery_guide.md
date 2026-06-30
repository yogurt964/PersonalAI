# Recovery Guide

## 目的

このファイルは、PC、VS Code、ChatGPT、Codexの履歴や作業文脈が消えた場合に、PersonalAIプロジェクトを再開するための手順書である。

## VS Codeで開く

```powershell
cd C:\AIProject\PersonalAI
code .
```

`code` コマンドが使えない場合は、VS Codeから `C:\AIProject\PersonalAI` フォルダを開く。

## venv有効化

```powershell
.\venv\Scripts\Activate.ps1
```

うまくいかない場合は、PowerShellの実行ポリシーに注意する。
一時的にvenvを有効化せず、以下のように直接 `venv\Scripts\python.exe` を使ってもよい。

```powershell
venv\Scripts\python.exe --version
```

## Python確認

```powershell
venv\Scripts\python.exe --version
```

## PersonalAI import確認

```powershell
venv\Scripts\python.exe -B -c "from core.personal_ai import PersonalAI; print('PersonalAI import OK')"
```

期待:

```text
PersonalAI import OK
```

## app.py起動確認

```powershell
"exit" | venv\Scripts\python.exe -B app.py
```

PowerShell上では日本語プロンプトが文字化けする場合がある。
正常終了していれば、まずは起動確認として扱ってよい。

## checkスクリプト確認

最低限:

```powershell
venv\Scripts\python.exe -B scripts\check_ver020.py
venv\Scripts\python.exe -B scripts\check_ver019.py
venv\Scripts\python.exe -B scripts\check_ver018.py
```

余裕があれば:

```powershell
venv\Scripts\python.exe -B scripts\check_ver017.py
venv\Scripts\python.exe -B scripts\check_ver016.py
venv\Scripts\python.exe -B scripts\check_ver015.py
venv\Scripts\python.exe -B scripts\check_ver014.py
venv\Scripts\python.exe -B scripts\check_ver013.py
venv\Scripts\python.exe -B scripts\check_ver012.py
venv\Scripts\python.exe -B scripts\check_ver011.py
```

注意:

- `check_ver013.py`、`check_ver017.py`、`check_ver018.py`、`check_ver019.py` はDBテスト書き込み・削除を含む
- CodexのサンドボックスではSQLite書き込み時に `disk I/O error` になる場合がある
- その場合は権限付きで実行する

## Git確認

```powershell
git status
git log --oneline -5
```

作業前に、未commitの変更があるか必ず確認する。
未commitの変更がある場合は、勝手に戻さない。

## GitHubから復旧する場合

```powershell
git clone https://github.com/yogurt964/PersonalAI.git
cd PersonalAI
```

venvはGit管理されていない可能性があるため、再作成が必要になる可能性がある。
必要な依存関係が不明な場合は、既存環境、README、docs、過去のchangelogを確認する。

## DBについて

```text
data/personal_ai.db はローカルDB。
Git管理外の可能性が高い。
DBを削除すると記憶が消える。
DBを直接編集しない。
```

Memoryの確認には以下を使う。

```powershell
venv\Scripts\python.exe -B scripts\list_memories.py --include-inactive --limit 20
venv\Scripts\python.exe -B scripts\show_memory_context.py --limit 20
```

Memoryの無効化・復元には以下を使う。

```powershell
venv\Scripts\python.exe -B scripts\manage_memory_status.py --id 1 --deactivate
venv\Scripts\python.exe -B scripts\manage_memory_status.py --id 1 --deactivate --apply
venv\Scripts\python.exe -B scripts\manage_memory_status.py --id 1 --restore
venv\Scripts\python.exe -B scripts\manage_memory_status.py --id 1 --restore --apply
```

`--apply` がない場合はdry-runであり、DBは変更されない。

## よくある注意

```text
PowerShellで日本語が文字化けする場合がある。
LF/CRLF warningは基本的に問題ない。
__pycache__ はGit管理しない。
data/personal_ai.db は不用意にcommitしない。
check_ver013.py など一部スクリプトはDBテスト書き込み・削除を含む。
```

## 再開時に読むdocs

まず以下を読む。

```text
docs/project_handoff.md
docs/recovery_guide.md
docs/core_principles.md
docs/changelog.md
docs/version_1_0_test_plan.md
```

Memory周辺を触る場合は、以下も読む。

```text
docs/memory.md
docs/preference_memory.md
docs/preference_confirmation.md
```
