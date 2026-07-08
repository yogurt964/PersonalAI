# Project Handoff

## プロジェクト概要

```text
プロジェクト名: PersonalAI
ローカルパス: C:\AIProject\PersonalAI
GitHub: https://github.com/yogurt964/PersonalAI.git
現在バージョン: Ver2.70
開発環境: Windows / VS Code / PowerShell / Python venv / Git / GitHub / Codex / Ollama Qwen
```

このファイルは、ChatGPT、Codex、VS Codeなどの会話履歴や作業文脈が消えても、PersonalAIプロジェクトを再開できるようにするための引き継ぎ書である。

## PersonalAIの最終目標

PersonalAIの最終目標は、ユーザーがChatGPT、Codex、VS Code、PowerShell、ブラウザ、Word、Excel、PDFツールなどを直接触らなくても、PersonalAIを入口にしてほぼすべての作業をできるようにすることである。

限界はあるが、最終的には「このAI以外を直接触らなくても問題ない」状態を目指す。

PersonalAIは単なるチャットボットではなく、ユーザーの作業入口、記憶、判断、実行、安全確認を統括するシステムとして育てる。

PersonalAIの最終スコープは、開発補助に限定しない。
アプリ開発、ゲーム開発、資料作成、Web検索、データ分析、勉強、創作支援、予定管理、メールなどを扱う個人用総合AIアシスタントを目指す。
具体的な外部アプリは固定ではなく、用途や開発段階に応じて選ぶ。

ユーザーは、細かいコード差分よりも、実際の動作結果・自然さ・使いやすさ・ポートフォリオとしての見え方を重視する。

AIエージェントは、ユーザーが提案する前に不足観点を先回りして提案・確認する。
ただし、作業を止めすぎない。

安全管理は、致命的リスクを中心に行う。
PC破壊、大量課金、重要データ消失、外部流出、DB破壊、Git履歴破壊は必ず確認する。
一方で、後から修正できる通常作業はAIエージェントが自走してよい。

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

Ver2.23時点では、以下が実装済みである。

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
Ver2.20: Memory検索の最小実用化
Ver2.21: Claude Code移行用MIGRATION.md
Ver2.22: READMEのポートフォリオ見せ方強化
Ver2.23: Claude Code移行準備パッケージ
Ver2.24: Claude Code引継ぎ確認結果の反映
Ver2.25: Claude Code自走運用モード整備
Ver2.26: LLM Intent Resolver設計
Ver2.27: project_handoff.mdの現在バージョン固定依存の解消
Ver2.28: OpenAI利用方針の見直し（月間上限額制・都度確認省略）
Ver2.29: File Reader最小実装
Ver2.30: 「ワード」/「キーワード」誤判定バグ修正
Ver2.31: Reader結果をQwenでの応答に接続
Ver2.32: PDF Reader最小実装
Ver2.33: ファイルパス抽出のスペース対応バグ修正
Ver2.34: last_read_documentの誤解答防止
Ver2.35: 将来の記憶アーキテクチャ方針をdocs化
Ver2.36: Word Reader最小実装
Ver2.37: Excel Reader最小実装
Ver2.38: Excel Readerに数値列の自動集計を追加
Ver2.39: CLIに考え中表示を追加
Ver2.40: 応答の正直さ・Qwen性能・OpenAIエスカレーション方針をdocs化
Ver2.41: PowerPoint Reader最小実装
Ver2.42: Excel Readerにグループ集計を追加
Ver2.43: YouTube Reader最小実装
Ver2.44: 確認判定にハイブリッド方式（固定語彙優先＋不明時のみLLM）を導入
Ver2.45: SYSTEM_PROMPTに日本語回答の指示を追加
Ver2.46: SYSTEM_PROMPTの日本語指示に、明示指定があれば他言語に従う例外を追加
Ver2.47: Image Reader最小実装（ローカルvision、qwen2.5vl:7b）
Ver2.48: File Readerの対応拡張子をcsv/json/log/yaml/xml/ini/toml/tsvへ拡張
Ver2.49: File Readerの複数ファイル同時読み取りに対応
Ver2.50: 複数ファイル対応をPDF/Word/Excel/PowerPoint/Image Readerへ展開
Ver2.51: Reader結果全文のDB保存を追加
Ver2.52: Memory Candidate専用テーブル（提案結果の監査履歴）を追加
Ver2.53: Memory一覧表示・削除UI（削除は確認必須、非破壊的な無効化）を追加
Ver2.54: OpenAI vision接続（vision_router、月間予算ガード付き）を追加
Ver2.55: Image Readerの自動OpenAIエスカレーション（ローカル低信頼時のみ、予算ガード内）を追加
Ver2.56: Reader経由のテキスト応答（要約・質問）にも自動OpenAIエスカレーションを追加
Ver2.57: 画像・テキスト両方のエスカレーションにTier3（最上位モデル）を追加
Ver2.58: Web検索が必要な質問への対応（新機能、エスカレーションとは別枠）を追加
Ver2.59: OpenAI vision（画像入り）の実API検証
Ver2.60: 通常会話への自動OpenAIエスカレーション拡張
Ver2.61: Memory編集機能（内容の書き換え）
Ver2.62: 実機テストで見つかった3件の不具合修正（未実行操作の捏造回答・Memory重複・capability_managerキーワード誤爆）
Ver2.63: 商品・価格・実在リンクの断定回答を修正（Web検索対象の拡張、SYSTEM_PROMPTの抽象度向上）
Ver2.64: 解釈層全体のレイヤードパイプライン設計（docs/llm_intent_resolver_design.mdに追記、実装なし）
Ver2.65: エスカレーション条件・検証層・コストガバナンスの詳細設計（実装なし）
Ver2.66: Stage 1実装（input_analyzer/capability_manager/tool_request_builderの重複キーワード統合）
Ver2.67: Web検索/回答生成の分離可否を実APIで調査し、実現不可能と結論を確定
Ver2.68: Stage 2実装（ルーティング分類のハイブリッド化: capability_manager/web_search_intent）
Ver2.69: 不使用コード削除（tool_request_builder.py/tool_flow.py、影響する8チェックを外科的修正）
Ver2.70: 検証層B実装（通常会話の記憶操作捏造を検出し正直な注記を追加）
```

## 現在の主要ファイル

```text
AGENTS.md: AIエージェントが最初に読む短い開発運用ルール
MIGRATION.md: Claude Code / Cursorなど別開発環境へ移行するための包括的な引継書
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
core/confirmation_intent.py: 確認待ち状態の入力をweb_reader/file_reader共通で確認Intentとして解釈するルールベースresolver
core/web_reader_confirmation.py: URL入力からWeb Reader確認メッセージと確認応答dry-run結果を作る
core/file_reader_adapter.py: File Reader最小実用版（単一txt/mdファイルのみ）
core/file_reader_confirmation.py: ファイルパス入力からFile Reader確認メッセージと確認応答結果を作る
core/memory_candidate.py: Reader結果からMemory Candidateを作るdry-run
core/memory_candidate_confirmation.py: Memory Candidate確認応答と編集応答をdry-runで解釈
core/memory_candidate_saver.py: Memory Candidateを既存の長期記憶保存機構へ渡す保存処理
core/memory_search.py: 保存済みMemoryを簡易キーワード検索するread-only検索基礎
core/personal_ai.py: URL確認、確認応答、ToolRunner経由Web Reader実行、File Reader確認・実行、Memory Candidate dry-run、pending_memory_candidate_edit、last_memory_candidate_save_result、last_saved_memory_candidate_result、確認待ち状態の文脈解釈を接続
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
docs/claude_code_start.md: Claude Codeへ移行する際の開始手順
docs/portfolio_notes.md: 就活・面接で説明するための補助メモ
docs/portfolio_readme_policy.md: READMEをポートフォリオとして見せる方針
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
scripts/check_ver2200.py
scripts/check_ver2210.py
scripts/check_ver2220.py
scripts/check_ver2230.py
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

## OpenAI利用方針

今後はOpenAIの利用も想定している。現時点ではQwen / Ollama中心だが、LLM Intent Resolver、Memory抽出、資料読解、複雑なコード読解などでOpenAIを使う可能性がある。OpenAI利用は月間上限額を決めた運用とし、上限額の範囲内なら都度確認しない（上限額の初回設定・引き上げ、APIキー設定、個人情報・機密情報の外部送信は引き続き都度ユーザー確認が必要）。

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
Ver2.20でMemory検索の最小実用化を追加
`覚えてる？` などの入力からqueryを取り出し、保存済みMemoryを検索する
core/memory_search.py でread-onlyの簡易キーワード検索を分離
DBスキーマ変更はしない
LLMによる検索query生成はまだ未実装
Ver2.21でClaude Code移行用MIGRATION.mdを追加
MIGRATION.md に Claude Code / Cursor 移行用の役割分担、実装済み機能、未実装機能、安全ルール、開発コマンドを整理
ただしPDF/Image/YouTube/File Readerはまだ未実装
Ver2.22でREADMEのポートフォリオ見せ方を強化
READMEにMermaidのアーキテクチャ図と処理フローを追加
Web Reader → Memory Candidate → 保存 → 検索 のデモ導線を整理
技術的に工夫した点を面接で説明しやすい形に整理
docs/portfolio_readme_policy.md を追加
Ver2.23でClaude Code移行準備パッケージを追加
docs/claude_code_start.md にClaude Code開始手順、最初に読むファイル、引継ぎ確認タスクを整理
Claude Code移行後の最初の作業は、実装ではなく引継ぎ確認にする
自動checkでは実Webアクセスしない
URL検出だけでは自動Webアクセスしない
保留中の確認に対する肯定応答がある場合だけWeb Readerを実行する
user_confirmed=Falseでは実行しない
Reader結果全文のDB保存はまだしない
実Webアクセスはユーザー確認つきの手動確認で行う
Ver2.24でClaude Code引継ぎ確認結果の反映を追加
Claude Codeが AGENTS.md、MIGRATION.md、README.md、development_workflow.md、project_handoff.md、check_workflow.md、changelog.md、portfolio_readme_policy.md、demo_logs を読み、目的・実装済み機能・未実装スコープ・開発スタイル・コスト方針・失敗時対応・致命的リスク・次Ver候補を把握したことを確認
docs/claude_code_start.md のVer表記をVer2.23/2.24に合わせて修正
MIGRATION.md の古いロードマップ重複（Ver2.22表記）を整理
MIGRATION.md にコスト方針の金額ライン未確定の補足を追加
MIGRATION.md / README.md / docs/claude_code_start.md にQwen / OpenAIの利用方針を追加
`scripts/check_ver2240.py` を追加
`scripts/run_ver2_checks.py` に `check_ver2240.py` を追加
新機能実装、DBスキーマ変更、Memory保存・検索ロジック変更はしない
Ver2.25でClaude Code自走運用モードを整備
`CLAUDE.md` を新規作成し、Claude Code向けの短い運用ルール（Project / Read first / Current development mode / User preferences / Autonomous development rules / Confirmation rules / Cost rules / Failure handling / Checks / Git rules / Report format / Next version policy）を整理
`AGENTS.md` / `docs/claude_code_start.md` / `MIGRATION.md` から `CLAUDE.md` への参照を追加し、CLAUDE.md / AGENTS.md / MIGRATION.md / README.mdの役割分担を整理
README.mdの「現在はVer2.23です。」という固定Ver表記を、`docs/project_handoff.md` / `docs/changelog.md` を参照する表現に変更
README.mdの固定Ver番号にひもづいていた過去check（check_ver2190.py、check_ver2200.py、check_ver2210.py、check_ver2230.py）を、README内の固定文言ではなくdocs/project_handoff.md参照に緩和
`scripts/check_ver2250.py` を追加
`scripts/run_ver2_checks.py` に `check_ver2250.py` を追加
新機能実装、DBスキーマ変更、Memory保存・検索ロジック変更はしない
Ver2.26でLLM Intent Resolver設計を追加
`docs/llm_intent_resolver_design.md` を新規作成
LLMは解釈のみを担当し、実行可否はPermissionManager / ToolRunner / 状態管理が最終判断する方針を明記
既存のルールベースresolver（core/confirmation_intent.py、core/memory_candidate_confirmation.py）をフォールバックとして残す方針を明記
固定語彙で判定できる入力はLLMを呼ばないハイブリッド判定でコストを抑える方針を明記
モデル選定はQwenを優先し、精度不足時にOpenAI利用を検討する方針（ユーザー確認必須）を明記
段階的な実装ステップ案（プロンプト設計→dry-run→Qwen接続→精度確認→OpenAI検討）を整理
`scripts/check_ver2260.py` を追加
`scripts/run_ver2_checks.py` に `check_ver2260.py` を追加
core/confirmation_intent.py、core/memory_candidate_confirmation.pyの実装変更はしない
LLM呼び出し追加、DBスキーマ変更、Memory保存・検索ロジック変更、OpenAI/Claude/Gemini接続はしない
Ver2.27でproject_handoff.mdの現在バージョン固定依存を解消
`scripts/check_ver2180.py`〜`check_ver2260.py`が`project_handoff.md`の「現在バージョン: VerX.X」を厳密な文字列一致で要求していたため、バージョンを上げるたびに過去checkを機械的に追随修正する必要があった
該当する9本のcheckを、「現在バージョン:」という項目自体の存在確認に緩和し、具体的なバージョン番号には依存しないようにした
過去の実績記録（例:「Ver2.24: Claude Code引継ぎ確認結果の反映」のような達成済みVerの説明文）は、履歴として引き続き要求する
`scripts/check_ver2270.py` を追加し、対象9本のcheckに固定バージョン番号への依存が残っていないことを継続的に確認する
`scripts/run_ver2_checks.py` に `check_ver2270.py` を追加
新機能実装、DBスキーマ変更、Memory保存・検索ロジック変更はしない
Ver2.28でOpenAI利用方針を見直し
OpenAI機能が今後複数増えると都度確認が煩雑になるとのユーザー指摘を受け、OpenAI利用を「月間上限額を決めた運用」に変更
OpenAIを初めて実接続する前に月間上限額を決める（初回設定・引き上げは都度ユーザー確認）方針に変更し、上限額の範囲内であれば通常のOpenAI API呼び出しは都度確認しない方針にした
APIキーの新規設定・変更、個人情報・機密情報を含む外部送信は、月間上限額の話とは別に引き続き都度ユーザー確認する方針を維持
作業や回答の精度を最優先とし、コスト削減のために精度を犠牲にしない方針を明記
MIGRATION.md / CLAUDE.md / AGENTS.md / README.md / docs/claude_code_start.md / docs/llm_intent_resolver_design.md のOpenAI関連記述を更新
実際の月間上限額（具体的な金額）は、OpenAIを実接続する段階で改めてユーザーと決める
`scripts/check_ver2280.py` を追加
`scripts/run_ver2_checks.py` に `check_ver2280.py` を追加
OpenAI実接続、APIキー設定、DBスキーマ変更、Memory保存・検索ロジック変更はしない
Ver2.29でFile Reader最小実装を追加
`core/file_reader_adapter.py` を追加し、ユーザーが指定した単一のtxt/mdファイルだけを読み取れるようにした
対応拡張子はtxt/mdに限定し、ディレクトリ探索・ワイルドカード・書き込み・実行は行わない
ファイルサイズ上限（デフォルト1MB）を超える場合は読み取らない方針を追加
`core/file_reader_confirmation.py` を追加し、Web Reader同様に実行前確認を必須にした
`core/confirmation_intent.py` を汎用化し、`context_type="file_reader"` でもWeb Readerと同じ「はい/いいえ」語彙を再利用できるようにした（Web Reader側の挙動は変更なし）
`core/personal_ai.py` にFile Readerを接続し、確認→ToolRunner経由実行→本文プレビュー表示の流れをWeb Readerと同じ設計で追加
Ver2.29ではMemory Candidateへの接続は行わない（Web ReaderがVer2.0で辿った段階と同じ最小スコープ）
対応外拡張子（pdfなど）は、既存のCapabilityManagerによる「未実装」応答にそのまま委ねる
`scripts/check_ver2290.py` を追加し、一時ディレクトリ内のfakeファイルのみを使って、パス検出・確認・ToolRunner実行・キャンセル・存在しないファイル・対応外拡張子・PersonalAI結合の各シナリオを確認する
自動チェックでは実際のユーザーファイルへはアクセスせず、一時テスト用ファイルのみを使う
`scripts/run_ver2_checks.py` に `check_ver2290.py` を追加
DBスキーマ変更、Memory保存・検索ロジック変更、PDF/Image/YouTube Readerの実装はしない
Ver2.30でFile Reader実機テスト中に見つかった「ワード」/「キーワード」誤判定バグを修正
File Readerの実機テストで「テストキーワードを教えて」と聞くと文書作成モードに誤って入る不具合が見つかった
原因は`core/input_analyzer.py`、`core/capability_manager.py`、`core/tool_request_builder.py`の文書作成判定が、単純な部分一致で「ワード」を検出しており、「キーワード」という単語自体に「ワード」が含まれるため誤爆していたこと
3ファイルの該当キーワードを「ワード文書」「ワードで」「ワードファイル」という、より具体的な語に修正し、「キーワード」との衝突を解消した
実際のWord文書作成依頼（例: 「Wordで文書を作って」）は引き続き正しく検出されることを確認した
File Reader自体のロジックは変更していない
`scripts/check_ver2300.py` を追加
`scripts/run_ver2_checks.py` に `check_ver2300.py` を追加
Ver2.31でReader結果をQwenでの応答に接続
File Reader実機テストで、読み取った内容について追加質問できない、「読んで要約して」を同時に実行できないという課題が見つかった
`core/personal_ai.py` に `last_read_document`（直近に読み取ったWeb Reader / File Readerの本文）を保持する仕組みを追加
`build_messages()` に `last_read_document` の内容をsystem messageとして注入し、読み取り後の別ターンでの追加質問にも、本文（上限4000文字）をもとに答えられるようにした
読み取り依頼に要約・質問などの目的（InputAnalyzerのtask_type）が含まれていた場合、読み取った本文全文をもとにQwenへ直接問い合わせて回答する `build_document_task_response_if_requested` を追加し、「読んで要約して」を同一ターンで実行できるようにした
単なる「読んで」だけの依頼は、従来通りの本文プレビュー表示を維持する
自動チェックで実LLMを呼ばないよう、`PersonalAI.ask_llm_func`（デフォルトは実際の`ask_llm`）を注入可能にした
`scripts/check_ver2310.py` を追加し、fakeのLLM関数を使って、読み取り+要約の同時実行、プレーンな読み取りの現状維持、別ターンでの文脈利用、未読み取り時に文脈が注入されないことを確認する
`scripts/run_ver2_checks.py` に `check_ver2310.py` を追加
DBスキーマ変更、Memory保存・検索ロジック変更はしない
Ver2.32でPDF Reader最小実装を追加
`requirements.txt` を新規作成し、実際に使用しているパッケージ（ollama、SQLAlchemy、pypdf）を記録
`core/pdf_reader_adapter.py` を追加し、ユーザーが指定した単一のPDFファイルからpypdfでテキストを抽出できるようにした
ページ数上限（デフォルト50ページ）・ファイルサイズ上限（デフォルト20MB）を設け、暗号化・破損PDFや画像だけのスキャンPDF（テキストなし）は読めたふりをせず正直に失敗を返す
`core/pdf_reader_confirmation.py` を追加し、Web/File Reader同様に実行前確認を必須にした
`core/confirmation_intent.py` に `context_type="pdf_reader"` を追加し、既存の「はい/いいえ」語彙を再利用
`core/personal_ai.py` にPDF Readerを接続し、Web/File Readerと同じ「確認 → ToolRunner経由実行 → 本文プレビュー、または要約・質問への直接回答」の流れを追加（`remember_last_read_document` / `build_document_task_response_if_requested` を共通利用）
自動チェックでは、手書きで生成した実PDFバイナリを使いpypdfでの実テキスト抽出を確認し、PersonalAI経由の会話フローもfakeのPDF Readerで確認する
`scripts/check_ver2320.py` を追加
`scripts/run_ver2_checks.py` に `check_ver2320.py` を追加
DBスキーマ変更、Memory保存・検索ロジック変更はしない
Ver2.33でファイルパス抽出のスペース対応バグを修正
PDF Reader実機テストで、スペースを含むファイル名（Windowsの重複ダウンロードによる「curry_shop_reading_test (1).txt」形式）を指定すると、パスの一部（「(1).txt」）しか読み取られない不具合が見つかった
原因は`core/file_reader_adapter.py`と`core/pdf_reader_adapter.py`が、スペースなしの1トークンだけを拾う正規表現（`\S+\.拡張子`）でパスを抽出していたこと
`core/file_path_extraction.py` を新規作成し、引用符つきパス・ドライブレター始まりのWindows絶対パス（スペースや括弧を含んでもよい）・スペースなしの単純パス、の優先順位で抽出する共通関数 `extract_single_file_path_from_text` を追加
`file_reader_adapter.py` / `pdf_reader_adapter.py` を、この共通関数を使うようリファクタリング（公開関数名・シグネチャは変更なし）し、同じバグを将来のWord/Excel/PowerPoint Readerで再発させない設計にした
`core/confirmation_intent.py` の`WEB_READER_CONFIRMED_WORDS`に「イエス」を追加（実機テストで確認できた語彙の抜け）
実際のバグ再現ケース（スペースを含む絶対パス）でPersonalAI経由の読み取りが正しく動作することを確認した
`scripts/check_ver2330.py` を追加
`scripts/run_ver2_checks.py` に `check_ver2330.py` を追加
DBスキーマ変更、Memory保存・検索ロジック変更はしない
Ver2.34でlast_read_documentの誤解答を防止
実機テストで、2件目のファイル（PDF）を読んだ後に1件目のファイル（テキスト）の内容を聞くと、「他のファイルには記載されていません」と誤って断定する挙動が見つかった
`last_read_document`は直近1件のみを保持する設計（Ver2.31時点の既知の制約）のため、以前のファイルの本文はもうLLMに渡っていないが、そのことをLLM側に明示していなかったため、不正確な断定応答になっていた
`build_last_read_document_context()` のsystem message文言を修正し、「これより前に読み取った別のファイルの内容は、この会話ではもう保持していません」「別のファイルにも書かれていないと断定しないでください」を明記
実際のバグ再現ケース（2件連続で読み取り、1件目について質問）で、context messageが正しく警告することを確認した
`scripts/check_ver2340.py` を追加
`scripts/run_ver2_checks.py` に `check_ver2340.py` を追加
DBスキーマ変更、Memory保存・検索ロジック変更はしない
Ver2.35で将来の記憶アーキテクチャ方針をdocs化
ユーザーから、会話・Web検索・File/PDF Readerなどで得た情報を、短期記憶・長期記憶・知識に自動分類し、重要度判定・自動的な忘却判断を行う記憶アーキテクチャを最終的に望んでいるという方針を確認した
これは`docs/final_product_vision.md`の記憶階層（Raw Log〜Deletion Candidate）の本格実装であり、Reader個別の機能ではなくPersonalAIの記憶機能そのものの本実装として扱う方針を`docs/reader_memory_policy.md`に整理した
現在のFile Reader / PDF ReaderはMemory Candidateへ未接続であること、`last_read_document`（Ver2.31）は長期Memoryとは別の暫定キャッシュであることを明記した
記憶機能を本格的に作り直すタイミングで、あらためてユーザーと設計を確認する方針とし、それまでの暫定対応はAIエージェントの判断に委ねられた
コード実装は行っていない
Ver2.36でWord Reader最小実装を追加
`requirements.txt` に `python-docx` / `lxml` を追加
`core/word_reader_adapter.py` を追加し、ユーザーが指定した単一の.docxファイルからpython-docxで段落・表のテキストを抽出できるようにした
古い.doc形式（バイナリ）や破損ファイルは読めたふりをせず正直に失敗を返す
`core/word_reader_confirmation.py` を追加し、Web/File/PDF Reader同様に実行前確認を必須にした
`core/confirmation_intent.py` に `context_type="word_reader"` を追加
`core/personal_ai.py` にWord Readerを接続し、既存Reader群と同じ「確認 → ToolRunner経由実行 → 本文プレビュー、または要約・質問への直接回答」の流れを追加
開発中に、`core/input_analyzer.py` / `core/capability_manager.py` / `core/tool_request_builder.py` の文書作成判定にある素の「Word」「word」「Excel」「excel」キーワードが、`word_report (1).docx` のようなファイル名自体に含まれる「word」と衝突し、読み取り+要約の同時実行が誤って文書作成モードに入ってしまう不具合を発見
Ver2.30の「ワード」/「キーワード」衝突と同種の問題であったため、3ファイルすべてで該当キーワードをより具体的な語（"Word file"、"Word document"、"in Word"、"Wordで"、"Excel file"、"Excel document"、"in Excel"）に置き換えて修正（Excelも同時に予防的に修正）
`scripts/check_ver2360.py` を追加し、ファイル名にword/excelを含むケースでの結合テストも含めて確認する
`scripts/check_ver2290.py` の「対応外拡張子」テストを、.docxが実装済みになったため.xlsxに変更
`scripts/run_ver2_checks.py` に `check_ver2360.py` を追加
DBスキーマ変更、Memory保存・検索ロジック変更はしない
Ver2.37でExcel Reader最小実装を追加
`requirements.txt` に `openpyxl` / `et-xmlfile` を追加
`core/excel_reader_adapter.py` を追加し、ユーザーが指定した単一の.xlsxファイルからopenpyxlでシート・セルのテキストを抽出できるようにした
数式は評価値ではなく保存済みの計算済み値（data_only=True）を読み取り、マクロは実行しない
古い.xls形式（バイナリ）や破損ファイルは読めたふりをせず正直に失敗を返す
Windowsで`load_workbook(read_only=True)`のファイルハンドルが残る問題を、明示的な`close()`で解消
`core/excel_reader_confirmation.py` を追加し、他Reader同様に実行前確認を必須にした
`core/confirmation_intent.py` に `context_type="excel_reader"` を追加
`core/personal_ai.py` にExcel Readerを接続し、既存Reader群と同じ流れを追加
ファイル名に「excel」を含むケース（例: excel_report (1).xlsx）でも、Ver2.36で修正済みのキーワード衝突対策により誤判定なく動作することを確認した
`scripts/check_ver2370.py` を追加
`scripts/check_ver2290.py` の「対応外拡張子」テストを、.xlsxが実装済みになったため.pptxに変更
`scripts/run_ver2_checks.py` に `check_ver2370.py` を追加
DBスキーマ変更、Memory保存・検索ロジック変更はしない
Ver2.38でExcel Readerに数値列の自動集計を追加
実機テストで、「総売上はいくら」「平均満足度は」のような集計質問に対し、AIが実際に計算せず一般的な説明を繰り返すだけの問題が見つかった
原因は、行データをそのままテキストで渡すだけで、合計・平均などの値がどこにも計算されておらず、LLMにテキストから再計算させるのは精度が低いこと、かつ大きな表では文字数上限で本文が途中で切れ、全行を見られない場合があること
`core/excel_reader_adapter.py` に `_build_numeric_column_summary()` を追加し、1行目をヘッダーとみなして数値だけの列（テキストが混在する列は対象外）について合計・平均・最小・最大・件数をPythonで正確に計算するようにした
計算結果は行データより先に配置し、文字数上限で本文が切り詰められても正確な集計値が残るようにした
「列名」「店舗」のような文字列だけの列は誤って集計しないことを確認した
`scripts/check_ver2380.py` を追加し、実際の売上データに近いテストケースで合計・平均が正しく計算されること、同一ターンでの要約・別ターンでの追加質問の両方で集計値を参照できることを確認する
「一番売上が高い店舗はどこか」のようなグループ集計（店舗ごとの合計比較）は今回のスコープ外とし、今後の課題として残す
`scripts/run_ver2_checks.py` に `check_ver2380.py` を追加
DBスキーマ変更、Memory保存・検索ロジック変更はしない
Ver2.39でCLIに考え中表示を追加
実機テストで、Excelの集計質問への応答にQwenが5分以上かかり、何も表示されないため停止したように見える状況が発生した
トレースバックで確認した結果、`ask_llm`がOllamaからのHTTP応答を待っている最中（`self._sock.recv`）であり、コードの不具合ではなく、qwen3:8bが実際に処理に時間をかけていたことが分かった
`core/personal_ai.py`の`run()`に、ユーザー入力受付直後・`handle_user_input`呼び出し前に「Qwenが考え中です。内容によっては数分かかることがあります…」という表示を追加し、処理中であることが分かるようにした
`scripts/check_ver2390.py` を追加し、表示が入力受付後・応答生成前の正しい位置にあることを確認する
`scripts/run_ver2_checks.py` に `check_ver2390.py` を追加
ユーザーから、Qwenで答えられる工夫（今回のExcel自動集計のような、LLMに重い計算をさせない設計）を優先しつつ、将来的に必要な場面ではOpenAIを頼れるようにしてほしいという方針を確認した。これはMIGRATION.mdの「Qwen / OpenAIの利用方針」（Qwen優先、精度不足時にOpenAI検討、月間上限額制）に沿うものであり、追加のdocs変更は行っていない
コード実装は表示追加のみで、応答生成ロジックやタイムアウト処理は変更していない
```

Ver2.40では、応答の正直さ・Qwen性能・OpenAIエスカレーション方針をdocs化した。

実機テストで、Excel Reader経由の質問に対し、①事前計算済みの正しい集計値があるのに受け流すだけで使わない、②未実装のグループ集計（列をまたぐ集計・比較）をQwenが自己流に計算し、検証されていない値を断定的に答えてしまう、という2つの問題が見つかった。
これはQwen（qwen3:8b）の推論能力・応答の一貫性に起因する部分が大きいと判断し、Ver2.40では修正しない（ユーザーの了承済み）。

ユーザーから、将来的に以下を実現してほしいという方針を確認した。

```text
分からない・自信がない場合は断定せず正直に「分からない」と言えるようにする
Qwen（ローカルモデル）自体の性能・推論能力を向上させる方法を検討する
Qwenで精度が不十分な場合に、必要に応じてOpenAIを頼れるようにする（月間上限額制の実装を含む）
```

`docs/conversation_quality.md`に「データ分析・集計の正直さ」節を追加し、`MIGRATION.md`の「Qwen / OpenAIの利用方針」に「OpenAIエスカレーションの将来トリガー」節を追加した。
これらは会話品質・ModelRouter・OpenAI接続に関わる本格的な設計判断であり、個別のReader実装ではなくPersonalAI本体の応答品質・モデル選択の仕組みとして扱う。着手する場合はあらためてユーザーと設計を確認する。
コード実装は行っていない。

Ver2.41でPowerPoint Reader最小実装を追加

```text
requirements.txt に python-pptx / XlsxWriter / Pillow を追加
core/pptx_reader_adapter.py を追加し、ユーザーが指定した単一の.pptxファイルから、スライドのタイトル・本文・表・ノートのテキストをpython-pptxで抽出できるようにした
古い.ppt形式（バイナリ）や破損ファイル、画像だけのスライドは読めたふりをせず正直に失敗を返す
core/pptx_reader_confirmation.py を追加し、他Reader同様に実行前確認を必須にした
core/confirmation_intent.py に context_type="pptx_reader" を追加
core/personal_ai.py にPowerPoint Readerを接続し、既存Reader群と同じ流れを追加
ファイル名に"powerpoint"を含むケースでも、キーワード衝突は起きないことを確認した（input_analyzer / capability_manager / tool_request_builder にPowerPoint関連の素のキーワードがそもそも存在しないため）
scripts/check_ver2410.py を追加
scripts/check_ver2290.py の「対応外拡張子」テストを、.pptxが実装済みになったため.png（Image Reader未実装）に変更
scripts/run_ver2_checks.py に check_ver2410.py を追加
DBスキーマ変更、Memory保存・検索ロジック変更はしない
これでOffice系Reader（Word/Excel/PowerPoint）が一通り揃った
```

Ver2.42でExcel Readerにグループ集計を追加

```text
これまで対応していなかった「一番売上が高い店舗はどこ？」のような、カテゴリ列（店舗名など）をまたぐ比較質問に対応した
core/excel_reader_adapter.py に _build_group_by_summary() を追加し、繰り返し値を持つ文字列列（カテゴリ列）でグループ化して、数値列ごとの合計が最大・最小になるグループをPythonで正確に計算する
出力を抑えるため、グループの全内訳ではなく最大・最小のグループだけを報告する
全行が一意な値を持つ列（注文IDなど）は、合計しても意味がないため数値集計対象から除外する
値がすべて一意なカテゴリ列（グループ化する意味がない列）も対象外にする
集計結果は既存の数値列集計と同じく行データより先に配置し、文字数上限で切り詰められても残るようにした
scripts/check_ver2420.py を追加し、実際の売上データに近いテストケースで店舗ごとの合計比較が正しく計算されること、ID列が誤って集計されないこと、同一ターンでの要約・別ターンでの追加質問の両方で参照できることを確認する
scripts/run_ver2_checks.py に check_ver2420.py を追加
DBスキーマ変更、Memory保存・検索ロジック変更はしない
```

Ver2.43でYouTube Reader最小実装を追加

```text
requirements.txt に youtube-transcript-api / requests / urllib3 / charset-normalizer / defusedxml を追加
core/youtube_reader_adapter.py を追加し、ユーザーが指定した単一のYouTube動画から、既存の字幕・自動生成トランスクリプトのみをyoutube-transcript-apiで取得できるようにした（動画・音声のダウンロードや文字起こしの実行はしない）
対応URL形式: youtube.com/watch?v=、youtu.be/、youtube.com/embed/、youtube.com/shorts/
字幕が存在しない・無効化されている・動画が非公開/削除済みの場合は読めたふりをせず正直に失敗を返す
core/youtube_reader_confirmation.py を追加し、他Reader同様に実行前確認を必須にした（ファイルパスではなくYouTube URLを対象とする点のみ異なる）
core/confirmation_intent.py に context_type="youtube_reader" を追加
core/personal_ai.py にYouTube Readerを接続し、capability_managerのyoutube_read_required（未実装扱い）より先に判定されるようにした
自動checkでは実際のYouTubeへアクセスせず、fakeのtranscript_fetcherで動作を確認する。実際のYouTube動画での動作確認はユーザー自身に行ってもらう方針とした（Web Readerの実Web手動テストと同じ運用）
scripts/check_ver2430.py を追加
scripts/run_ver2_checks.py に check_ver2430.py を追加
DBスキーマ変更、Memory保存・検索ロジック変更はしない
```

Ver2.44で確認判定にハイブリッド方式（固定語彙優先＋不明時のみLLM）を導入

```text
Ver2.30以来、Web/File/PDF/Word/Excel/PowerPoint/YouTube Reader共通の実行確認は固定語彙リストのみで判定していた
ユーザーと「キーワード判定をLLM解釈へ置き換える検討」について相談し、プロンプトインジェクションなどの安全性リスクと精度向上のトレードオフを説明した上で、次のハイブリッド設計を採用した
1. まず固定語彙リスト（WEB_READER_CONFIRMED_WORDS / REJECTED_WORDS）で判定する。一致すれば今まで通り決定的に処理し、LLMは一切呼び出さない
2. 固定語彙に一致しない場合のみ、LLMに「confirmed/rejected/unclearの1語で答えて」と単独で解釈させる
3. LLMに渡すのはユーザー自身の返信テキストだけで、Readerが読み込んだ外部本文（Web/PDF/YouTube等）は一切含めない。これは外部contentに紛れた指示文で実行許可を誤認識させるリスクを避けるため
4. LLMの応答が3語のどれにも一致しない、または呼び出しに失敗した場合は、必ずunclear（不明・再確認）にfail-safeする。silentに実行許可扱いにすることは絶対にしない
core/confirmation_intent.py の resolve_confirmation_intent() / _resolve_generic_confirmation_intent() にask_llm_func引数を追加し、上記のロジックを実装した
core/{web,file,pdf,word,excel,pptx,youtube}_reader_confirmation.py の resolve_X_reader_confirmation_response() すべてにask_llm_func引数を追加して橋渡しした
core/personal_ai.py の7つのhandle_pending_X_reader_confirmation()すべてで、self.ask_llm_func（Qwen呼び出し関数、テストでは差し替え可能）を渡すようにした
ask_llm_funcを渡さない呼び出し元（Ver2.44以前の古いcheckスクリプトが作るtest doubleなど）は、暗黙に実際のQwenを呼び出さず、これまで通りunclearのままにする設計にし、既存の全checkが無変更で通るようにした
scripts/check_ver2260.pyの「confirmation_intent.pyは変更しない」というVer2.26時点のpinを、「ハイブリッド方式が実装された」ことを確認するpinに更新した（Ver2.26は設計docのみで、Ver2.44が実際に実装したため）
scripts/check_ver2440.py を追加
scripts/run_ver2_checks.py に check_ver2440.py を追加
DBスキーマ変更、Memory保存・検索ロジック変更はしない
```

将来的な設計方針（ユーザーと合意済み、Image Reader着手時に反映）:

```text
PersonalAIはQwen/OpenAI/Visionなどの機能を「道具」として使い分ける設計が本来の意図であるため、Image Reader実装時はvision routerを単独の特殊ロジックにせず、将来のModelRouter/ToolRouterの一部として設計すること
Image Readerはローカルvisionモデル（ユーザーのRTX 4070 SUPER・メモリ32GBで実用的）とOpenAI visionの併用とし、難易度や安全性に応じてLLMが使い分けを判断する
OpenAI契約は必要になったタイミングでユーザーと一緒に金額等を決める（今はまだ契約しない）
```

Ver2.45でSYSTEM_PROMPTに日本語回答の指示を追加

```text
実機テストのスクリーンショットで、Excel Readerでの会話中に「ありがとう」という日本語入力に対し、Qwenが英語で応答する場面が見つかった
ユーザーから「少し気になる」との指摘があり、低リスク・低コストで直せる範囲のため、その場で修正した
ai/llm.py のSYSTEM_PROMPTに「ユーザーが日本語で話しかけている場合は、日本語で回答する（英語などへ勝手に切り替えない）」を1行追加
scripts/check_ver2450.py を追加し、SYSTEM_PROMPTにこの指示が含まれることを確認する
既存の全checkスクリプトへの影響がないことを確認した（SYSTEM_PROMPTの内容を厳密一致で検証するcheckは存在しない）
DBスキーマ変更、Memory保存・検索ロジック変更はしない
これは根本的な言語切り替え問題を保証するものではなく、Qwenへの指示強化による軽減策。完全な解決が必要な場合はVer2.40で記録した「Qwen性能改善・OpenAIエスカレーション」の本格設計の中で扱う
```

Ver2.46でSYSTEM_PROMPTの日本語指示に例外を追加

```text
Ver2.45で追加した「日本語で話しかけられたら日本語で回答する」という指示が、ユーザーが明示的に別言語を指定した場合（例:「英語で答えて」）にも対応できるよう、例外規定を1行追加した
ai/llm.py のSYSTEM_PROMPTに「ただし、ユーザーが『英語で答えて』のように別の言語を明示的に指定した場合は、その指定に従う」を追加
これも根本的な言語切り替え問題（解釈の精度）の完全な解決ではなく軽減策。完全な解決はVer2.40で記録した「Qwen性能改善・OpenAIエスカレーション」の本格設計で扱う
scripts/check_ver2460.py を追加
scripts/run_ver2_checks.py に check_ver2460.py を追加
DBスキーマ変更、Memory保存・検索ロジック変更はしない
```

READMEスクリーンショットについては、提出が近づいたタイミングで現時点の動作として数枚貼る方針で合意（今は急がない）

Ver2.47でImage Reader最小実装（ローカルvision）を追加

```text
ローカルvisionモデル qwen2.5vl:7b をOllamaに追加（6GB、ユーザーのRTX 4070 SUPER・メモリ32GBで実機確認済み）
core/vision_router.py を追加。choose_vision_backend()は現時点で常に"local"を返すが、
将来OpenAI vision接続時にここへ難易度・安全性判定を追加できる設計にした
（ユーザーの「機能を道具として使い分ける設計にしてほしい」というフィードバックに沿った実装）
core/image_reader_adapter.py を追加し、ユーザーが指定した単一の画像ファイル（.png/.jpg/.jpeg/.bmp/.gif/.webp）を
ローカルvisionモデルで解析し、日本語で詳しい説明を生成できるようにした
画像と一緒に具体的な質問が来ている場合、元のメッセージを解析プロンプトに含め、最初の解析でできるだけ
具体的に答えるようにした（後続ターンでは画像そのものを再度見られないため）
破損画像・非対応形式・vision呼び出し失敗時は読めたふりをせず正直に失敗を返す
core/image_reader_confirmation.py を追加し、他Reader同様に実行前確認を必須にした
core/confirmation_intent.py に context_type="image_reader" を追加
core/personal_ai.py にImage Readerを接続し、capability_managerのimage_read_required（未実装扱い）より先に判定されるようにした
実機で赤い正方形・青い円を描いたテスト画像を読み取らせ、正しく形状・色を認識できることを確認した
scripts/check_ver2470.py を追加（fakeのvision_describerを使い、実際のOllama呼び出しはしない）
scripts/check_ver2290.py の「対応外拡張子」テストを、.pngが実装済みになったため.mp4に変更
scripts/run_ver2_checks.py に check_ver2470.py を追加
DBスキーマ変更、Memory保存・検索ロジック変更はしない
OpenAI vision（クラウド側の併用）は未接続のまま。接続する際はAPIキー設定・費用面を含め改めてユーザーに確認する
```

Ver2.48でFile Readerの対応拡張子を拡張

```text
未実装として残っていた「File Reader（txt/md以外の拡張子）」に対応した
core/file_reader_adapter.py のALLOWED_EXTENSIONSを (.txt, .md) から
(.txt, .md, .csv, .json, .log, .yaml, .yml, .xml, .ini, .toml, .tsv) へ拡張
いずれもプレーンテキスト系の形式で、既存のUTF-8デコード処理をそのまま使える
PDF/Word/Excel/PowerPoint/画像などバイナリ形式は引き続き専用のReaderが担当し、File Readerの対象外のまま
_get_path_from_request()が、コンストラクタ引数allowed_extensionsを無視してモジュール定数だけを見ていたバグを修正し、
インスタンスごとの拡張子制限が実際にパス抽出にも反映されるようにした
実機でcsv・jsonファイル（スペースを含むファイル名含む）を読み取らせ、正しく動作することを確認した
scripts/check_ver2480.py を追加
scripts/run_ver2_checks.py に check_ver2480.py を追加
DBスキーマ変更、Memory保存・検索ロジック変更はしない
外部サービス・APIキー・費用は一切関係しないため、確認なしで実装した
```

Ver2.49でFile Readerの複数ファイル同時読み取りに対応

```text
ユーザーへ「PDF/File Readerの複数ファイル・ディレクトリ読み取り対応」について確認したところ、
「複数ファイルを一気に読み取れる方がいい」との回答。ただしディレクトリ丸ごとの読み取りは対象外とし、
ユーザーが名指ししたファイルだけを対象にする設計とした
core/file_path_extraction.py に extract_multiple_file_paths_from_text() を追加。
既存の3パターン（引用符 / Windows絶対パス / 素のパス）を出現順に走査し、重複を除いて
最大5件まで返す。既存のextract_single_file_path_from_text()は無変更
core/file_reader_confirmation.py の FileReaderConfirmation に paths（リスト）フィールドを追加。
1件の場合はVer2.49以前と完全に同じ文言・挙動を維持し、2件以上の場合だけ複数ファイル用の
確認文言・action="read_files"に切り替える（既存の単一ファイルフローへの回帰は一切なし）
core/personal_ai.py の execute_file_reader_tool_request_candidate() で、複数パスの場合は
1ファイルずつToolRunner経由で実行し、build_multi_file_reader_tool_response()で結果をまとめる
（File Reader Adapter自体は単一ファイルのまま変更していない）
成功したファイルの本文は「[ファイル名]\n本文」の形で連結し、1つのlast_read_documentとして記憶。
一部のファイルが失敗した場合も、成功分は読み取りつつ失敗理由を個別に報告する
scripts/check_ver2490.py を追加（単一ファイル挙動の完全な非回帰、複数ファイル読み取り、
一部失敗時の挙動、同一ターン要約・別ターン追加質問での複数ファイル参照を確認）
scripts/run_ver2_checks.py に check_ver2490.py を追加
外部サービス・APIキー・費用は一切関係しないため、確認なしで実装した
PDF/Word/Excel/PowerPoint/Image/YouTube Readerへの複数ファイル対応は今後、同じパターンで順次追加予定
```

ユーザーから、DBスキーマの追加変更（将来の忘却機能実装のため）を許可された。ただし修復不可能な操作（データ削除等）は引き続き都度確認する方針。
これにより「Reader結果全文のDB保存」「Memory Candidate専用テーブル」「Memory編集・削除UI」（削除自体は都度確認）が着手可能になった。

Ver2.50でPDF/Word/Excel/PowerPoint/Image Readerに複数ファイル対応を展開

```text
Ver2.49で確立したFile Readerの複数ファイルパターンを、PDF/Word/Excel/PowerPoint/Image Readerにも展開した
（YouTube ReaderはURLの性質が異なるため対象外。必要であれば別途検討する）
core/{pdf,word,excel,pptx,image}_reader_confirmation.py それぞれに paths（リスト）フィールドを追加。
単一ファイルの場合はVer2.50以前と完全に同じ文言・挙動を維持し、2件以上の場合だけ複数ファイル用の
確認文言・action（read_pdfs/read_words/read_excels/read_pptxs/read_images）に切り替える
core/personal_ai.py の execute_X_reader_tool_request_candidate() 5つに、複数パス時の
_execute_X_reader_multi() ヘルパーを追加（各Reader Adapter自体は単一ファイルのまま変更していない）
build_multi_X_reader_tool_response() 5つは、共通処理 _build_multi_reader_tool_response() に
まとめた（File Readerの実装も含めて6 Reader共通化）。Image Readerだけ文言（「解析」「画像」「説明」）が
異なるため、item_label/success_verb/failure_verb/failure_intro/content_labelを個別指定できるようにした
scripts/check_ver2500.py を追加（5 Reader全ての単一ファイル非回帰、複数ファイル確認、
Word/Imageでの実際の複数ファイル読み取り・結合・要約・一部失敗を確認）
scripts/run_ver2_checks.py に check_ver2500.py を追加
外部サービス・APIキー・費用は一切関係しないため、確認なしで実装した
```

Ver2.51でReader結果全文のDB保存を追加

```text
ユーザーから、DBスキーマの追加変更は許可されたが、「将来長期記憶にする場合は全文ではなく必要な情報に
絞って覚えられるといい」との補足があった。このため、今回追加するのはあくまで生ログ（Raw Log相当）の
保存であり、長期記憶そのものではないことをdocs/reader_memory_policy.mdに明記した
database/models.py に ReaderResult テーブルを追加（id/created_at/source_tool/title/location/text/truncated）
database/reader_results.py に save_reader_result() / get_recent_reader_results() を追加
（chat_history.py / memory_manager.pyと同じSessionLocalパターン）
core/personal_ai.py の remember_last_read_document() から、self.reader_result_saver（デフォルトは
save_reader_result）を呼び出すようにした。__init__ で実際の関数を設定するが、reader_result_saver属性を
持たないtest double（Ver2.51以前のcheckスクリプトが作るものすべて）は暗黙にDBへ書き込まない設計にし、
既存の全checkが無変更で通るようにした（Ver2.44のask_llm_funcと同じ設計パターン）
scripts/check_ver2510.py を追加。本番DB（data/personal_ai.db）には一切触れず、独立したin-memory SQLiteで
save_reader_result / get_recent_reader_results の実際のSQL動作を検証する
scripts/run_ver2_checks.py に check_ver2510.py を追加
テーブル作成自体は、実際のアプリ起動時にcreate_database()（Base.metadata.create_all、追加のみで既存
テーブルは変更しない）が行う。checkスクリプトの中では実行しない
```

Ver2.52でMemory Candidate専用テーブル（提案結果の監査履歴）を追加

```text
これまでMemory Candidateは、確認・保存・却下・保留の判断結果を一切記録せず、
実際に保存された場合のみ memories テーブルへ直接書き込んでいた（提案自体の履歴は残らない）
database/models.py に MemoryCandidateRecord テーブルを追加
（id/created_at/source_tool/source_url/title/summary/candidate_type/risk_level/status/saved_memory_id）
database/memory_candidates.py に save_memory_candidate_record() / get_recent_memory_candidate_records() を追加
core/personal_ai.py の handle_pending_memory_candidate_confirmation() から、self.memory_candidate_recorder
（デフォルトはsave_memory_candidate_record）を、saved/rejected/postponedの結果確定時に呼び出すようにした
（Ver2.51のreader_result_saverと同じ設計パターン。属性未設定のtest doubleは暗黙にDBへ書き込まない）
これは実際の長期記憶（memoriesテーブル）とは別の監査履歴であり、「どんな候補が提案されどう判断されたか」を
記録するためのもの。saved_memory_idの正確な紐付け（save_memory()自体がID を返さない）は今回は行わず、
Noneのままにする軽微な制約として残す
scripts/check_ver2520.py を追加。本番DBには一切触れず、独立したin-memory SQLiteで実際のSQL動作を検証する
scripts/run_ver2_checks.py に check_ver2520.py を追加
```

Ver2.53でMemory一覧表示・削除UIを追加

```text
「覚えていることを見せて」「記憶一覧」のような発話で、保存済みMemoryをID付きで一覧表示できるようにした
（read-onlyのため確認不要。既存のget_memories()をそのまま使う）
「(番号)の記憶を削除して」のような発話で、指定IDのMemoryを削除できるようにした。
「削除」は物理削除ではなく、既存のset_memory_active(id, False)による非破壊的な無効化（元に戻せる）
削除は他のReaderと同じ確認フローを通してから実行する（ユーザーの「削除の実行は都度確認」という
要望に沿った設計）。確認判定はconfirmation_intent.pyのハイブリッド方式をcontext_type="memory_delete"
として再利用した
「このファイルを削除して」のような無関係な削除依頼と衝突しないよう、削除動詞と「記憶」「Memory」への
言及の両方が含まれる場合のみ削除意図として扱う
core/memory_management_intent.py（意図判定）と core/memory_management.py（一覧表示・確認メッセージ・
削除結果表示）を追加
core/personal_ai.py に self.memory_deactivator（デフォルトはset_memory_active）を追加し、
handle_pending_memory_delete_confirmation()から呼び出す。属性未設定のtest doubleは暗黙にDBへ
書き込まない設計（Ver2.51/2.52と同じパターン）
一覧表示（get_memories/get_memory_by_id）はread-onlyのため、既存のbuild_messages()と同じく
DI無しで直接呼び出す。書き込み（set_memory_active経由の無効化）だけをDI対象にした
scripts/check_ver2530.py を追加。本番DBには一切触れず、独立したin-memory SQLiteで実際のSQL動作を検証する
scripts/run_ver2_checks.py に check_ver2530.py を追加
Memoryの内容自体を書き換える「編集」機能は今回のスコープに含めない（より複雑なUX設計が必要なため、
別途検討する）
```

Ver2.54でOpenAI vision接続（月間予算ガード付き）を追加

```text
ユーザーとOpenAIアカウント設定を一緒に実施（プリペイド式クレジット$5購入、Auto rechargeはOFF、
APIキーはsetxでユーザー環境変数として設定済み）。実際の課金は発生済みだが、コード側は
まだ実際のAPI呼び出しをしていない（fakeのclient_factory経由のテストのみ）
database/models.py に OpenAIUsageLog テーブルを追加
database/openai_usage.py に record_openai_usage() / get_monthly_openai_usage_total() を追加
ai/openai_client.py を追加。describe_image_with_openai()は、呼び出し前に必ず今月の想定利用額
（PersonalAI側の概算値）が上限未満かを確認し、上限到達時は実際の呼び出し自体を行わずに
例外を送出する（デフォルト上限$5。ユーザーとの合意額）
core/vision_router.py の choose_vision_backend() を実装。デフォルトは常にlocalで、
ユーザーが「OpenAIで解析して」のように明示的に求めた場合のみOpenAIへエスカレーションする
（画像の難易度を自動判定してのエスカレーションはまだ実装しない。外部送信・課金を伴うため、
ユーザーの明示的な意図がある場合に限定）
core/image_reader_adapter.py の_describe_image()にOpenAI分岐の実装を追加
requirements.txt に openai==2.43.0 を追加
scripts/check_ver2540.py を追加。実際のOpenAI API呼び出しは一切行わず、fakeのclient_factoryと
独立したin-memory SQLiteで、エスカレーション判定・予算ガード・Image Reader結合を検証する
scripts/run_ver2_checks.py に check_ver2540.py を追加
実際のライブAPI呼び出しでの動作確認は、ユーザーとの合意のもとで別途実施する
```

Ver2.55でImage Readerの自動OpenAIエスカレーションを追加

```text
ユーザーから「将来的には明示的に求めなくてもPersonalAIが必要なタイミングを判断してOpenAIを
呼び出してほしい」との要望があり、月間予算ガード（Ver2.54）が既にあることを踏まえて実装した
core/vision_router.py に should_escalate_after_local_result() を追加。ローカルvisionモデルの
解析結果に「わかりません」「判断できません」などの低信頼な表現が含まれる場合、自動的に
OpenAIへの再解析を試みる（ユーザーが明示的にOpenAIを指定する既存の仕組みは維持）
core/image_reader_adapter.py の_describe_image()を、まずローカルで解析→低信頼ならOpenAIへ
自動エスカレーション、という流れに変更。予算超過・キー未設定などでOpenAIが使えない場合は、
エスカレーションを試みず、ローカルの結果をそのまま正直に返す（silent fallback、失敗として扱わない）
実際に使われたバックエンド（local/openai）をToolResultに正確に記録するよう変更した
（以前はエスカレーション前に選んだバックエンドをそのまま記録していた）
scripts/check_ver2550.py を追加。実際のOpenAI API呼び出しは一切行わず、fakeのclient_factoryと
独立したin-memory SQLiteで、低信頼判定・自動エスカレーション・予算超過時のフォールバックを検証する
scripts/run_ver2_checks.py に check_ver2550.py を追加
```

Ver2.56でReader経由のテキスト応答にも自動OpenAIエスカレーションを追加

```text
ユーザーから「画像検索以外でもエスカレーション機能は実装してください」との要望があり、
Image Reader（Ver2.55）と同じ考え方をテキスト応答にも展開した
core/confidence_check.py を新設し、低信頼判定ロジック（LOW_CONFIDENCE_MARKERS /
seems_low_confidence）をvision_routerとテキスト応答で共有するようにした
（core/vision_router.py の should_escalate_after_local_result() はこの共有関数を呼ぶだけに変更）
ai/openai_client.py に ask_openai_text() を追加（describe_image_with_openai()と同じ
budget guardパターン。featureタグは"text_escalation"、想定コストはgpt-4o-miniで$0.005/回）
core/personal_ai.py の build_document_task_response_if_requested()
（Reader経由の要約・質問への回答、Ver2.40で問題が見つかったExcel集計質問などが対象）を、
まずQwenで回答→低信頼ならOpenAIへ自動エスカレーション、という流れに変更
予算超過・キー未設定などでOpenAIが使えない場合は、エスカレーションを試みず、Qwenの回答を
そのまま正直に返す（silent fallback、失敗として扱わない）
self.openai_text_client_factory（デフォルトNone、ai/openai_client.py内の実際のOpenAI呼び出しを使う）
を追加。属性を明示的に確認せず使う既存test doubleでも、低信頼にならない通常の応答では
問題なく動作することを確認した
通常会話（雑談等）やconfirmation intent判定など、他の場所へのエスカレーションはまだ拡張していない。
Reader経由の要約・質問への回答に限定したスコープ
scripts/check_ver2560.py を追加。実際のOpenAI API呼び出しは一切行わない
scripts/run_ver2_checks.py に check_ver2560.py を追加
```

Ver2.56でOpenAI連携の最終ゴールをユーザーとすり合わせ、Ver2.57でTier3エスカレーションを追加

```text
OpenAI接続を機に、ユーザーとPersonalAIの最終ゴールについて具体的にすり合わせた
（詳細はdocs/final_product_vision.md 11章）。要点:
- ゲーム開発はClaude Codeのように設計相談後は自律実装（Unity/Blender直接操作含む）してほしい
- Web検索による自律的な知識蓄積を中核機能にしたい
- 創作・技術ツールの操作は固定モードではなく、できることをなるべく増やす方針
- 既存AI（ChatGPT/Claude Code）の機能を土台に、自動実行・PC自由操作・画面共有・
  能動的な話しかけ/作業開始を差別化点にしたい（いずれも要安全設計、着手時に別途相談）
- 効率的な設計でコストを抑えつつ性能を上げる（3段階モデル活用と対応）

このすり合わせを受けて、Ver2.55/2.56で作ったTier1(Qwen)↔Tier2(OpenAI安価モデル)の
エスカレーションに、Tier3（高性能モデル、gpt-4o想定・モデル名は要検証）を追加した。
画像解析・テキスト応答の両方で、Tier2の回答も低信頼ならTier3へ自動エスカレーションする。
Tier3が使えない場合は、Tier2の結果へ正直にフォールバックする。
ai/openai_client.py の describe_image_with_openai() / ask_openai_text() に
feature/estimated_cost_usdの上書きパラメータを追加し、Tier3呼び出しの利用記録を
Tier2と区別できるようにした（既存呼び出しはデフォルト値のまま変更なし）。
scripts/check_ver2570.py を追加。実際のOpenAI API呼び出しは一切行わない。
```

Ver2.58でWeb検索が必要な質問への対応を追加

```text
core/web_search_intent.py の needs_web_search() を新設。最新情報・時事的な表現
（「最新」「今日の」「ニュース」等）や明示的な検索依頼（「調べて」「検索して」等）を
キーワードで判定する。Tierエスカレーション（低信頼を検知してから遡る）とは異なり、
質問の時点で判定し、最初からOpenAIのWeb検索機能（responses APIのweb_searchツール、
Ver2.58時点では未検証）へ直接渡す設計にした。
ai/openai_client.py に ask_openai_with_web_search() を追加（同じbudget guardパターン、
featureタグ"web_search"）。personal_ai.py の capability_analysis チェック直後、
通常会話フローに入る前に判定するよう組み込んだ。
予算超過・キー未設定などでOpenAIが使えない場合は、検索できない旨を正直に伝える
（調べたふりはしない）。
ユーザーから「検索はOpenAI、回答生成はQwenに分離できないか」という提案があった。
実現できるかは実際にAPIを叩いて応答形式を確認してから判断する（現時点では一括呼び出し）。
また「機能ごとに最適なモデルを個別に割り当てる」という原則も共有され、
docs/final_product_vision.md 6章に記録した。
scripts/check_ver2580.py を追加。実際のOpenAI API呼び出しは一切行わない。

--- 実API検証による追記（課金設定完了後）---
ユーザーの課金設定完了を受け、初めて実際のOpenAI APIでテキスト呼び出し・Web検索呼び出しを
検証した（最小コストのみ、check scriptは引き続きfakeのみ使用）。以下2件の実バグを発見・修正:
1. Web検索: tool_choiceを明示しないと、曖昧な短い質問でモデルが検索を省略し古い情報で
   答えることがあった → tool_choice={"type": "web_search"}を強制するよう修正
2. gpt-5.5等の新しいモデルはmax_tokensではなくmax_completion_tokensを要求する →
   text/vision呼び出し両方にフォールバックを追加
gpt-5.5の実在を確認できたため、Tier3のDEFAULT_POWERFUL_TEXT_MODEL/VISION_MODELを
gpt-4oからgpt-5.5に更新（テキストのみ実確認、visionは同じ修正を共有のため未確認だが動作見込み）。
```

Ver2.59でOpenAI vision（画像入り）の実API検証を実施

```text
Ver2.58ではテキスト・Web検索のみ実API検証済みで、visionはコード修正を共有しているだけの
未検証・動作見込みの状態だった。テスト用画像（赤い正方形・青い円、Ver2.47の手動テストと
同じ構図）をローカルで生成し、describe_image_with_openai()をTier2（gpt-4o-mini）・
Tier3（gpt-5.5）の両方で実際に呼び出した。
両モデルとも画像内容を正しく説明する応答が返り、Tier3のmax_completion_tokensフォールバックも
visionで問題なく動作することを確認した。実際のコードバグは見つからなかった
（PowerShellのコンソール出力がcp932のため日本語レスポンスの表示が文字化けする現象があったが、
これは表示上の問題であり、UTF-8でファイルへ書き出した内容自体は正しかった）。
ai/openai_client.pyのDEFAULT_POWERFUL_VISION_MODELのコメントを「未検証だが動作見込み」から
「Ver2.59で実API確認済み」に更新した。
検証にかかった実費用は月間上限$5のうち約$0.05程度。
scripts/check_ver2590.py を追加。実際のOpenAI API呼び出しは一切行わない。
```

Ver2.60で通常会話への自動OpenAIエスカレーション拡張を実施

```text
これまでの自動エスカレーション（Ver2.55画像、Ver2.56/2.57テキスト）はReader経由の
要約・質問に限定されており、通常会話（雑談・質問・提案依頼など）には適用されていなかった。
最上位方針（final_product_vision.md 1章）の「精度最優先」に沿って対象を拡張した。
core/personal_ai.pyに_is_qwen_free_form_answer(plan, route)を追加し、Planner/Routerの
判定結果からQwenが自由生成した回答（chat/recommend/answer_question等）だけを
エスカレーション対象にする。ask_clarificationや各種unsupported/summarize系の固定案内文は
対象外にし、無駄なOpenAI呼び出しを避ける。
handle_user_input()の最後で、この判定を通してから既存の_escalate_text_answer_if_low_confidence()
（Tier2→Tier3の順に自動エスカレーションする既存ロジック）にそのまま渡すよう変更した。
新しいエスカレーションロジックは追加しておらず、既存の低信頼判定・budget guard・
silent fallbackをそのまま再利用しているため、動作の一貫性は既存のReader経由エスカレーションと同じ。
scripts/check_ver2600.py を追加。実際のOpenAI API呼び出しは一切行わない。
```

Ver2.61でMemory編集機能（内容の書き換え）を追加

```text
Ver2.53では「より複雑なUX設計が必要」として対象外にしていた、Memory内容自体の書き換え機能を実装した。
「(番号)の記憶を編集して」→新しい内容の入力→変更前後を並べた確認→実行、の2段階確認フローにした。
core/memory_management_intent.pyにdetect_memory_edit_request()を追加し、削除判定と同じく
「記憶」「Memory」への言及と編集動詞の両方が揃った場合のみ編集意図として扱う。
core/memory_management.pyにbuild_memory_edit_prompt() / build_memory_edit_confirmation() /
resolve_memory_edit_confirmation_response() / build_memory_edit_result_response()を追加し、
core/confirmation_intent.pyにcontext_type="memory_edit"を追加して、他のReader・Memory削除と
同じハイブリッド確認判定を再利用した。
database/memory_manager.pyにupdate_memory_content()を追加。物理削除ではなく、既存レコードの
contentだけを上書きする（書き換え前の内容は保持しない）。
core/personal_ai.pyにself.memory_content_updater（デフォルトは実際のupdate_memory_content）を
追加し、属性未設定のtest doubleは暗黙にDBへ書き込まない設計にした（memory_deactivatorと同じパターン）。
scripts/check_ver2610.py を追加。本番DBには一切触れず、独立したin-memory SQLiteで検証する。
```

Ver2.62で実機テストにより見つかった3件の不具合を修正

```text
ユーザーがVer2.60/2.61の会話フローを実機で試した結果から、以下3件の不具合を発見・修正した。
1. [最重要] 「記憶」という語を含まない削除依頼（例:「６を削除して」）は意図検出の対象外
   （設計通り）で通常会話に流れるが、Qwenが実際には何も削除していないのに「削除しました」と
   回答してしまう事象があった。DBを確認し実際には削除されていないこと（捏造回答）を確認した。
   ai/llm.pyのSYSTEM_PROMPTに、実行していない操作を実行したかのように答えない旨を追加した。
2. [中] memory_keyなしの過去レコードとmemory_keyつきの新しい保存経路が、同じcategory
   （好きな食べ物など）でも別レコードとして重複し続けるバグがあった。
   database/memory_manager.pyのsave_memory()に、memory_keyで見つからない場合の
   category単位フォールバック検索を追加した。
3. [軽微] capability_managerの「このファイル」等の素の言及判定が、削除・編集依頼にも
   誤反応し、無関係なReader未実装の定型応答を返す問題があった。
   _has_non_reading_action_intent()ガードを追加し、削除・編集動詞がある場合は
   素の言及だけでは即座にtrueにしないよう修正した。
この挙動変更に伴い、scripts/check_ver2530.py / scripts/check_ver2610.pyのテスト用
PersonalAIインスタンスにPlanner/Router/PermissionManager/Executorを追加し、
core.executor.ask_llmをfakeに差し替えて実際のQwen呼び出しを避けるよう更新した。
scripts/check_ver2620.py を追加。
```

Ver2.63で商品・価格・実在リンクの断定回答を修正

```text
実機テストで、「予算20万円のPCが欲しい」「具体的な構成例と実際の商品を教えて」に対し、
Web検索なしにQwenが実在しないAmazon/Yodobashiリンク、古い価格、内部矛盾のあるパーツ構成を
断定的に提示する事象が見つかった。
core/web_search_intent.pyのneeds_web_search()にPRODUCT_AND_PRICING_MARKERS
（価格・予算・在庫・リンク・BTO・比較・ランキング・セール・実際の商品等）を追加し、
これらの質問はVer2.58と同じ経路でOpenAI Web検索へ渡すようにした。
用途・予算が未確定な最初の漠然とした相談は、Qwenが聞き返す既存の良い挙動を壊さないよう
あえて対象外のままにした。
ai/llm.pyのSYSTEM_PROMPTに、機能個別ではなく抽象度を上げた一般原則として、根拠のない
具体的事実（商品名・価格・URL等）を断定しないこと、確信度を区別することを追加した。
一般知識の細部不正確さはQwen(8B)自体の能力限界に起因する部分が大きく、今回では
完全には解決しない（ModelRouterでの高精度モデルエスカレーション拡大が本質的な対応）。
ユーザーから、キーワード羅列よりLLM解釈でツール選択すべきという指摘があり、これは
docs/llm_intent_resolver_design.md（Ver2.26）の既存方針と一致する。ただしneeds_web_search()は
毎ターン呼ばれるため、LLM解釈への置き換えはレイテンシ影響を見極めてから別Verで検討する。
scripts/check_ver2630.py を追加。
```

Ver2.64で解釈層全体のレイヤードパイプライン設計をdocs化

```text
Ver2.62/2.63の実機バグ修正をきっかけに、解釈層（意図判定）全体の設計をユーザーとすり合わせた。
input_analyzer.py/capability_manager.py/tool_request_builder.pyに「文書作成/読み取りが必要か」の
判定が重複していること、LLMフォールバックを持つのはconfirmation_intent.pyだけであることを監査で確認した。
処理パイプライン（入力→解釈→記憶検索→統合→計画→作業→検証→出力→記憶）を、毎回全レイヤーを
順番に通すのではなく入力の性質に応じて必要なレイヤーだけを通る条件付きルーティングにする方針、
解釈対象を安全確認系（変更しない）とルーティング分類系（対象）に分ける方針を明記した。
ルーティング分類系はStage1（重複統合）→Stage2（ハイブリッド化）→Stage3（学習型キーワード記憶、
既存Memory機構に相乗り、完全一致ベース）の段階で進める。言い換え対応にはベクトルDBが必要だが、
実装は必要性が高まった時点まで見送る方針でユーザーと合意した。
検証層（操作実行や具体的事実の主張がある場合だけ条件付き発動）の設計も明記した。
docs/llm_intent_resolver_design.mdに追記。コード実装は行っていない。
```

Ver2.65でエスカレーション条件・検証層・コストガバナンスの詳細をユーザーとすり合わせ

```text
エスカレーションは質問内容での事前一括判断ではなく、各層が自分の担当作業をQwenで
処理できるか個別に判断する設計にする方針を明記した（機能単位モデル選択をレイヤー単位まで
徹底）。トリガーは検証層の信頼度判定・時間経過・作業難易度の3種類を併用する。
検証層を検証層A（内容検証・グラウンディング確認）と検証層B（実行ログとの整合性チェック、
Ver2.62のSYSTEM_PROMPT努力目標を将来構造化する）に分ける方針を明記した。
検証で問題が見つかった場合は、再生成の見込みがあれば再生成し、難しければ正直に
「確認できませんでした」と伝える方針とした。
層単位エスカレーションで増えるOpenAI呼び出し頻度に対応するコストガバナンス方針
（1ターンあたりの呼び出し上限、利用額の可視化、月間上限到達前の事前警告）も明記した。
コード実装は行っていない。
```

Ver2.66でStage 1（重複キーワード統合）を実装

```text
input_analyzer.py/capability_manager.py/tool_request_builder.pyに重複していたキーワード
リストのうち、複数ファイルで実際に一致していた部分をcore/reading_keywords.pyに共通定数
として切り出した。3ファイルのリストは完全同一ではなかった（呼び出し文脈ごとの意図的な
違いがあった）ため、無理な統合はせず共通部分だけを抽出し、各ファイルは独自キーワードを
追加する形にした。各ファイルの実効キーワード集合がリファクタリング前後で完全一致する
ことを集合比較で検証し、挙動・レイテンシは変更していない。
scripts/check_ver2660.py を追加。
```

Ver2.67でWeb検索/回答生成の分離可否を実APIで調査し、結論を確定

```text
Ver2.58で保留にしていた「検索はOpenAI、回答生成はQwenに分離してコストを抑えられないか」を
実APIで調査した。web_search_call項目は検索クエリのみでsourcesは常にnull、実質的な回答内容と
引用元URLはmessage項目に合成済みの形でしか存在せず、Qwenが再構成できる生データを
取り出す方法がないことを確認した。分離は技術的に実現不可能と判断し、一括呼び出しのまま
維持する方針を確定した（追加のコード変更なし）。
ai/openai_client.pyのask_openai_with_web_search()docstringを調査結果で更新した。
scripts/check_ver2670.py を追加。
```

Ver2.68でStage 2（ルーティング分類のハイブリッド化）を実装

```text
capability_manager.analyze()とweb_search_intent.needs_web_search()に、
confirmation_intent.pyと同じハイブリッド判定（固定語彙優先、不明時のみLLM）を追加した。
既存キーワードにどれも一致しない場合のみQwenに1語で判定させ、LLMの応答が不明瞭・
呼び出し失敗の場合は安全側に倒して従来の挙動にフォールバックする。ask_llm_funcを
渡さない既存呼び出し元は暗黙にLLMを呼ばず今まで通り動作し、既存の全チェックは無変更で通過した。
監査の結果、core/tool_request_builder.py（core/tool_flow.py経由）は現在の会話フローに
一切接続されていない不使用コードであることが分かった。今回は対象外とし、削除・再利用は
別途ユーザーと相談する。
キーワード不一致時は1往復分レイテンシが増えるが、最終UI（通知つきチャットアプリ）では
許容範囲とユーザーから確認済みのため追加の緩和策は取らない。
scripts/check_ver2680.py を追加。
```

Ver2.69で不使用コード（tool_request_builder.py/tool_flow.py）を削除

```text
Ver2.68のStage 2作業中に、core/tool_request_builder.py（core/tool_flow.py経由）が
現在の会話フローに一切接続されていない、Ver1.6〜1.10時代のdry-run実装だと判明した。
今のルーティング判断はcapability_manager.py（Ver2.68でハイブリッド化済み）と各Readerの
専用confirmationモジュールが担っている。
tool_adapter.py/tool_registry.py/tool_execution_log.py/tool_runner.py/tool_permission.pyは
tool_flow.py経由ではなく独立して使われている現役コードであることを確認し、削除対象から除外した。
2ファイルを参照していた8本の既存チェック（check_ver160/170/180/190/1100/200/2300/2660）を
外科的に修正した。全機能を不使用コードに依存していたcheck_ver160.pyのみ削除し、他は該当箇所
だけ削除・書き換え。既存の全チェック（Ver1: 12本、Ver2: 70本）が引き続き通ることを確認した。
scripts/check_ver2690.py を追加。
```

Ver2.69後の候補:

```text
Ver2.x: 検証層B（実行整合性チェック）の実装
Ver2.x: README用スクリーンショット/GIF追加（提出が近づいたタイミングで対応）
```

Ver2.70で検証層B（実行整合性チェック）を実装

```text
通常会話（Executor経由のQwen自由生成）は記憶の削除・編集・保存を実際には一切実行しないため、
Ver2.62で見つかったような「実行していない操作を実行したと捏造する」問題への構造的な対策として、
core/execution_claim_check.pyのcontains_unverified_action_claim()を追加した。
「記憶」への言及と操作完了表現（削除しました/編集しました/保存しました等）の両方を含む場合のみ
反応する（無関係な「ファイルを保存しました」等には反応しない）。
handle_user_input()の自由回答経路で、Tierエスカレーション後にこの判定を通し、該当する場合は
本文を書き換えずに「この会話の中では実際に実行する仕組みは動いていません」という正直な注記を
追記する。完全一致検知の限界により、過去の実行済み操作を正しく振り返る発言にも注記が付く
場合があるが、注記自体は常に事実であるため誤りにはならない。
scripts/check_ver2700.py を追加。
```

Ver2.70後の候補:

```text
Ver2.x: 検証層A（内容検証・グラウンディング確認）の実装検討
Ver2.x: README用スクリーンショット/GIF追加（提出が近づいたタイミングで対応）
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
