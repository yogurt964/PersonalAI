# PersonalAI

## PersonalAIとは

PersonalAIは、ローカルLLMとPythonを使って開発している、長期記憶・外部情報読み取り・安全な確認フローを持つ個人AIアシスタントです。

単なるチャットボットではなく、ユーザーの作業を理解し、必要な情報を読み取り、記憶候補を作り、安全確認を挟みながら作業を支援するAIエージェントを目指しています。

## 開発背景

ChatGPTや開発支援AIを使う中で、会話履歴や作業文脈が切れるたびに、同じ説明を繰り返す課題がありました。

PersonalAIでは、会話履歴、長期記憶、Reader、Permission、Tool実行ログを段階的に組み合わせ、ユーザーの作業を継続的に支援できるローカルAIアシスタントを作っています。

## 目指しているもの

- ユーザーの目的を理解する
- 必要な情報を読み取る
- 長期的に役立つ情報をMemory候補として整理する
- 危険な操作や外部アクセスでは確認を挟む
- 未実装機能をできたふりしない
- ローカル環境を中心に、安全に拡張できるAIエージェントに育てる

## 現在できること

実装済みの主な機能:

- Qwen / Ollamaを使ったローカルAI会話
- 会話履歴の保存
- 長期記憶の基礎
- ユーザー入力の分析
- URL入力の検出
- Web Reader実行前の確認
- Web Readerによるページ読み取り
- 読み取り結果の整形表示
- Reader結果からMemory Candidateを生成
- Memory Candidateのdry-run表示
- 保存する / 保存しない / 編集して保存 / 後で確認 の確認応答dry-run
- Memory Candidateをユーザー確認つきで長期記憶へ保存する基礎
- 保存したMemory Candidateの内容を直近保存結果として確認する基礎
- ToolRunner / PermissionManager による安全な実行設計
- Verごとのチェックスクリプト
- 開発自走方針

まだ実装していないもの:

- Memory Candidate専用テーブル
- Reader結果全文のDB保存
- 本格的なMemory検索UI
- Memory編集・削除UI
- PDF Reader
- Image Reader
- YouTube Reader
- File Reader
- OpenAI / Claude / Gemini 接続
- GUI
- PC操作
- 自律的な外部送信
- MIGRATION.md

## 技術スタック

- Python
- SQLite
- SQLAlchemy
- Ollama
- Qwen
- PowerShell
- Git / GitHub
- ローカル実行中心のCLI構成

## アーキテクチャ概要

現在のPersonalAIは、以下のような責務分離を進めています。

```text
User Input
↓
InputAnalyzer
↓
CapabilityManager
↓
Planner
↓
Router
↓
Executor / ToolRunner
↓
Qwen / Web Reader
↓
Memory Candidate dry-run
↓
Response
```

主な構成:

- `core/personal_ai.py`: 会話処理の中心
- `core/input_analyzer.py`: 入力分類
- `core/capability_manager.py`: 現在扱える能力の判定
- `core/planner.py`: 行動計画
- `core/router.py`: 実行先選択
- `core/executor.py`: LLM実行や未実装応答
- `core/tool_runner.py`: Tool実行入口
- `core/web_reader_adapter.py`: Web Reader
- `core/memory_candidate.py`: Reader結果からMemory Candidateを生成
- `core/memory_candidate_confirmation.py`: Memory Candidate確認応答dry-run
- `core/memory_candidate_saver.py`: Memory Candidateのユーザー確認つき保存
- `database/`: 会話履歴とMemory基礎
- `docs/`: 設計方針と開発履歴
- `scripts/`: バージョンごとの自動チェック

## デモ

Web ReaderからMemory Candidate確認応答までの流れは、以下に記録しています。

- `docs/demo_logs/web_reader_memory_candidate_demo.md`

概要:

```text
ユーザー:
このURLを読んで https://example.com

PersonalAI:
Web Readerで読み取ってもよいですか？

ユーザー:
はい

PersonalAI:
Web Readerで読み取りました。
Memory Candidate dry-run:
保存候補タイプ: reader_summary
保存実行: しない

ユーザー:
保存する

PersonalAI:
Memory Candidateを長期記憶に保存しました。

ユーザー:
今保存した記憶を確認して

PersonalAI:
直近保存したMemoryは以下です。
```

このデモでは、外部Webアクセス前に確認を挟み、読み取り結果から保存候補を作り、ユーザーが明示的に保存を選んだ場合だけ既存の長期記憶保存機構へ渡し、その後に直近保存内容を確認する流れを示しています。

## 安全設計

PersonalAIでは、安全設計を初期段階から分けて考えています。

- Web ReaderはURL検出だけでは実行しない
- 外部Webアクセス前に確認する
- 失敗時に読めたふりをしない
- Memory Candidateは勝手に保存しない
- `保存する` と明示された場合だけ低リスク候補を保存する
- 保存後に直近保存内容を確認できる
- 高リスク候補は自動保存しない
- DBスキーマ変更はしていない
- PermissionManagerで高リスク操作を止める土台を用意
- DB削除、Memory物理削除、Git履歴書き換え、課金、外部送信は確認必須

## 開発プロセス

PersonalAIは、小さなバージョン単位で設計、実装、チェック、docs更新を進めています。

- `docs/changelog.md`: 変更履歴
- `docs/project_handoff.md`: 引き継ぎ用まとめ
- `docs/check_workflow.md`: チェック運用
- `docs/development_workflow.md`: AIエージェントによる開発自走方針
- `AGENTS.md`: AIエージェント向けの短い運用ルール

各バージョンで専用のcheckスクリプトを追加し、既存機能を壊さないように確認しています。

## 今後のロードマップ

近い予定:

- ポートフォリオ用READMEとデモ資料の継続改善
- Memory検索の最小実用化
- Memory Candidate保存フローの改善
- MIGRATION.md作成

将来の予定:

- PDF Reader
- Image Reader
- YouTube Reader
- File Reader
- OpenAI / Claude / Gemini 接続
- GUI
- PC操作
- Project Knowledge / Archive / User Preferenceの整理強化

## 現在の開発状況

現在はVer2.18です。

Web Reader、Memory Candidate dry-run、編集dry-run、ユーザー確認つき保存、直近保存内容の確認まで実装済みです。
ただし、Reader結果全文のDB保存、Memory Candidate専用テーブル、本格的なMemory検索UIはまだ行っていません。

このリポジトリは、就活ポートフォリオとして、AIエージェント設計、責務分離、安全設計、段階的な開発プロセスを見せることを意識して整備しています。
