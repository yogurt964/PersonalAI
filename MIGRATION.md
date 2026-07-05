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
docs/claude_code_start.md は Claude Code 移行時に最初に読む短い開始手順である。
MIGRATION.md は Claude Code / Cursor など別環境へ移行するための包括的な引継書である。

Claude Codeが日常的にVer単位で自走開発するときの入口は `CLAUDE.md` である。
`CLAUDE.md` / `AGENTS.md` / `MIGRATION.md` / `README.md` の役割分担は以下の通りである。

- `CLAUDE.md`: Claude Code向けの短い運用ルール
- `AGENTS.md`: AIエージェント共通の運用ルール
- `MIGRATION.md`: 移行用の包括的な引継ぎ
- `README.md`: GitHub閲覧者・ポートフォリオ向け概要

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

## Qwen / OpenAIの利用方針

PersonalAIは、現時点ではQwen / Ollamaを中心に、ローカル・低コストで開発している。

ただし、将来的にはOpenAIを利用する可能性が高い。

OpenAIは、以下のような高精度処理や実用化段階での利用候補である。

- LLM Intent Resolver
- Memory抽出・分類・要約の高精度化
- PDF / Word / Excel / PowerPointなどの資料読解
- 複雑なコード読解
- Web検索結果の要約・判断
- ToolRouter / ModelRouterの判断精度向上
- 就活ポートフォリオとしての完成度向上
- Qwenでは品質が不足する場面の補助

一方で、OpenAI APIの利用は外部送信や課金を伴う可能性がある。

そのため、以下は必ずユーザー確認を取る。

- OpenAI APIキーの設定
- OpenAI APIへの実データ送信
- 有料API利用
- 継続的なAPI利用
- 個人情報・機密情報を含むデータの送信

基本方針は、Qwen / Ollamaで進められる部分はローカルで進め、精度・安定性・開発効率・ポートフォリオ価値が明確に上がる場面でOpenAIの利用を検討することである。

OpenAIを使う場合も、無駄なAPI消費やblind retry loopは避ける。

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
docs/claude_code_start.md
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
docs/claude_code_start.md: Claude Codeへ移行する際の開始手順
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

## 11. ユーザー適応仕様

PersonalAIは、ユーザーに合わせて振る舞いを調整するAIを目指す。

単に質問に答えるだけではなく、ユーザーの目的、作業スタイル、理解度、確認の好み、過去の会話、作業履歴を踏まえて、返答や行動を調整する。

### ユーザーの開発スタイル

- ユーザーはPython / AI開発について初心者寄りであり、具体的な手順やコマンドが必要
- 一方で、コード差分の細かい確認を見せられても判断しづらい
- ユーザーへの確認は、コード詳細ではなく、動作結果・使いやすさ・自然さ・ポートフォリオとしての見え方に寄せる
- 後から修正できる通常作業はAIエージェント側で進めてよい
- 通常の実装、docs更新、テスト追加、commit、pushは自走してよい
- ユーザーは、完成物が実際に使いやすいか、自然に動くか、就活で説明しやすいかを重視する

### ユーザーが好む会話パターン

- 目的が明確な場合は、必要以上に確認せず具体的に進める
- 重要な仕様判断や致命的リスクがある操作では確認を省略しない
- 説明は段階的で分かりやすくする
- 必要なコマンドはコピペしやすく提示する
- 初心者にも理解できるように、難しい内容は噛み砕いて説明する
- 長すぎる説明やコード差分の細部説明で作業を止めすぎない
- ユーザーが知りたいのは主に「何ができるようになったか」「次に何をすべきか」「実用上問題ないか」である
- 実装確認では、コードの正しさだけでなく、実際にPersonalAIを動かしたときの自然さ・使いやすさを重視する

### AIエージェントに期待する先回り

AIエージェントは、ユーザーに言われてから不足点を補うだけでなく、必要に応じて先回りして提案・質問する。

特に以下は、AI側から積極的に確認・提案する。

- 引継ぎに不足している観点
- 将来実装で問題になりそうな設計
- ユーザーの目的とズレそうな実装方針
- ポートフォリオとして弱くなりそうな見せ方
- コストが無駄に増えそうな開発方法
- 失敗時に危険な復旧方法を選びそうな場面
- 仕様が曖昧で後から大きな手戻りになりそうな部分

ただし、質問しすぎて作業を止めるのは避ける。
必要な確認は行い、十分に判断できる場合はAI側で進める。

### ユーザーが避けたい進め方

- 毎回コード差分を貼らせて細かく確認する進め方
- commit / push のたびに確認で止まる進め方
- dry-runばかりで実機能が進まない進め方
- ユーザーに判断しづらい内部実装だけを見せる進め方
- 未実装機能を完成済みのように説明すること
- 重要な不足点をユーザーが言うまで放置すること
- 致命的リスクがある操作を勝手に行うこと

### テスト・確認の好み

ユーザーが重視するテストは、コードの内部確認よりも実用面である。

重視すること:

- AIの返答が自然か
- ユーザーの意図を正しく理解できているか
- 欲しい情報や作業結果が出ているか
- 操作の流れが使いやすいか
- 明らかな破綻や不自然な挙動がないか
- 以前より便利になっているか
- 就活ポートフォリオとして説明しやすいか

自動チェックは必要だが、ユーザーに確認してもらう内容は、実際の動作ログや使い心地を中心にする。

### 最終的なPersonalAI像

PersonalAIの最終目標は、単なるチャットボットではなく、ユーザーの作業相棒・個人秘書・自律型AIに近い存在である。

理想は、ユーザーが複数のアプリや画面を行き来しなくても、PersonalAIに依頼すれば、必要な情報の読み取り、判断、作業、資料作成、開発補助、創作補助、予定管理などをまとめて支援できる状態である。

ただし、致命的リスクがある操作は必ずユーザー確認を残す。

## 12. 就活ポートフォリオとしての目的

PersonalAIは、就活ポートフォリオとして使うことを想定している。

このプロジェクトでは、単にAIを使っているだけではなく、以下をアピールできるようにする。

- ローカルLLMを使った個人AIアシスタント開発
- 長期記憶の設計
- Web Readerの実装
- Memory Candidateの設計
- 保存前確認フロー
- PermissionManager / ToolRunner による安全な実行設計
- Git / GitHub を使った段階的な開発履歴
- README / demo log / docs による説明可能性
- AIエージェントを設計し、実装し、改善するプロセス

ポートフォリオとしての書き方:

- 実装済み機能と未実装機能を明確に分ける
- 未実装機能を完成済みのように書かない
- GitHub閲覧者や面接官が見ても分かるREADMEにする
- デモログを残し、実際にどう動くか分かるようにする
- 技術的に工夫した点を説明できるようにする
- 安全設計を強みとして説明する
- 将来構想はロードマップとして整理する

## 13. 開発コスト方針

PersonalAI開発では、基本的には低コストで進める。

ただし、ユーザーは「絶対に課金したくない」わけではない。
開発効率、AI性能、完成度、安定性、就活ポートフォリオとしての価値が明確に上がる場合は、必要な課金は許容する方針で検討する。

### 基本方針

- まずはローカル環境、Qwen、既存ツール、無料または低コストな手段を優先する
- 不要なAPI呼び出しや長時間の無駄なLLM実行は避ける
- Codex / Claude Code / OpenAI APIなどの利用量が増える場合は、目的と期待効果を明確にする
- 課金が発生する可能性がある操作は、必ずユーザーに確認する
- APIキー、外部送信、課金、契約、購入はAIエージェントが勝手に行わない

### 無駄なAPI消費を避ける方針

ユーザーは、無駄なAPI使用料やAIエージェント使用量の消費を避けたい。

特に、以下は避ける。

- 原因を調べずに同じ失敗を何度も繰り返す
- 無限ループのようにAPIやAIエージェントを回し続ける
- 失敗ログを読まずに再実行だけを続ける
- 目的が曖昧なまま高性能モデルを使う
- 安価な方法で十分な作業に高額APIを使う
- 大量の文脈を毎回無駄に読み込む
- 不要に大きいタスクを一度に投げて失敗と再試行を繰り返す

AIエージェントは、失敗した場合に以下を行う。

1. まずエラーログを読む
2. 原因を仮説立てする
3. 小さく修正する
4. 必要なチェックだけ再実行する
5. 同じ失敗が続く場合は、無限に再試行せず方針を見直す
6. 追加コストが発生しそうな場合は、ユーザーに確認する

### 必要な課金は許容する方針

ユーザーは、開発効率・AI性能・完成度・安定性・就活ポートフォリオとしての価値が明確に上がる場合、必要な課金を惜しまない。

ただし、課金前には必ず以下を説明する。

- 何に費用がかかるか
- なぜ必要か
- 無料または低コストの代替案
- 低コストの代替案で足りるか
- 課金した場合に得られる改善
- 今すぐ必要か、後回しでよいか

正しい方針は、「絶対に課金しない」でも「無制限に課金する」でもない。
基本は低コストで進め、必要な場面では理由を明確にしたうえで課金を検討する。

### 金額ラインについて

現時点では、API利用や有料ツール利用に関する具体的な金額ラインは未確定である。

有料API、従量課金モデル、追加サブスクリプション、外部サービス利用が必要になった段階で、ユーザーと以下をすり合わせる。

- 1回の試行にかけてよい上限
- 1日の上限
- 1か月の上限
- 就活ポートフォリオ完成度向上のために許容できる範囲
- 無料または低コスト代替案

金額ラインが未確定な間は、課金・契約・購入・APIキー利用・外部送信は必ず事前確認する。

## 14. 失敗時の対応方針

PersonalAI開発では、失敗そのものは問題ではない。
重要なのは、失敗時に破壊的な操作をせず、原因を切り分けて安全に修正することである。

### 基本方針

- エラーが出たら、まずログを読む
- 原因を切り分ける
- 小さく修正する
- チェックを再実行する
- 直ったらcommit / pushする
- ユーザーには原因・対応・現在状態を簡潔に報告する

### AIエージェントが自分で対応してよい失敗

以下は、通常ユーザー確認なしで修正してよい。

- Pythonの構文エラー
- import error
- テスト失敗
- docsの語句不足
- check scriptの軽微な不整合
- READMEやdocsの表現修正
- 型や引数の軽微な修正
- fakeテストの調整
- CRLF warning
- 通常のmerge conflictの安全な解消
- commit後の修正用commit
- push前の通常修正
- 後から戻せる軽微な実装ミス

### ユーザー確認が必要な失敗対応

ユーザーは細かい安全管理を最重要視しているわけではない。
ただし、以下のような致命的リスクは必ず避ける。

必ずユーザー確認を取る操作:

- PCが使い物にならなくなる可能性がある操作
- OS、レジストリ、ドライバ、環境変数、PATHなどへの大きな変更
- 大量の費用が発生する可能性がある操作
- 課金、契約、購入
- APIキーや個人情報の外部送信
- 重要データが消える可能性がある操作
- `data/personal_ai.db` の削除
- DB初期化
- DBスキーマの破壊的変更
- Memory物理削除
- 大量ファイル削除
- `reset --hard`
- `force push`
- `rebase`
- Git履歴の書き換え
- 作業内容が消える可能性がある操作
- PermissionManagerや安全チェックを大きく弱める変更

### 安全管理の優先度

PersonalAI開発では、安全管理は必要だが、開発を過度に止める目的ではない。

基本方針:

- 致命的リスクは必ず確認する
- 後から修正できるミスはAIエージェント側で進めてよい
- 軽微な手戻りや通常のバグ修正は許容する
- 安全確認を理由に、通常作業を毎回止めない
- PC破壊、大量課金、重要データ消失、外部流出、DB破壊、Git履歴破壊などは必ず防ぐ

### やってはいけない復旧方法

以下は禁止。

- エラーを直すためにDBを削除する
- エラーを直すためにDBを初期化する
- 原因不明のまま `reset --hard` する
- 原因不明のままforce pushする
- テストを通すためだけに重要な安全チェックを消す
- Memory保存やPermission確認を無効化して通す
- 未実装機能を実装済みのようにdocsへ書く
- 未実装機能を完成済みのように書かない
- 失敗を隠して成功したように報告する

### SQLite disk I/O error / timeout の扱い

開発環境では、`scripts/run_ver2_checks.py` の通常実行で SQLite disk I/O error や timeout が出ることがある。

この場合:

- DBを削除しない
- DBを初期化しない
- まず個別checkを実行する
- 権限付き再実行で通るか確認する
- 権限付き再実行で成功する場合は、既知の環境問題として扱う
- 同じエラーが再現し続ける場合は原因を調べる

### 失敗時の報告形式

ユーザーに報告する場合は、以下を簡潔にまとめる。

```text
【失敗対応まとめ】

1. 何が失敗したか
2. 原因として考えられること
3. 実施した修正
4. 再実行したチェック
5. 現在の状態
6. ユーザー確認が必要か
```

ユーザーはコード差分の詳細より、現在安全か、何が直ったか、次に何を確認すればよいかを重視する。

## 15. 移行先AIエージェントへのユーザー対応方針

Claude Codeや他のAIエージェントは、ユーザーに対して以下の方針で対応する。

- コード差分を毎回細かく見せるのではなく、完了内容・動作結果・確認ポイントを報告する
- 通常の修正、docs更新、テスト追加、commit、pushは自走してよい
- 致命的リスクがある操作は必ず確認する
- 実装後は、ユーザーが試すべき具体的な動作確認手順を提示する
- エラーが出た場合は、原因・対応・次に必要な操作を簡潔にまとめる
- ポートフォリオとして見せる観点を常に意識する
- ユーザーが初心者寄りであることを踏まえ、必要な操作はコピペしやすく書く
- ユーザーが判断しづらい内部実装の説明で止めすぎない
- ユーザーが提案する前に、必要そうな観点はAI側から先回りして提案・確認する

## 16. 安全ルール

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

## 17. 開発・検証コマンド

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

## 18. Claude Code開始時の手順

Claude Codeが最初に行うこと:

```powershell
git status
git log --oneline -5
venv\Scripts\python.exe -B scripts\run_ver2_checks.py
```

Claude Code移行時の入口として、まず `docs/claude_code_start.md` を読む。

その後に読むファイル:

```text
AGENTS.md
docs/claude_code_start.md
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

## 19. 作業完了時の報告フォーマット

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

## 20. ポートフォリオ方針

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

## 21. 次に進める候補

```text
Ver2.28: File Reader最小実装
Ver2.x: PDF Reader
Ver2.x: Image Reader
Ver2.x: YouTube Reader
Ver2.x: README用スクリーンショット/GIF追加
```
