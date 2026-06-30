# Check Workflow

## 目的

このドキュメントは、PersonalAIのVer1.x開発で、どのcheckをいつ実行するかを整理するための運用メモである。

Ver1.xでは、毎回すべてのcheckを思い出して手動実行するのではなく、変更の大きさに応じて quick check / standard check / full pre-release check を使い分ける。

## quick check

quick check は、小さな変更後に短時間で最低限の確認をしたいときに使う。

例:

```powershell
venv\Scripts\python.exe -B scripts\check_ver120.py
venv\Scripts\python.exe -B scripts\check_ver110.py
venv\Scripts\python.exe -B -c "from core.personal_ai import PersonalAI; print('PersonalAI import OK')"
```

確認すること:

- 最新version固有のcheckが通る
- Ver1.xで追加した重要機能が壊れていない
- PersonalAIのimportができる

## standard check

standard check は、Ver1.xの通常commit前に使う基本確認である。

Ver1.xの基本確認には `scripts/run_ver1_checks.py` を使う。

```powershell
venv\Scripts\python.exe -B scripts\run_ver1_checks.py
```

`run_ver1_checks.py` は、Ver1.xでよく使うcheckをまとめて実行する。

主な対象:

- `scripts/check_ver120.py`
- `scripts/check_ver110.py`
- `scripts/check_v1_final_preparation.py`
- `scripts/check_ver031.py`
- `scripts/run_pre_v1_checks.py`

## full pre-release check

full pre-release check は、大きな区切りやRelease前に使う。

Release前や大きな変更では、`run_ver1_checks.py` に加えて、必要に応じて以下も確認する。

```powershell
venv\Scripts\python.exe -B scripts\run_pre_v1_checks.py
venv\Scripts\python.exe -B scripts\benchmark_lightweight.py
"exit" | venv\Scripts\python.exe -B app.py
git diff --check
git status
```

`run_pre_v1_checks.py` はVer1.0前に整備した一括checkであり、DBテスト書き込みを含む既存機能確認にも使う。
環境によってSQLiteの `disk I/O error` が出る場合は、Codexサンドボックス由来かどうかを確認し、必要なら権限付きで再実行する。

## Ver1.xのcheck番号方針

Ver1.1以降のcheck番号は、Ver0.xと混同しないように以下の形式にする。

```text
Ver1.1 -> scripts/check_ver110.py
Ver1.2 -> scripts/check_ver120.py
Ver1.3 -> scripts/check_ver130.py
```

各version固有のcheckは、作業内容に合わせて追加する。
たとえば、Ver1.1では `check_ver110.py` でMemory利用方針を確認し、Ver1.2では `check_ver120.py` でVer1.xチェック運用を確認する。

## 運用方針

- 小さな変更後は quick check を使う
- 通常のcommit前は standard check を使う
- 大きな区切りやRelease前は full pre-release check を使う
- checkはDB削除、Memory物理削除、既存Memory削除を行わない方針にする
- Git commit / push はユーザー確認後に行う
