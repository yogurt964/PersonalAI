# Project Handoff

## プロジェクト概要

```text
プロジェクト名: PersonalAI
ローカルパス: C:\AIProject\PersonalAI
GitHub: https://github.com/yogurt964/PersonalAI.git
現在バージョン: Ver2.19
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

## Permission / 開発自走方針

Ver2.14以降、後から修正できる通常作業はユーザー確認なしで進める。

確認不要:

- コード修正
- 機能追加
- 軽いリファクタリング
- テスト追加
- docs更新
- ファイル編集
- git add
- git commit
- git push
- branch作成
- 通常merge
- 修正用commit

確認が必要:

- force push
- reset --hard
- rebase
- Git履歴の書き換え
- 作業内容の消失につながる操作
- DB削除
- DB初期化
- DBスキーマの破壊的変更
- Memory物理削除
- 大量ファイル削除
- APIキー、個人情報、機密情報の外部送信
- 課金、契約、購入
- PermissionManagerや安全チェックを弱める変更
- 後から戻すのが難しい仕様変更

ユーザーにはコード差分の細部ではなく、実際の動作結果、AIの返答の自然さ、使いやすさ、ポートフォリオとして見せられるかを確認してもらう。

## 現在の実装済み機能

Ver2.19時点では、以下が実装済みである。

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
Ver1.0 Final Preparation: Ver1.0最終GO判定とリリース準備
Ver1.1: Memory利用バランス調整
Ver1.2: Ver1.x用チェック運用整理
Ver1.3: 会話品質改善
Ver1.4: Reader追加前のTool / Adapter受け口整理
Ver1.5: PermissionManagerとTool実行前確認の接続準備
Ver1.6: Reader実装前のInputAnalyzer / Capability / Tool連携確認
Ver1.7: Tool実行ログと結果記録の設計
Ver1.8: Reader実装前の手動テストケース整理
Ver1.9: Ver2.0 Reader実装計画
Ver1.10: Ver1.x総仕上げ確認
Ver2.0: Web Reader最小実用版
Ver2.1: Web Reader手動実行テストと会話UI接続方針整理
Ver2.2: URL入力検出から確認メッセージ生成までのdry-run
Ver2.3: URL確認メッセージを会話UIに表示するdry-run接続
Ver2.4: Web Reader確認応答の前段処理とToolRequest候補作成dry-run
Ver2.5: user_confirmed=True後にToolRunner経由でWeb Readerを実行
Ver2.6: Web Reader実Web手動テスト結果整理
Ver2.7: 完成形ビジョンと自律・記憶・モデル選定方針整理
Ver2.8: Web Reader結果の会話品質改善
Ver2.9: Reader結果のMemory保存方針設計
Ver2.10: Memory Candidate生成のdry-run設計
Ver2.11: Memory CandidateをWeb Reader結果にdry-run接続
Ver2.12: Memory Candidate確認UI方針
Ver2.13: Memory Candidate確認応答のdry-run
Ver2.14: 開発自走方針
Ver2.15: ポートフォリオREADMEとデモログ整備
Ver2.16: Memory Candidate編集dry-run
Ver2.17: Memory Candidateのユーザー確認つき保存
Ver2.18: Memory保存後の確認・表示フロー
Ver2.19: 確認待ち状態の文脈解釈
```

## 現在の主要ファイル

```text
AGENTS.md: AIエージェントが最初に読む短い開発運用ルール
README.md: 就活ポートフォリオ向けのプロジェクト概要
app.py: CLI起動入口
core/personal_ai.py: PersonalAI本体
core/input_analyzer.py: 入力分類
core/capability_manager.py: Capability判定
core/planner.py: 行動計画
core/router.py: 実行先選択
core/executor.py: 実行・未実装応答
core/permission_manager.py: Permission / Risk判断
core/tool_adapter.py: Tool / Adapter共通データ構造
core/tool_registry.py: Tool / Adapter登録管理
core/tool_permission.py: ToolRequest単位の実行前Permission判定
core/tool_request_builder.py: 入力からToolRequestを作るdry-run判定
core/tool_flow.py: ToolRequest / Registry / Permissionのdry-runプレビュー
core/tool_execution_log.py: Tool実行ログと結果記録のインメモリ基礎
core/tool_runner.py: Permission確認後にToolRequestを実行する入口
core/web_reader_adapter.py: Web Reader最小実用版
core/confirmation_intent.py: 確認待ち状態の入力を確認Intentとして解釈するルールベースresolver
core/web_reader_confirmation.py: URL入力からWeb Reader確認メッセージと確認応答dry-run結果を作る
core/memory_candidate.py: Reader結果からMemory Candidateを作るdry-run
core/memory_candidate_confirmation.py: Memory Candidate確認応答と編集応答をdry-runで解釈
core/memory_candidate_saver.py: Memory Candidateを既存の長期記憶保存機構へ渡す保存処理
core/personal_ai.py: URL確認、確認応答、ToolRunner経由Web Reader実行、Memory Candidate dry-run、pending_memory_candidate_edit、last_memory_candidate_save_result、last_saved_memory_candidate_result、確認待ち状態の文脈解釈を接続
ai/llm.py: Qwen呼び出しとSYSTEM_PROMPT
ai/memory_extract.py: 汎用記憶抽出
ai/memory_context.py: MemoryContext生成
ai/memory_usage_policy.py: Memory利用方針判定
ai/conversation_quality_policy.py: 会話品質方針判定
ai/memory_forgetting.py: 自動忘却dry-run候補判定
ai/preference_memory.py: Preference記憶抽出・保存
ai/preference_confirmation.py: Preference確認質問判定
scripts/benchmark_lightweight.py: 軽量性ベンチマーク
docs/future_app_integrations.md: 将来アプリ・ツール連携方針
docs/version_1_0_manual_test.md: Ver1.0前の手動テスト表
docs/version_1_0_final_check.md: Ver1.0前の総合チェック手順
docs/version_1_0_release_decision.md: Ver1.0へ進めるGO / HOLD / NO-GO判定
docs/version_policy.md: 長期開発のバージョン管理方針
docs/check_workflow.md: Ver1.xチェック運用方針
docs/conversation_quality.md: 会話品質方針
docs/tool_adapter_design.md: Tool / Adapter設計方針
docs/tool_permission_design.md: Tool Permission設計方針
docs/tool_input_integration.md: InputAnalyzer / Capability / Tool連携方針
docs/tool_execution_log_design.md: Tool実行ログ設計方針
docs/reader_pre_implementation_test_cases.md: Reader実装前の手動テストケース
docs/reader_implementation_plan_v2.md: Ver2.0 Reader実装計画
docs/ver1_x_final_review.md: Ver1.x総仕上げ確認
docs/web_reader_design.md: Web Reader設計方針
docs/web_reader_manual_test.md: Web Reader手動実行テスト手順
docs/web_reader_ui_connection_plan.md: Web Reader会話UI接続方針
docs/final_product_vision.md: 完成形ビジョン、高自律、記憶、ModelRouter / ToolRouter、自律調査、自己アップデート方針
docs/conversation_policy.md: 会話品質・返答方針
docs/reader_memory_policy.md: Reader結果のMemory保存方針
docs/memory_candidate_ui_policy.md: Memory Candidate確認UI方針
docs/development_workflow.md: 開発自走方針とユーザー確認の線引き
docs/portfolio_notes.md: 就活・面接で説明するための補助メモ
docs/demo_logs/web_reader_memory_candidate_demo.md: Web ReaderからMemory Candidate確認応答までのデモログ
scripts/run_pre_v1_checks.py: Ver1.0前の自動チェックまとめ実行
scripts/run_ver1_checks.py: Ver1.x用の標準チェックまとめ実行
scripts/run_ver2_checks.py: Ver2.x用の標準チェックまとめ実行
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
scripts/check_v1_final_preparation.py
scripts/check_ver110.py
scripts/check_ver120.py
scripts/check_ver130.py
scripts/check_ver140.py
scripts/check_ver150.py
scripts/check_ver160.py
scripts/check_ver170.py
scripts/check_ver180.py
scripts/check_ver190.py
scripts/check_ver1100.py
scripts/check_ver200.py
scripts/check_ver210.py
scripts/check_ver220.py
scripts/check_ver230.py
scripts/check_ver240.py
scripts/check_ver250.py
scripts/check_ver260.py
scripts/check_ver270.py
scripts/check_ver280.py
scripts/check_ver290.py
scripts/check_ver2100.py
scripts/check_ver2110.py
scripts/check_ver2120.py
scripts/check_ver2130.py
scripts/check_ver2140.py
scripts/check_ver2150.py
scripts/check_ver2160.py
scripts/check_ver2170.py
scripts/check_ver2180.py
scripts/check_ver2190.py
scripts/run_ver1_checks.py
scripts/run_ver2_checks.py
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

現在状態:

```text
Ver2.0.0でWeb Reader最小実用版に到達
v2.0.0 タグ作成済み
GitHub Release PersonalAI Version 2.0.0 作成済み
Ver2.1でWeb Reader手動実行テストと会話UI接続方針を整理済み
Ver2.2でURL入力検出から確認メッセージ生成までのdry-runを追加
Ver2.3でURL確認メッセージを会話返答として表示するdry-run接続を追加
Ver2.4で確認応答の前段処理とToolRequest候補作成dry-runを追加
Ver2.5でuser_confirmed=True後にToolRunner経由でWeb Readerを実行する接続を追加
Ver2.6で https://example.com の実Web手動テスト結果をdocsへ整理
実Web手動確認では Example Domain と text_preview が返った
Ver2.7で完成形ビジョンをdocs化
高自律・記憶・ModelRouter/ToolRouter・自己アップデート・自律調査方針を整理
会話品質・返答方針を整理
Ver2.8でWeb Reader結果の会話品質を改善
成功時の返答を見やすくした
失敗時に読めたふりをしない方針を維持
Ver2.9でReader結果のMemory保存方針をdocs化
Memory Candidate生成やユーザー確認つき保存へ進める土台を整理
Ver2.9時点ではMemory保存の本実装はまだしていない
Ver2.10でMemory Candidate生成のdry-runを追加
Reader結果から保存候補を作る土台を追加
Ver2.11でMemory CandidateをWeb Reader結果にdry-run接続
Web Reader成功時に保存候補を作る
失敗時・未実行時はMemory Candidateを作らない
Memory CandidateもDB保存しない
Ver2.12でMemory Candidate確認UI方針をdocs化
保存前にユーザーが確認できる形を整理
保存 / 保存しない / 編集 / 後で確認 の選択肢を整理
高リスク候補は自動保存しない
Memory CandidateのDB保存もしない
Ver2.13でMemory Candidate確認応答のdry-runを追加
保存する / 保存しない / 編集して保存 / 後で確認 の応答を解釈
「保存する」と言われてもdry-runで止める
まだMemory保存はしない
Ver2.14で開発自走方針をリポジトリに反映
AGENTS.md と docs/development_workflow.md を追加
通常の後から修正できる操作はユーザー確認なしで進める方針に変更
commit / push は通常確認不要
不可逆操作、DB削除、Memory物理削除、課金、外部送信は確認必須
Ver2.15でREADME.mdをポートフォリオ向けに整理
docs/portfolio_notes.md を追加
docs/demo_logs/web_reader_memory_candidate_demo.md を追加
Web ReaderからMemory Candidate確認応答dry-runまでのデモを説明可能にした
Ver2.16でMemory Candidate編集dry-runを追加
`編集して保存` の後に編集内容を受け取り、編集済み候補としてdry-run保持できる
pending_memory_candidate_edit で編集待ち状態を管理
ただし、まだMemory保存はしない
DBスキーマ変更もしない
Ver2.17でMemory Candidateのユーザー確認つき保存を追加
ユーザーが明示的に `保存する` と答えた低リスク候補だけ、既存の長期記憶保存機構へ渡す
core/memory_candidate_saver.py で保存用テキストへ変換する
last_memory_candidate_save_result に保存結果を保持する
自動チェックでは実DB保存しない
高リスク候補は保存しない
Ver2.18でMemory保存後の確認・表示フローを追加
保存成功後に保存内容プレビューを表示する
last_saved_memory_candidate_result に直近保存結果を保持する
`今保存した記憶を確認して` で直近保存したMemoryを表示できる
DBスキーマ変更はしない
Ver2.19で確認待ち状態の文脈解釈を改善
core/confirmation_intent.py で confirmation intent を分離
Web Reader確認待ち中は `いいよ` や `お願いします` を許可、`キャンセル` を拒否として扱う
確認待ち中に不明な入力が来た場合は通常会話へ流さず確認を聞き直す
Web Reader未対応という誤解を避ける
LLMによるIntent判定はまだ未実装
ただしPDF/Image/YouTube/File Readerはまだ未実装
自動checkでは実Webアクセスしない
URL検出だけでは自動Webアクセスしない
保留中の確認に対する肯定応答がある場合だけWeb Readerを実行する
user_confirmed=Falseでは実行しない
Reader結果全文のDB保存はまだしない
実Webアクセスはユーザー確認つきの手動確認で行う
```

Ver2.19後の候補:

```text
Ver2.20: Memory検索の最小実用化
Ver2.20: MIGRATION.md作成
Ver2.x: READMEへの画像・GIF・図の追加
Ver2.x: File / PDF Reader
Ver2.x: LLM Intent Resolver設計
```

## Ver1.1以降の改善候補

```text
Memory利用方針 minimal / normal / detailed の判定語彙を増やす
通常会話でのMemory利用が自然か実会話で継続確認する
会話品質を改善する
Reader / Tool / Adapter追加前の受け口を整理する
```

## Ver1.0.0リリース済みメモ

```text
Ver1.0.0はGitHub Releaseまで完了済み。
Ver1.0.0は完成版ではなく、最低限の会話・記憶・安全確認・未実装機能の正直な扱いをテストできる実用テスト版である。
Ver1.0 Final Preparationでは、git tag v1.0.0 作成、tag push、GitHub Release作成へ進む準備を整理した。
```

## ChatGPT再開用プロンプト

```text
PersonalAIプロジェクトを再開します。
まず AGENTS.md、docs/development_workflow.md、docs/project_handoff.md、docs/recovery_guide.md、docs/core_principles.md、docs/changelog.md、docs/version_1_0_test_plan.md、docs/version_1_0_manual_test.md、docs/version_1_0_final_check.md、docs/version_1_0_release_decision.md、docs/version_policy.md を確認してください。
現在の状態を要約し、後から修正できる通常作業は自走し、不可逆操作や危険操作だけ確認してください。
```

## Codex再開用プロンプト

```text
PersonalAIプロジェクトを再開します。
まず AGENTS.md、docs/development_workflow.md、docs/project_handoff.md、docs/recovery_guide.md、docs/core_principles.md、docs/changelog.md、docs/version_1_0_release_decision.md、docs/version_policy.md を読んでください。
現在のバージョン、実装済み機能、未実装機能、次の作業候補を把握してください。
Ver2.14以降は、後から修正できる通常作業は自走して進めてください。
不可逆操作、DB削除、Memory物理削除、課金、外部送信、Git履歴書き換えはユーザー確認してください。
```
