# Project Handoff

## プロジェクト概要

```text
プロジェクト名: PersonalAI
ローカルパス: C:\AIProject\PersonalAI
GitHub: https://github.com/yogurt964/PersonalAI.git
現在バージョン: Ver0.31
開発環境: Windows / VS Code / PowerShell / Python venv / Git / GitHub / Codex / Ollama Qwen
```

このファイルは、ChatGPT、Codex、VS Codeなどの会話履歴や作業文脈が消えても、PersonalAIプロジェクトを再開できるようにするための引き継ぎ書である。

## PersonalAIの最終目標

PersonalAIの最終目標は、ユーザーがChatGPT、Codex、VS Code、PowerShell、ブラウザ、Word、Excel、PDFツールなどを直接触らなくても、PersonalAIを入口にしてほぼすべての作業をできるようにすることである。

限界はあるが、最終的には「このAI以外を直接触らなくても問題ない」状態を目指す。

PersonalAIは単なるチャットボットではなく、ユーザーの作業入口、記憶、判断、実行、安全確認を統括するシステムとして育てる。

## 最重要品質

完成形で最も重視するのは、ユーザーが本当に回答してほしいことに正確に答えられる精度である。

単に機能が多いことより、ユーザーの意図を理解し、必要な情報を確認し、未実装機能や不確かな内容をできたふりせず、求められている回答に到達することを優先する。

## 開発で重視すること

- 後から変更しやすいこと
- 壊れにくいこと
- 変な操作をしても破綻しにくいこと
- 小さく実装すること
- checkスクリプトを作ること
- docsを更新すること
- 既存機能を壊さないこと
- Gitでこまめにcommit / pushすること

## Permission方針

ユーザーに影響する操作は必ず許可を取る。

対象例:

- ファイル作成
- ファイル編集
- ファイル削除
- 外部送信
- Git commit / push
- PC操作
- Webアクセス
- 個人情報処理
- 外部API利用

将来的には、以下のような柔軟な許可を扱いたい。

- 今回だけ許可
- この種類の操作は今後も許可
- このプロジェクト内だけ許可
- このフォルダ内だけ許可
- 危険度が高い操作は毎回確認

## 現在の実装済み機能

Ver0.31時点では、以下が実装済みである。

```text
Ver0.9.1: 状態整理・安定化
Ver0.9.2: vision整理
Ver0.10: InputAnalyzer結果をPlanner / Router / Executorへ反映
Ver0.11: Clarification基礎
Ver0.12: Permission / Risk基礎
Ver0.13: Memory設計強化
Ver0.14: MemoryContext強化
Ver0.15: MemoryContextプレビュー
Ver0.16: Memory一覧表示
Ver0.17: Memory手動無効化・復元
Ver0.18: 無効化MemoryのContext反映確認、Ver1.0テスト計画
Ver0.19: Preference記憶
Ver0.20: Preference確認質問
Ver0.21: Project Handoff / Recovery / Core Principles
Ver0.22: 確認回答後にPreference保存を続行する仕組み
Ver0.23: Capability判定強化
Ver0.24: 自動忘却dry-run
Ver0.25: 軽量性ベンチマーク
Ver0.26: Future App Integrations / Ver1.0手動テスト表
Ver0.27: Ver1.0前の総合チェック手順
Ver0.28: Ver1.0リリース判定
Ver0.29: バージョン管理方針
Ver0.30: Ver1.0直前の手動テスト実測更新
Ver0.31: Ver1.0直前 GO / HOLD / NO-GO 最終確認
```

## 現在の主要ファイル

```text
app.py: CLI起動入口
core/personal_ai.py: PersonalAI本体
core/input_analyzer.py: 入力分類
core/capability_manager.py: Capability判定
core/planner.py: 行動計画
core/router.py: 実行先選択
core/executor.py: 実行・未実装応答
core/permission_manager.py: Permission / Risk判断
ai/llm.py: Qwen呼び出しとSYSTEM_PROMPT
ai/memory_extract.py: 汎用記憶抽出
ai/memory_context.py: MemoryContext生成
ai/memory_forgetting.py: 自動忘却dry-run候補判定
ai/preference_memory.py: Preference記憶抽出・保存
ai/preference_confirmation.py: Preference確認質問判定
scripts/benchmark_lightweight.py: 軽量性ベンチマーク
docs/future_app_integrations.md: 将来アプリ・ツール連携方針
docs/version_1_0_manual_test.md: Ver1.0前の手動テスト表
docs/version_1_0_final_check.md: Ver1.0前の総合チェック手順
docs/version_1_0_release_decision.md: Ver1.0へ進めるGO / HOLD / NO-GO判定
docs/version_policy.md: 長期開発のバージョン管理方針
scripts/run_pre_v1_checks.py: Ver1.0前の自動チェックまとめ実行
database/models.py: DBモデル
database/memory_manager.py: Memory保存・取得・状態変更
database/chat_history.py: 会話履歴保存・取得
```

## 現在の確認スクリプト

```text
scripts/check_ver011.py
scripts/check_ver012.py
scripts/check_ver013.py
scripts/check_ver014.py
scripts/check_ver015.py
scripts/check_ver016.py
scripts/check_ver017.py
scripts/check_ver018.py
scripts/check_ver019.py
scripts/check_ver020.py
scripts/check_ver021.py
scripts/check_ver022.py
scripts/check_ver023.py
scripts/check_ver024.py
scripts/check_ver025.py
scripts/check_ver026.py
scripts/check_ver027.py
scripts/check_ver028.py
scripts/check_ver029.py
scripts/check_ver030.py
scripts/check_ver031.py
```

注意:

- `check_ver013.py`、`check_ver017.py`、`check_ver018.py`、`check_ver019.py`、`check_ver022.py` などはDBテスト書き込み・削除を含む
- テストデータは `verxxx_test` のようなsource / tags / memory_keyに限定して削除する
- ユーザーの既存記憶を削除しない設計にする
- CodexのサンドボックスではSQLite書き込みが `disk I/O error` になる場合があり、その場合は権限付き実行が必要

## 未実装機能

```text
OpenAI接続
Claude / Gemini接続
Webページ実読み取り
YouTube実要約
PDF読み取り
画像読み取り
Word / Excel / PDF作成
PC画面読み取り
PC操作
自動忘却の実行
ベクトルDB
Embedding検索
Knowledge DB本格実装
GUI
```

## 次にやること

Ver0.31後の候補:

```text
Ver1.0直前: Ver0.31をcommit / pushしてGit状態をcleanにする
Ver1.0: 最低限の会話・記憶・安全確認をテストできる実用テスト版
Ver1.1以降: Memory利用バランス調整
Ver1.1以降: Reader / Tool / Adapter追加
```

## Ver1.1以降の改善候補

```text
通常会話でMemory情報を使いすぎないようにする
ユーザーが明示的に記憶参照を求めたときだけ詳しくMemoryを使う
何気ない会話では、関連が強いMemoryだけ使う
Preference情報を毎回話題に出しすぎない
```

## ChatGPT再開用プロンプト

```text
PersonalAIプロジェクトを再開します。
まず docs/project_handoff.md、docs/recovery_guide.md、docs/core_principles.md、docs/changelog.md、docs/version_1_0_test_plan.md、docs/version_1_0_manual_test.md、docs/version_1_0_final_check.md、docs/version_1_0_release_decision.md、docs/version_policy.md を確認してください。
現在の状態を要約し、勝手に実装せず、次にやるべき作業案を出してください。
```

## Codex再開用プロンプト

```text
PersonalAIプロジェクトを再開します。
まず docs/project_handoff.md、docs/recovery_guide.md、docs/core_principles.md、docs/changelog.md、docs/version_1_0_release_decision.md、docs/version_policy.md を読んでください。
現在のバージョン、実装済み機能、未実装機能、次の作業候補を把握してください。
勝手に大きな変更をせず、変更前に作業計画を出してください。
```
