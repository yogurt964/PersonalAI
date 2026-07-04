# MIGRATION.md

## 1. このドキュメントの目的

このドキュメントは、PersonalAI開発を新しいAIエージェント環境へ移行するための引継書である。

移行先は主に Claude Code を想定する。
Cursor は、視覚確認用エディタとして併用する。

ユーザーはコード差分の細部確認ではなく、動作結果、使いやすさ、ポートフォリオとしての見え方、不可逆操作の承認を担当する。
AIエージェントは、実装、チェック、修正、docs更新、commit、pushまで自走する。

README.md はGitHub閲覧者・就活ポートフォリオ向けである。
AGENTS.md はAIエージェント向けの短い運用ルールである。
docs/development_workflow.md は開発方針の詳細である。
MIGRATION.md は Claude Code / Cursor など別環境へ移行するための包括的な引継書である。

## 2. プロジェクト概要

```text
プロジェクト名: PersonalAI
ローカルパス: C:\AIProject\PersonalAI
GitHub: https://github.com/yogurt964/PersonalAI.git
```

PersonalAIは、ローカルLLMとPythonを使った個人AIアシスタントである。

主な目的:

- 長期記憶
- Web Reader
- Memory Candidate
- PermissionManager
- ToolRunner
- 安全な確認フロー
- 将来的なAIエージェント化

最終ゴールは、ユーザーの意図を理解し、情報を読み、記憶し、安全に作業を支援するAIに育てることである。

## 3. 現在の開発環境

現在の開発環境:

- Windows
- PowerShell
- VS Code
- Git / GitHub
- Python venv
- Python 3.10.11
- Ollama / Qwen
- Codex

今後の移行候補:

- Claude Code
- Cursor

## 4. 新環境の役割分担

### Claude Code

Claude Codeは、メインの自走エージェントとして扱う。

担当:

- ファイル読み書き
- ターミナル実行
- テスト実行
- エラー検知
- 自己修正
- docs更新
- 次Ver実装
- git add
- git commit
- git push

### Cursor

Cursorは、視覚確認用エディタとして扱う。

担当:

- README表示確認
- UI確認
- ゲーム/アプリ画面確認
- Jupyterやグラフ確認
- Claude Codeが見えない部分の補助

### ユーザー

ユーザーは、実用面の確認と高リスク判断を担当する。

担当:

- 実際の動作確認
- AIの返答が自然か確認
- ポートフォリオとして見せられるか確認
- 不可逆操作への承認
- 課金・外部送信・DB破壊などへの承認

## 5. 技術スタック

現在:

- Python 3.10.11
- SQLite
- SQLAlchemy
- Ollama
- Qwen
- PowerShell
- Git / GitHub

将来候補:

- OpenAI API
- Claude
- Gemini
- ModelRouter
- ToolRouter

現時点では OpenAI / Claude / Gemini 接続は未実装である。

## 6. ディレクトリ構成

```text
ai/
core/
database/
docs/
docs/demo_logs/
scripts/
data/
README.md
AGENTS.md
MIGRATION.md
app.py
```

主要ファイル:

```text
app.py: CLI起動入口
ai/llm.py: Qwen呼び出しとSYSTEM_PROMPT
ai/memory_context.py: MemoryContext生成
ai/memory_extract.py: 汎用記憶抽出
ai/memory_usage_policy.py: Memory利用方針判定
ai/conversation_quality_policy.py: 会話品質方針判定
core/personal_ai.py: PersonalAI本体
core/input_analyzer.py: 入力分類
core/capability_manager.py: Capability判定
core/planner.py: 行動計画
core/router.py: 実行先選択
core/executor.py: 実行入口
core/permission_manager.py: Permission / Risk判断
core/tool_runner.py: ToolRunner
core/web_reader_adapter.py: Web Reader
core/confirmation_intent.py: 確認待ち状態のIntent解釈
core/web_reader_confirmation.py: Web Reader確認応答
core/memory_candidate.py: Reader結果からMemory Candidateを作る
core/memory_candidate_confirmation.py: Memory Candidate確認応答
core/memory_candidate_saver.py: Memory Candidate保存
core/memory_search.py: Memory検索
database/models.py: DBモデル
database/memory_manager.py: Memory保存・取得・状態変更
database/chat_history.py: 会話履歴保存・取得
docs/project_handoff.md: 引継ぎ用まとめ
docs/development_workflow.md: 開発自走方針
docs/check_workflow.md: check運用
docs/final_product_vision.md: 完成形ビジョン
docs/conversation_policy.md: 会話方針
docs/reader_memory_policy.md: Reader結果のMemory保存方針
docs/memory_candidate_ui_policy.md: Memory Candidate確認UI方針
docs/demo_logs/web_reader_memory_candidate_demo.md: デモログ
scripts/run_ver2_checks.py: Ver2.x標準チェック
```

## 7. 現在の実装済み機能

現在できること:

- Qwen / Ollamaを使った会話
- 会話履歴
- 長期記憶基盤
- InputAnalyzer
- Planner / Router / Executor
- PermissionManager
- ToolRunner
- Web Reader
- Web Reader実行前確認
- 確認待ち状態の文脈解釈
- Memory Candidate生成
- Memory Candidate dry-run表示
- Memory Candidate確認応答
- Memory Candidate編集dry-run
- Memory Candidateユーザー確認つき保存
- 直近保存Memory確認
- Memory検索
- ポートフォリオREADME
- デモログ
- 開発自走方針

Ver2.20時点では、以下の流れが一通り動く。

```text
URL入力
→ Web Reader実行前確認
→ いいよ / お願いします などの確認応答
→ Web Reader実行
→ Memory Candidate生成
→ 保存する
→ 長期記憶へ保存
→ 今保存した記憶を確認して
→ 直近保存Memory表示
→ Example Domainについて覚えてる？
→ 保存済みMemory検索
```

## 8. 現在できる代表的なデモ

### Web Reader → Memory保存 → 直近確認

```text
このURLを読んで https://example.com
いいよ
保存する
今保存した記憶を確認して
```

期待される動作:

- Web Reader確認
- 読み取り
- Memory Candidate表示
- 保存
- 保存内容プレビュー
- 直近保存Memory表示

### Memory検索

```text
Example Domainについて覚えてる？
```

期待される動作:

- 保存済みMemoryを検索
- 関連Memoryがあれば表示
- なければ自然に未発見を返す

## 9. PersonalAIの最終利用スコープ

この章は、現在実装済みの機能ではなく、将来的にPersonalAIで扱いたい利用範囲を整理するものである。

現在実装済み:

- Web Reader
- Memory Candidate
- Memory Candidateのユーザー確認つき保存
- 直近保存Memory確認
- Memory検索
- PermissionManager
- ToolRunner

将来スコープ:

- 画像、音声、動画などの入力
- YouTube、PDF、Word、Excel、PowerPointなどのReader
- Office操作、カレンダー連携、メール連携
- アプリ開発、ゲーム開発、創作支援、データ分析、予定管理
- コードエディタ、ゲームエンジン、イラスト制作ソフト、動画編集ソフト、音楽制作ツール、ノートアプリなどとの連携

PersonalAIは、単なるチャットAIや開発補助AIではなく、ユーザーの日常・学習・開発・創作・予定管理まで広く支援する個人用総合AIアシスタントを目指す。

### 主な使用場面

- アプリ開発
- ゲーム開発
- 資料要約
- 資料作成
- Web検索
- データ分析
- 勉強
- 雑談
- アドバイス
- Live2D
- 動画制作
- イラスト
- 3Dモデリング
- 音楽制作
- 動画生成
- 画像生成
- 予定管理
- メール

### 将来的に扱いたい入力

- 画像
- 音声
- 動画
- YouTube
- URL
- PDF
- Word
- Excel
- PowerPoint
- 日本語文章
- 英語文章
- コード
- アプリ画面
- カレンダー
- メール
- Obsidianなどのノート

### 将来的に連携・支援したい外部ツール

PersonalAIは、将来的にコードエディタ、ゲームエンジン、イラスト制作ソフト、動画編集ソフト、データ分析ツール、Office系ツール、ノートアプリ、画像生成ツール、動画生成ツール、音楽制作ツールなどの支援を視野に入れる。

以下の具体名は、固定ではない。
あくまで各分野で想定される代表例・候補例であり、実際に使うツールは用途や開発段階に応じて選ぶ。

#### 開発

- VS Code
- Unity
- コードエディタ
- ゲームプラットフォーム

#### イラスト・創作

- CLIP STUDIO PAINT / クリスタ
- MediBang
- Live2D
- 3Dモデリングツール
- 画像生成ツール
- 動画生成ツール
- 音楽制作ツール

#### 動画制作

- DaVinci Resolve
- Adobe系ツール

#### データ分析

- R
- 表計算
- グラフ作成

#### 資料・業務

- Office
- Word
- Excel
- PowerPoint
- カレンダー
- メール
- Obsidian

### 利用するAI

現時点で主に想定しているAI:

- Qwen
- OpenAI

将来的には、用途に応じてClaudeやGeminiなども候補にできる。

ただし、Claude Codeは開発環境としての利用を想定しており、PersonalAI本体の実行モデルとして使うかは別途判断する。

## 10. 未実装機能

未実装:

- PDF Reader
- Image Reader
- YouTube Reader
- File Reader
- LLM Intent Resolver
- ModelRouter
- ToolRouter
- OpenAI / Claude / Gemini 接続
- GUI
- PC操作
- Word / Excel / PDF作成
- Memoryの本格検索
- ベクトル検索
- Memory編集UI
- Memory削除UI
- 自己アップデート
- 自律調査

未実装機能は、できるように見せない。
必要な場合は未実装であることを明確に伝え、代替案を出す。

## 11. 安全ルール

必ず守ること:

```text
data/personal_ai.db を削除しない
DB初期化しない
DBスキーマ変更は計画なしにしない
Memory物理削除は禁止
force push禁止
reset --hard禁止
rebase禁止
Git履歴書き換え禁止
APIキーや個人情報を外部送信しない
課金・契約・購入はユーザー確認
PermissionManagerを勝手に弱めない
安全チェックを削除しない
```

通常は確認不要:

```text
コード修正
docs更新
テスト追加
軽いリファクタリング
git add
git commit
git push
branch作成
通常merge
修正用commit
```

判断に迷う場合は、AGENTS.md と docs/development_workflow.md を優先する。

## 12. 開発・検証コマンド

起動:

```powershell
venv\Scripts\python.exe -B app.py
```

Ver2.x標準チェック:

```powershell
venv\Scripts\python.exe -B scripts\run_ver2_checks.py
```

直近Ver固有チェック例:

```powershell
venv\Scripts\python.exe -B scripts\check_ver2200.py
```

Git確認:

```powershell
git status
git log --oneline -5
git diff --check
```

通常実行でSQLite disk I/O errorやtimeoutが出ることがある。
DB削除・初期化はしない。
権限付き再実行で通る場合は、既知の環境問題として扱う。

## 13. Claude Code開始時の手順

Claude Codeが最初に行うこと:

```powershell
git status
git log --oneline -5
venv\Scripts\python.exe -B scripts\run_ver2_checks.py
```

その後に読むファイル:

```text
AGENTS.md
MIGRATION.md
README.md
docs/development_workflow.md
docs/project_handoff.md
docs/check_workflow.md
```

必要に応じて読むファイル:

```text
docs/final_product_vision.md
docs/conversation_policy.md
docs/reader_memory_policy.md
docs/memory_candidate_ui_policy.md
docs/demo_logs/web_reader_memory_candidate_demo.md
```

## 14. 作業完了時の報告フォーマット

```text
【VerX.X 完了まとめ】

1. 完了した内容
2. 実際にできるようになったこと
3. 実行したチェックと結果
4. commit hash
5. git status
6. ユーザーが確認すべき動作ポイント
7. 次に進めるVer候補
```

## 15. ポートフォリオ方針

PersonalAIは就活ポートフォリオとして使う予定である。

見せ方:

- ローカルLLM
- 長期記憶
- Web Reader
- Memory Candidate
- Permission管理
- 安全設計
- GitHubでの段階的開発

未実装機能は未実装として正直に書く。

参照:

```text
README.md
docs/portfolio_notes.md
docs/demo_logs/web_reader_memory_candidate_demo.md
```

## 16. 次に進める候補

```text
Ver2.22: READMEへの画像・GIF・図の追加
Ver2.22: LLM Intent Resolver設計
Ver2.22: File Reader最小実装
Ver2.x: PDF Reader
Ver2.x: Memory検索の改善
Ver2.x: Claude Code移行テスト
```
