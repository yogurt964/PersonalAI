# Ver1.0 Final Check

## 目的

このドキュメントは、PersonalAIをVer1.0へ進める前に、自動チェック・ベンチマーク・手動テスト・Git状態確認を行うための総合チェック手順である。

Ver1.0は完成版ではない。
最低限の会話、記憶、安全確認、未実装機能の正直な扱いを、実用に近い形で確認できる版として扱う。

## チェック全体の順番

1. Git状態確認
2. import確認
3. app.py起動確認
4. Ver0.11〜Ver0.28の自動check実行
5. 軽量性ベンチマーク実行
6. Ver1.0手動テスト表に沿った確認
7. 未実装機能の扱い確認
8. Memory / Preference / Forgetting の安全確認
9. project_handoff / recovery_guide の確認
10. Ver1.0リリース判定基準の確認
11. Ver1.0へ進めるかの判定

## 1. Git状態確認

```powershell
git status
git log --oneline -10
```

期待結果:

```text
working tree clean であること
最新コミットがVer0.28の作業を含んでいること
```

## 2. import確認

```powershell
venv\Scripts\python.exe -B -c "from core.personal_ai import PersonalAI; print('PersonalAI import OK')"
```

期待結果:

```text
PersonalAI import OK
```

## 3. app.py起動確認

```powershell
"exit" | venv\Scripts\python.exe -B app.py
```

期待結果:

```text
終了コード0
```

PowerShell上で日本語が文字化けする可能性はある。
ただし、終了コード0なら起動確認としてはOKとする。

## 4. 自動check実行

```powershell
venv\Scripts\python.exe -B scripts\check_ver028.py
venv\Scripts\python.exe -B scripts\check_ver027.py
venv\Scripts\python.exe -B scripts\check_ver011.py
venv\Scripts\python.exe -B scripts\check_ver012.py
venv\Scripts\python.exe -B scripts\check_ver013.py
venv\Scripts\python.exe -B scripts\check_ver014.py
venv\Scripts\python.exe -B scripts\check_ver015.py
venv\Scripts\python.exe -B scripts\check_ver016.py
venv\Scripts\python.exe -B scripts\check_ver017.py
venv\Scripts\python.exe -B scripts\check_ver018.py
venv\Scripts\python.exe -B scripts\check_ver019.py
venv\Scripts\python.exe -B scripts\check_ver020.py
venv\Scripts\python.exe -B scripts\check_ver021.py
venv\Scripts\python.exe -B scripts\check_ver022.py
venv\Scripts\python.exe -B scripts\check_ver023.py
venv\Scripts\python.exe -B scripts\check_ver024.py
venv\Scripts\python.exe -B scripts\check_ver025.py
venv\Scripts\python.exe -B scripts\check_ver026.py
```

注意:

```text
一部のcheckはテスト用Memoryを書き込み、テストデータのみ削除または無効化する。
ユーザーの既存Memoryを削除しない設計であることを確認する。
```

まとめて実行する場合:

```powershell
venv\Scripts\python.exe -B scripts\run_pre_v1_checks.py
```

`run_pre_v1_checks.py` はVer0.11〜Ver0.26と軽量性ベンチマークをまとめて確認する。
Ver0.27とVer0.28のcheckは、上の個別コマンドで確認する。

## 5. 軽量性ベンチマーク

```powershell
venv\Scripts\python.exe -B scripts\benchmark_lightweight.py
```

確認観点:

```text
Qwen / Ollamaへ問い合わせていない
外部通信していない
DBを破壊していない
主要処理時間が表示される
極端に重くなっていない
```

## 6. Ver1.0手動テスト表

`docs/version_1_0_manual_test.md` を使って確認する。

対象:

```text
通常会話
記憶保存
記憶参照
Preference記憶
Preference確認質問
確認回答後の保存
未実装機能の扱い
Capability判定
Permission方針
MemoryContext
忘却dry-run
軽量性ベンチマーク
引き継ぎ・復旧
```

結果欄は `未実施` から `OK / NG / 保留` に更新していく。
NGの場合は、入力例、実際の返答、期待との差分をメモに残す。

## 7. 未実装機能の扱い確認

以下を確認する。

```text
URLを読んだふりをしない
YouTubeを見たふりをしない
PDFを読んだふりをしない
画像を見たふりをしない
PC操作を実行したふりをしない
Word / Excel / PDF作成を実行したふりをしない
高精度が必要な内容で断定しすぎない
```

## 8. Memory / Preference / Forgetting 安全確認

以下を確認する。

```text
is_active=False のMemoryはMemoryContextに入らない
Preferenceのlike / not_like / dislikeが扱える
一番好きなどの曖昧なPreferenceは確認質問になる
確認回答後に保存できる
忘却dry-runは候補提案のみで、削除や自動無効化をしない
```

## 9. 引き継ぎ・復旧確認

以下のdocsを確認する。

```text
docs/project_handoff.md
docs/recovery_guide.md
docs/core_principles.md
docs/changelog.md
docs/version_1_0_test_plan.md
docs/version_1_0_manual_test.md
docs/version_1_0_final_check.md
docs/version_1_0_release_decision.md
```

## 10. Ver1.0リリース判定基準

`docs/version_1_0_release_decision.md` を確認する。

確認対象:

```text
Ver1.0の位置づけ
GO条件
HOLD条件
NO-GO条件
Ver1.0後に回す作業
Ver1.0直前の推奨手順
判定欄
```

## 11. Ver1.0へ進める判定基準

以下を満たす場合、Ver1.0へ進める候補とする。

```text
Ver0.11〜Ver0.28のcheckが成功している
app.pyが起動できる
PersonalAI importが成功する
軽量性ベンチマークが極端に遅くない
手動テストの重要項目がOKである
未実装機能をできたふりしない
MemoryやPreferenceが破壊的に動いていない
project_handoff / recovery_guide が最新である
Git working tree が clean である
```

Ver1.0へ進める前に、NGや保留の項目がある場合は、内容と影響範囲を整理する。
最終判断は `docs/version_1_0_release_decision.md` の GO / HOLD / NO-GO に沿って行う。
