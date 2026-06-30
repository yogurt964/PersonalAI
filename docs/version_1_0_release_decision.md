# Ver1.0 Release Decision

## 目的

このドキュメントは、PersonalAIをVer1.0へ進めるかどうかを判定するための基準をまとめたものである。

Ver1.0は完成版ではなく、最低限の会話・記憶・安全確認・未実装機能の正直な扱いをテストできる実用テスト版である。

今回は、Ver1.0タグ作成、GitHub Release作成、正式なVer1.0化は行わない。
Ver1.0へ進める条件、保留すべき条件、進めてはいけない条件を分けて確認できるようにする。

## Ver1.0の位置づけ

Ver1.0はPersonalAIの完成版ではない。

Ver1.0は、以下を満たす最初の実用テスト版である。

- 通常会話ができる
- 記憶保存・記憶参照の基礎がある
- Preference記憶を扱える
- 曖昧なPreferenceでは確認質問できる
- 確認回答後に保存を続行できる
- 未実装機能をできたふりしない
- Permission / Capability の基礎がある
- Memoryを物理削除せず安全に扱う
- 引き継ぎ・復旧docsがある
- checkスクリプトで最低限の安定性を確認できる

Ver1.0で大事なのは、すべての機能を完成させることではない。
今ある会話、Memory、Preference、安全確認、未実装説明が壊れていないことを確認し、次の拡張に進める状態にすることである。

## GO条件

以下を満たす場合、Ver1.0へ進めてよい候補とする。

- git status が clean
- PersonalAI import が成功
- app.py が起動し、exitで正常終了する
- scripts/run_pre_v1_checks.py が成功
- scripts/check_ver030.py が成功
- scripts/check_ver029.py が成功
- scripts/check_ver028.py が成功
- 軽量性ベンチマークが極端に遅くない
- docs/version_1_0_manual_test.md の重要項目が OK
- URL / YouTube / PDF / 画像 / PC操作などを読んだふり・実行したふりしない
- Preferenceのlike / not_like / dislike が扱える
- 一番好きなどの曖昧なPreferenceで確認質問できる
- 確認回答後に保存できる
- 忘却dry-runが候補提案のみで、削除や自動無効化をしない
- project_handoff / recovery_guide / core_principles / version_policy が最新

GOは「完全に完成した」という意味ではない。
Ver1.0の目的に対して、最低限の実用テストに進める状態という意味である。

## HOLD条件

以下がある場合、Ver1.0は一時保留にする。
原因と影響範囲を整理し、必要な修正を行ってから再判定する。

- checkの一部が失敗している
- app.pyが起動しない
- importに失敗する
- Preference記憶が壊れている
- 未実装機能をできたふりしている
- MemoryContextに inactive memory が入ってしまう
- 忘却dry-runがDBを書き換えている
- 手動テストの重要項目が未実施または保留
- docs/project_handoff.md が古い
- git working tree が clean ではない

HOLDは「進めてはいけない」ではなく、判断材料が足りない、または軽微から中程度の修正が必要な状態である。

## NO-GO条件

以下がある場合、Ver1.0へ進めてはいけない。
安全性や信頼性に関わるため、先に必ず修正する。

- ユーザーの既存Memoryを勝手に削除する
- 自動で is_active=False にする
- data/personal_ai.db を削除または破壊する
- ファイル削除や外部送信を無許可で行う
- Git commit / push を無許可で行う
- Web / PDF / 画像 / YouTubeを読んだふりする
- app.pyが正常終了できない
- checkスクリプトが広範囲に失敗する

NO-GOは、Ver1.0の目的である「安全に実用テストできる状態」を満たしていない状態である。

## Ver1.0後に回す作業

以下はVer1.0後の候補として扱う。
Ver1.0前に無理に入れず、Ver1.0の安定確認後に順番を決める。

- OpenAI接続
- Web Reader
- PDF Reader
- Image Reader
- YouTube Reader
- Word / Excel / PDF作成
- PC操作
- VS Code / PowerShell / Git操作の統合
- GUI
- Vector DB / Embedding検索
- 高度な自動忘却
- Tool / Adapter実装
- 画像生成 / 動画生成 / 制作アプリ連携
- 予定管理 / ファイル整理などの日常統合

## Ver1.0直前の推奨手順

Ver1.0へ進める直前は、以下の順番で確認する。

```powershell
git status
venv\Scripts\python.exe -B scripts\check_ver030.py
venv\Scripts\python.exe -B scripts\check_ver029.py
venv\Scripts\python.exe -B scripts\check_ver028.py
venv\Scripts\python.exe -B scripts\run_pre_v1_checks.py
venv\Scripts\python.exe -B scripts\benchmark_lightweight.py
venv\Scripts\python.exe -B -c "from core.personal_ai import PersonalAI; print('PersonalAI import OK')"
"exit" | venv\Scripts\python.exe -B app.py
git diff --check
git status
```

その後、`docs/version_1_0_manual_test.md` の結果欄を確認する。
Ver1.0判定前には、`docs/version_policy.md` も確認し、Ver1.0が整数バージョンとして「実用的に使える区切り」になっているか確認する。
重要項目が `未実施` や `保留` のままなら、Ver1.0へ進める前に内容と影響を整理する。

## 判定の考え方

判定は以下の3つに分ける。

- GO: Ver1.0へ進める
- HOLD: 保留して追加確認または軽微な修正を行う
- NO-GO: 安全性や基本動作に問題があり、進めてはいけない

迷う場合はHOLDにする。
PersonalAIでは、速度よりも精度と安全性を優先するためである。

## Ver1.0リリース判定欄

| 項目 | 判定 |
|---|---|
| 自動check | OK |
| benchmark | OK |
| 手動テスト | 保留 |
| 未実装機能の扱い | OK |
| Memory安全性 | OK |
| docs最新性 | OK |
| Git状態 | 保留 |
| 総合判定 | HOLD |

総合判定は GO / HOLD / NO-GO のいずれかにする。

Ver0.30実測メモ:

- `scripts/check_ver030.py`、`scripts/check_ver029.py`、`scripts/check_ver028.py` は成功
- `scripts/run_pre_v1_checks.py` は通常実行でCodexサンドボックス由来のSQLite `disk I/O error` が発生したが、権限付き再実行で成功
- `scripts/benchmark_lightweight.py` は total_benchmark_time 0.634 sec で成功
- `PersonalAI import` と `app.py` のexit確認は成功
- 手動テスト表では、実会話の詳細品質確認が未再確認の項目を `保留` とした
- Ver0.30変更が未コミットの間はGit状態を `保留` とする
