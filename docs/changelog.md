# Changelog

## Version 2.21

開始内容:

- `MIGRATION.md` を追加
- Claude Code / Cursor への開発環境移行用の引継書を作成
- 実装済み機能、未実装機能、安全ルール、開発コマンドを整理
- README / project_handoff / development_workflow / check_workflow を移行方針に合わせて更新
- `scripts/check_ver2210.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver2210.py` を追加
- `MIGRATION.md` にPersonalAIの最終利用スコープを追加
- 画像、音声、動画、Office、創作支援、予定管理、メールなどは将来スコープとして整理
- 具体的な外部ツール名は固定ではなく、用途や開発段階に応じて選ぶ方針を明記

## Version 2.20

開始内容:

- Memory検索の最小実用化を追加
- `core/memory_search.py` を追加し、保存済みMemoryをキーワード検索できる土台を作成
- `覚えてる？` / `記憶ある？` / `Memoryを探して` などの簡易Intent抽出を追加
- 直近保存Memory確認と、保存済みMemory全体の検索を分離
- DBスキーマ変更はしない方針を維持
- 自動チェックではfake検索を使い、実DB保存や実Webアクセスを行わない
- `scripts/check_ver2200.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver2200.py` を追加

## Version 2.19

開始内容:

- 確認待ち状態の文脈解釈を改善
- `core/confirmation_intent.py` を追加し、confirmation intentをルールベースで分離
- Web Reader確認待ち中の `いいよ` / `お願いします` / `OKです` などを実行許可として扱う
- Web Reader確認待ち中の `キャンセル` / `やめて` / `今回はいい` などを拒否として扱う
- 確認待ち中に不明な入力が来た場合、通常会話へ流さず確認を聞き直す
- Memory Candidate確認応答に、保存・拒否・保留・編集の自然表現を追加
- Web Reader未対応という誤解を避ける返答へ調整
- LLM解釈はまだ実装しない方針を維持
- `scripts/check_ver2190.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver2190.py` を追加

## Version 2.18

開始内容:

- Memory保存後の確認・表示フローを追加
- Memory Candidate保存成功後の返答に保存内容プレビューを表示
- 直近保存したMemoryを会話内で確認できる基礎を追加
- `今保存した記憶を確認して` などの入力で直近保存内容を表示
- `last_saved_memory_candidate_result` で保存成功結果を保持
- 編集済みMemory Candidate保存後も編集後summaryを確認表示に反映
- DBスキーマ変更はしない方針を維持
- 自動チェックではfake保存・fake記憶確認を使い、実DB保存しない
- `scripts/check_ver2180.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver2180.py` を追加

## Version 2.17

開始内容:

- Memory Candidateのユーザー確認つき保存を追加
- ユーザーが明示的に `保存する` と答えた場合だけ、低リスク候補を保存対象にする
- `core/memory_candidate_saver.py` を追加
- Memory Candidateを既存の長期記憶保存機構へ渡せる保存用テキストに変換
- 編集済みMemory Candidateも保存対象にできるようにした
- 高リスク候補はVer2.17では自動保存しない
- DBスキーマ変更はしない方針を維持
- 自動チェックでは実DB保存しない方針を維持
- `scripts/check_ver2170.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver2170.py` を追加

## Version 2.16

開始内容:

- Memory Candidate編集dry-runを追加
- `編集して保存` の後に、次のユーザー入力を編集内容として受け取る流れを追加
- 編集内容を反映した編集済みMemory Candidateをdry-run保持
- `pending_memory_candidate_edit` で編集待ち状態を管理
- `core/memory_candidate_confirmation.py` に編集応答解釈を追加
- まだMemory保存はしない方針を維持
- Memory CandidateのDB保存もしない方針を維持
- DBスキーマ変更はしない方針を維持
- `scripts/check_ver2160.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver2160.py` を追加

## Version 2.15

開始内容:

- ポートフォリオREADMEを整備
- `README.md` を就活ポートフォリオ向けに追加
- `docs/portfolio_notes.md` を追加
- `docs/demo_logs/web_reader_memory_candidate_demo.md` を追加
- Web Reader から Memory Candidate dry-run までのデモログを整理
- 実装済み機能と未実装機能を分けて記載
- MIGRATION.mdはまだ作らない方針を維持
- `scripts/check_ver2150.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver2150.py` を追加

## Version 2.14

開始内容:

- 開発自走方針をリポジトリに反映
- `AGENTS.md` を追加
- `docs/development_workflow.md` を追加
- 後から修正できる通常作業はユーザー確認なしで進める方針を明記
- 通常の `git add` / `git commit` / `git push` は確認不要とする方針を明記
- 不可逆操作、DB削除、Memory物理削除、課金、外部送信は確認必須とする方針を明記
- `MIGRATION.md` はVer2.14ではまだ作らない方針を明記
- `scripts/check_ver2140.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver2140.py` を追加

## Version 2.13

開始内容:

- Memory Candidate確認応答のdry-runを追加
- `core/memory_candidate_confirmation.py` を追加
- 保存する / 保存しない / 編集して保存 / 後で確認 の応答を解釈
- Web Reader成功後のMemory Candidate pendingに確認応答dry-runを軽く接続
- 「保存する」と言われてもdry-runで止める
- まだMemory保存はしない方針を維持
- DBスキーマ変更はしない方針を維持
- Memory CandidateのDB保存もしない方針を維持
- 自動チェックでは実Webアクセス・LLM実行・DB書き込みをしない
- `scripts/check_ver2130.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver2130.py` を追加

## Version 2.12

開始内容:

- Memory Candidate確認UI方針をdocs化
- `docs/memory_candidate_ui_policy.md` を追加
- 保存前にユーザーが確認できる形を整理
- 保存 / 保存しない / 編集 / 後で確認 の選択肢を整理
- 高リスク候補は自動保存しない方針を明記
- まだMemory保存はしない方針を維持
- DBスキーマ変更はしない方針を維持
- Memory CandidateのDB保存もしない方針を維持
- `scripts/check_ver2120.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver2120.py` を追加

## Version 2.11

開始内容:

- Memory CandidateをWeb Reader結果にdry-run接続
- Web Reader成功時に保存候補を作る
- Web Reader成功時の返答にMemory Candidate dry-run情報を短く表示
- 失敗時・未実行時はMemory Candidateを作らない
- まだMemory保存はしない方針を維持
- DBスキーマ変更はしない方針を維持
- Memory CandidateもDB保存しない方針を維持
- 自動チェックではfake fetcherを使い、実Webアクセスしない
- `scripts/check_ver2110.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver2110.py` を追加

## Version 2.10

開始内容:

- Memory Candidate生成のdry-runを追加
- `core/memory_candidate.py` を追加
- Reader結果から保存候補を作る土台を追加
- `scripts/check_ver2100.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver2100.py` を追加
- まだMemory保存はしない方針を維持
- DBスキーマ変更はしない方針を維持
- Web Reader本体にはまだ自動接続しない方針を維持
- 自動チェックでは実Webアクセス・LLM実行・ToolRunner実行・DB書き込みをしない

## Version 2.9

開始内容:

- Reader結果のMemory保存方針をdocs化
- `docs/reader_memory_policy.md` を追加
- Reader結果から保存する候補、保存しないもの、保存前確認が必要な条件を整理
- Memory Candidate / Project Knowledge / User Preference / Archive の扱いを整理
- Memory保存の本実装はまだしない方針を維持
- Web Reader結果のMemory保存はまだしない方針を維持
- `scripts/check_ver290.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver290.py` を追加

## Version 2.8

開始内容:

- Web Reader結果の会話品質を改善
- 成功時の返答を見やすくした
- 本文プレビューの余分な空白を整理し、長すぎる場合は短く表示するようにした
- 失敗時に読めたふりをしない方針を維持
- 自動チェックではfake fetcherを使い、実Webアクセスしない方針を維持
- Reader結果のMemory保存はまだしない方針を維持
- `scripts/check_ver280.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver280.py` を追加

## Version 2.7

開始内容:

- 完成形ビジョンをdocs化
- `docs/final_product_vision.md` を追加
- `docs/conversation_policy.md` を追加
- 高自律・記憶・ModelRouter / ToolRouter・自己アップデート・自律調査方針を整理
- 会話品質・返答方針を整理
- 実装はまだ行わない方針を維持
- `scripts/check_ver270.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver270.py` を追加

## Version 2.6

開始内容:

- Web Reader実Web手動テスト結果をdocsへ整理
- `https://example.com` を会話UIから読み取り、`Example Domain` と `text_preview` が返ったことを記録
- 自動チェックではfake fetcherを使い、実Webアクセスしない方針を維持
- Reader結果のMemory保存はまだしない方針を維持
- PDF / Image / YouTube / File Reader は今後の段階追加として維持
- `scripts/check_ver260.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver260.py` を追加

## Version 2.5

開始内容:

- `user_confirmed=True` 後にToolRunner経由でWeb Readerを実行する接続を追加
- URL検出だけでは実行せず、保留中の確認に対する肯定応答がある場合だけ実行
- 成功時にtitle / final_url / text_previewを会話返答へ含める
- 失敗時に読めたふりをせず、失敗理由を返す
- 自動チェックではfake fetcherを使い、実Webアクセスしない方針を維持
- `scripts/check_ver250.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver250.py` を追加

## Version 2.4

開始内容:

- Web Reader確認応答の前段処理を整理
- 肯定・否定・別話題・pendingなしをdry-run結果として扱えるようにした
- 肯定時にToolRequest候補を作れるようにした
- ただしWeb Reader実行、ToolRunner呼び出し、run_tool_request呼び出し、fetch実行はまだ行わない
- `scripts/check_ver240.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver240.py` を追加

## Version 2.3

開始内容:

- URL確認メッセージを会話返答として表示するdry-run接続を追加
- `core/personal_ai.py` でWeb Reader確認メッセージを返せるようにした
- ユーザーが「はい」と答えてもWeb Reader実行には進まない方針を維持
- ToolRunnerを会話UIから呼ばず、WebReaderAdapterのfetchも実行しない方針を維持
- `scripts/check_ver230.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver230.py` を追加

## Version 2.2

開始内容:

- URL入力検出から確認メッセージ生成までのdry-runを追加
- `core/web_reader_confirmation.py` を追加
- Web Reader実行前確認メッセージを作れるようにした
- ToolRunnerを呼ばず、WebReaderAdapterのfetchも実行しない方針を維持
- 会話UIへの実接続はまだ行わない方針を維持
- `scripts/check_ver220.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver220.py` を追加

## Version 2.1

開始内容:

- Web Reader手動実行テスト手順を整理
- Web Readerの会話UI接続方針を整理
- `user_confirmed` と自動Webアクセス禁止方針を再確認
- `docs/web_reader_manual_test.md` を追加
- `docs/web_reader_ui_connection_plan.md` を追加
- `scripts/check_ver210.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver210.py` を追加

## Version 2.0

開始内容:

- Web Reader最小実用版を追加
- WebReaderAdapter を追加
- URL抽出とHTMLテキスト化の基礎を追加
- Permission確認なしではWebアクセスしないToolRunnerを追加
- Web Reader結果を ToolResult と ToolExecutionLog に接続
- 自動checkではfake fetcherを使い、実Webアクセスしない方針を追加
- `scripts/check_ver200.py` を追加
- `scripts/run_ver2_checks.py` を追加
- `docs/web_reader_design.md` を追加

## Version 1.10

開始内容:

- Ver1.x総仕上げ確認を追加
- Ver1.1からVer1.9までの実装内容を整理
- Ver2.0 Reader実装前の準備状態を確認
- Ver2.0でやること / やらないことを再確認
- Web Readerを最初の実装候補として再確認
- `docs/ver1_x_final_review.md` を追加
- `scripts/check_ver1100.py` を追加
- `scripts/run_ver1_checks.py` に `check_ver1100.py` を追加

## Version 1.9

開始内容:

- Ver2.0 Reader実装計画を整理
- Ver2.0を付ける条件をdocs化
- Readerの実装順序を整理
- Web Readerを最初の実装候補として整理
- PDF / Image / YouTube / File Reader の段階的追加方針を整理
- Reader共通の ToolRequest / ToolResult / Permission / ToolExecutionLog 方針を整理
- `docs/reader_implementation_plan_v2.md` を追加
- `scripts/check_ver190.py` を追加
- `scripts/run_ver1_checks.py` に `check_ver190.py` を追加

## Version 1.8

開始内容:

- Reader実装前の手動テストケースを整理
- 通常会話 / URL / YouTube / PDF / Image / File / Document / PC操作の期待挙動をdocs化
- ToolRequest dry-run / ToolPermission / ToolExecutionLog の確認観点を整理
- 未実装Toolを実行したふりしないためのテスト観点を追加
- `docs/reader_pre_implementation_test_cases.md` を追加
- `scripts/check_ver180.py` を追加
- `scripts/run_ver1_checks.py` に `check_ver180.py` を追加

## Version 1.7

開始内容:

- Tool実行ログと結果記録の設計を追加
- ToolExecutionRecord を追加
- ToolExecutionLogger を追加
- build_tool_execution_record を追加
- ToolRequest / ToolPermissionDecision / ToolResult をまとめて記録できる土台を追加
- executed=False を明確に記録する方針を追加
- DB保存はまだ行わない方針をdocs化
- `docs/tool_execution_log_design.md` を追加
- `scripts/check_ver170.py` を追加
- `scripts/run_ver1_checks.py` に `check_ver170.py` を追加

## Version 1.6

開始内容:

- Reader実装前のInputAnalyzer / Capability / Tool連携確認を追加
- ToolRequestDecision を追加
- build_tool_request_decision を追加
- 通常会話ではToolRequestを作らない方針を追加
- Reader系入力ではToolRequestを作るが実行しないdry-run方針を追加
- `docs/tool_input_integration.md` を追加
- `scripts/check_ver160.py` を追加
- `scripts/run_ver1_checks.py` に `check_ver160.py` を追加

## Version 1.5

開始内容:

- PermissionManagerとTool実行前確認の接続準備を追加
- ToolPermissionDecision を追加
- evaluate_tool_permission を追加
- build_permission_message を追加
- ToolRequest の requires_permission / risk_level を使った判定方針を追加
- 未許可ならToolを実行しない方針をdocs化
- `docs/tool_permission_design.md` を追加
- `scripts/check_ver150.py` を追加
- `scripts/run_ver1_checks.py` に `check_ver150.py` を追加

## Version 1.4

開始内容:

- Reader追加前のTool / Adapter受け口を整理
- ToolRequest / ToolResult / ToolAdapter を追加
- ToolRegistry を追加
- 未実装Toolを実行したふりせず扱う方針を追加
- `docs/tool_adapter_design.md` を追加
- `scripts/check_ver140.py` を追加
- `scripts/run_ver1_checks.py` に `check_ver140.py` を追加

## Version 1.3

開始内容:

- 会話品質方針を追加
- 通常会話では短めで自然に返す方針を追加
- 相談では結論、理由、選択肢を整理する方針を追加
- 開発補助では手順、変更対象、確認コマンド、注意点を明確にする方針を追加
- 不明点を断定しない方針を追加
- `ai/conversation_quality_policy.py` を追加
- `scripts/check_ver130.py` を追加
- `scripts/run_ver1_checks.py` に `check_ver130.py` を追加

## Version 1.2

開始内容:

- Ver1.x用チェック運用を整理
- quick check / standard check / full pre-release check の考え方を追加
- `scripts/run_ver1_checks.py` を追加
- `scripts/check_ver120.py` を追加
- Ver1.xのcheck番号方針をdocsに整理

## Version 1.1

開始内容:

- 通常会話でMemory情報を使いすぎないように調整
- Memory利用方針 minimal / normal / detailed を追加
- 明示的な記憶参照ではMemoryを詳しく使い、通常会話では控えめに使う方針を追加
- Preference情報を雑談に毎回混ぜない方針を追加
- `ai/memory_usage_policy.py` を追加
- `scripts/check_ver110.py` を追加

## Version 1.0 Final Preparation

開始内容:

- `docs/version_1_0_release_decision.md` の総合判定を GO に更新
- Git状態をOKに更新
- Ver1.0直前の最終自動check、benchmark、app起動確認を実施
- Ver1.0は完成版ではなく、最低限の会話・記憶・安全確認・未実装機能の正直な扱いをテストできる実用テスト版として位置づけ
- `scripts/check_v1_final_preparation.py` を追加
- 今回はまだVer1.0タグやGitHub Releaseは作成しない

## Version 0.31

開始内容:

- Ver0.30で保留だった通常会話2件と記憶参照1件をOKに更新
- `docs/version_1_0_release_decision.md` の総合判定を GO候補 に更新
- 通常会話でMemory情報を使いすぎる傾向をVer1.1以降の改善候補として記録
- `scripts/check_ver031.py` を追加
- 今回はまだVer1.0タグやGitHub Releaseは作成しない
- コード機能本体、DB削除、Memory物理削除、Git commit / push は行わない

## Version 0.30

開始内容:

- Ver1.0直前の手動テスト表を実測に基づいて更新
- `docs/version_1_0_release_decision.md` の判定欄を更新
- `scripts/check_ver030.py` を追加
- Ver1.0前の自動check、benchmark、manual test、未実装機能の扱い、Memory安全性、docs最新性を確認
- 今回はまだVer1.0タグやGitHub Releaseは作成しない
- コード機能本体、DB削除、Memory物理削除、Git commit / push は行わない

## Version 0.29

開始内容:

- `docs/version_policy.md` を追加
- 整数バージョンを「実用的に使える区切り」として扱う方針を整理
- Ver1.0〜Ver6.0の大まかな役割を整理
- Ver4.0とVer5.0の違いを整理
- GO / HOLD / NO-GO とメジャーバージョン更新の関係を整理
- `scripts/check_ver029.py` を追加
- 今回はコード機能本体を変更せず、長期開発に向けたバージョン管理方針をdocsとして明文化

## Version 0.28

開始内容:

- `docs/version_1_0_release_decision.md` を追加
- `scripts/check_ver028.py` を追加
- Ver1.0へ進めるGO / HOLD / NO-GO条件を整理
- Ver1.0後に回す作業を整理
- Ver1.0直前の推奨確認手順を整理
- 今回はコード機能本体を変更せず、Ver1.0へ進む前の判定基準をdocsとして明文化

## Version 0.27

開始内容:

- `docs/version_1_0_final_check.md` を追加
- `scripts/run_pre_v1_checks.py` を追加
- `scripts/check_ver027.py` を追加
- Ver1.0前の自動チェック、ベンチマーク、手動テスト、Git確認の順番を整理
- Ver1.0へ進める判定基準を整理
- `run_pre_v1_checks.py` はVer0.11〜Ver0.26のcheckと軽量性ベンチマークを順番に実行し、最後に結果を集計する
- 今回はコード機能本体を変更せず、docs整備と確認スクリプト追加として実施

## Version 0.26

開始内容:

- `docs/future_app_integrations.md` を追加
- `docs/version_1_0_manual_test.md` を追加
- 将来的に対応したい制作系・日常系・読み取り系・操作系アプリを整理
- Tool / Adapter形式で後から追加しやすくする方針を整理
- インストール、購入、外部投稿、配信開始、ファイル削除などは必ず許可を取る方針を整理
- Ver1.0前の手動テスト表を追加
- `scripts/check_ver026.py` を追加し、docsの存在、重要語、importを確認できるようにした
- 今回はコード機能本体を変更せず、docs整備と確認スクリプト追加として実施

## Version 0.25

開始内容:

- 軽量性ベンチマークを追加
- `scripts/benchmark_lightweight.py` を追加し、主要処理時間を測定できるように変更
- PersonalAI import時間、初期化時間、Capability判定時間、Preference抽出時間、Preference確認判定時間を測定
- MemoryContext生成時間と自動忘却dry-run時間を測定
- `scripts/check_ver025.py` を追加し、benchmarkスクリプトの存在と実行を確認
- `docs/performance_benchmark.md` を追加
- 今回は高速化ではなく、測定できる状態にすることを目的として実施
- Qwen / Ollama問い合わせ、外部通信、DB削除、Memory物理削除、`is_active` 変更は行わない方針を維持

## Version 0.24

開始内容:

- 自動忘却dry-runを追加
- `ai/memory_forgetting.py` を追加し、忘却候補をスコア方式で判定できるように変更
- `analyze_forgetting_candidates()` を追加
- `get_forgetting_candidates()` を追加
- 低重要度、低信頼度、一時記憶、test/debug系、期限切れ記憶を候補にしやすくする方針を追加
- ユーザー基本情報、Preference、project、core方針、高重要度・高信頼度の記憶を候補にしにくくする方針を追加
- dry-run結果に `dry_run=True`、`recommended_action`、`score`、`reasons` を含めるように変更
- `scripts/check_ver024.py` を追加し、synthetic memoryとDB読み取りdry-runを確認
- 物理削除、自動 `is_active=False`、ユーザー確認なしの忘却は行わない方針を明文化

## Version 0.23

開始内容:

- Capability判定を強化
- `CapabilityManager.analyze()` を追加し、入力に必要な能力と不足機能を判定できるように変更
- 通常会話、記憶参照、記憶保存、Preference記憶を現在対応可能な能力として分類
- Web / YouTube / PDF / 画像 / ファイル読み取り / 文書作成 / PC操作 / 外部API / OpenAI候補を必要能力として分類
- 未実装機能が必要な場合は、読んだふり・実行したふりをせず、`user_message` で正直に返す方針を追加
- PersonalAI本体にCapability判定を接続し、Planner / Router / Executorへ進む前に未実装機能を止めるように変更
- `scripts/check_ver023.py` を追加し、Capability判定とPersonalAI統合を確認
- CapabilityManagerは「できるかどうか」、PermissionManagerは「実行してよいか」を判断する役割として整理

## Version 0.22

開始内容:

- 確認質問後にPreference保存を続行する仕組みを追加
- PersonalAIが1件だけ `pending_preference_confirmation` を保持できるように変更
- pendingはPersonalAIインスタンス内のみで保持し、DBには保存しない方針を採用
- `resolve_preference_confirmation_answer()` を追加し、確認回答を `save_primary`、`save_addition`、`save_change`、`cancel`、`ask_again` に分類
- `save_resolved_preference_confirmation()` を追加し、確認回答後にPreferenceを保存できるように変更
- 一番好きな食べ物を `preference:food:primary` で保存する方針を追加
- `scripts/check_ver022.py` を追加し、回答解決、保存、PersonalAI pending flowを確認
- 完全な自然言語理解、長期的なpending DB保存、複数同時保留、OpenAI接続、Vector DB、Embedding検索は今後の課題として維持

## Version 0.21

開始内容:

- `docs/project_handoff.md` を追加
- `docs/recovery_guide.md` を追加
- `docs/core_principles.md` を追加
- ChatGPT / Codex / VS Code の履歴が消えても再開しやすいようにした
- PersonalAIの最終目標、安全方針、開発方針、回答精度重視の方針を明文化した
- `scripts/check_ver021.py` を追加し、引き継ぎ・復旧・原則docsの存在と重要語を確認できるようにした
- 今回は機能追加ではなく、プロジェクト継続性を高めるためのドキュメント整備として実施

## Version 0.20

開始内容:

- Preference矛盾時の確認質問設計を追加
- `ai/preference_confirmation.py` を追加し、Preference保存前に確認質問が必要か判定できるように変更
- `analyze_preference_confirmation()` を追加
- 好きなものの単純追加では確認しない方針を追加
- 明確な「好きじゃない」「嫌い」は確認せず更新してよい方針を追加
- 「一番好き」「今は / 前は」「変更」は確認候補にする方針を追加
- `core/personal_ai.py` にPreference保存前の確認判定を接続
- `scripts/check_ver020.py` を追加し、確認不要/確認必要の判定とVer0.19抽出維持を確認
- `docs/preference_confirmation.md` を追加し、確認しすぎない方針を整理
- 完全な自然言語理解、LLMによる高度な矛盾判定、自動忘却、OpenAI接続、ベクトルDB、Embedding検索は今後の課題として維持

## Version 0.19

開始内容:

- Preference記憶・矛盾記憶の最小実装を追加
- `ai/preference_memory.py` を追加し、明確な「好き」「好きじゃない」「嫌い」を抽出できるように変更
- `extract_preference_memories()` と `save_preference_memories()` を追加
- `memory_key=preference:food:<target>` により、同じ対象の現在Preferenceを更新できるように変更
- 好きな対象が複数ある場合は、別memory_keyとして複数保持できる方針を追加
- `core/personal_ai.py` にPreference記憶の最小接続を追加
- `scripts/check_ver019.py` を追加し、like / not_like / dislike の抽出・保存・更新を確認
- `docs/preference_memory.md` を追加し、記憶確認をしすぎない方針を整理
- 完全な自然言語理解、複雑なPreference抽出、自動忘却、OpenAI接続、ベクトルDB、Embedding検索は今後の課題として維持

## Version 0.18

開始内容:

- 無効化MemoryのMemoryContext反映確認を追加
- `scripts/check_ver018.py` を追加し、activeなMemoryがContextに出ること、無効化後に出ないこと、復元後に戻ることを確認
- inactiveなMemoryを直接 `build_memory_context()` に渡しても出力されないことを確認
- `docs/version_1_0_test_plan.md` を追加し、Ver1.0の位置づけとテスト計画を整理
- Ver1.0は完成版ではなく、最低限の会話・記憶・安全確認をテストできる実用テスト版と定義
- Preference記憶、矛盾記憶、記憶確認頻度、自動忘却、Capability判定、ユーザー応答調整、軽量性評価を今後の重要項目として整理
- Memory内容の編集、物理削除、自動忘却、OpenAI接続、Web/PDF/YouTube読み取り、Ver1.0本体への昇格は今後の課題として維持

## Version 0.17

開始内容:

- Memoryの手動無効化・復元機能を追加
- `database.memory_manager` に `get_memory_by_id()` と `set_memory_active()` を追加
- `scripts/manage_memory_status.py` を追加し、ID指定でMemoryを無効化・復元できるように変更
- `manage_memory_status.py` はデフォルトdry-runとし、実際に変更する場合は `--apply` を必須にした
- 無効化は `is_active=False`、復元は `is_active=True` とし、Memoryの物理削除は行わない
- 実行前に対象Memoryの内容を表示する安全確認を追加
- `scripts/check_ver017.py` を追加し、dry-run、無効化apply、復元applyを確認できるように変更
- Memory内容の編集、物理削除、自動無効化、短期記憶、Knowledge DB、ベクトルDB、Embedding検索の本格実装は今後の課題として維持

## Version 0.16

開始内容:

- Memory一覧・手動確認用スクリプトを追加
- `scripts/list_memories.py` を追加し、現在DBの長期記憶をブロック形式で一覧表示できるように変更
- `--limit`、`--memory-type`、`--category`、`--scope`、`--active-only`、`--include-inactive`、`--search` の簡易オプションを追加
- `scripts/check_ver016.py` を追加し、Memory一覧表示スクリプトの基本動作とフィルタ動作を確認できるように変更
- 一覧表示スクリプトは読み取り専用で、記憶の削除・更新・無効化は行わない方針を維持
- 記憶編集、無効化、削除、短期記憶、Knowledge DB、ベクトルDB、Embedding検索の本格実装は今後の課題として維持

## Version 0.15

開始内容:

- MemoryContextの実用確認・デバッグ機能を追加
- `scripts/show_memory_context.py` を追加し、現在DBの長期記憶からMemoryContextを表示できるように変更
- `show_memory_context.py` に `--limit`、`--category`、`--scope` の簡易オプションを追加
- `scripts/check_ver015.py` を追加し、MemoryContext生成とプレビュー用スクリプトの基本動作を確認できるように変更
- 既存記憶を削除・更新しない読み取り専用の確認スクリプトとして実装
- 短期記憶、Knowledge DB、ベクトルDB、Embedding検索の本格実装は今後の課題として維持

## Version 0.14

開始内容:

- MemoryContextを強化
- 長期記憶をカテゴリ別に整理してLLMへ渡すように変更
- `category` と `scope` を使い、ユーザー情報、好み・方針、プロジェクト、現在の作業、知識、その他へ分類
- `importance`、`confidence`、`scope`、`memory_key` をsystem message上で確認できるように変更
- `is_active=False` の記憶をLLMへ渡さないように変更
- `confidence < 50` の記憶に `低確信` 表示を追加
- MemoryContextの長さが伸びすぎないよう、全体件数と分類ごとの件数に上限を追加
- Ver0.14確認用スクリプト `scripts/check_ver014.py` を追加
- 短期記憶、知識DB、ベクトルDB、Embedding検索の本格実装は今後の課題として維持

## Version 0.13

開始内容:

- Memory設計を強化
- `memories` テーブルに `memory_key`、`subcategory`、`scope`、`confidence`、`updated_at`、`expires_at`、`is_active` を追加
- 既存DBを削除せず、足りない列だけを追加する安全なマイグレーションを追加
- `save_memory()` が `memory_key` による更新に対応
- `project`、`preference`、`goal`、`personality`、`other`、`knowledge` は、memory_keyがない場合にcategoryだけで上書きしない方針へ変更
- `get_memories()` に `memory_type`、`category`、`scope`、`active_only` の絞り込みを追加
- 記憶抽出プロンプトに任意項目として `memory_key`、`subcategory`、`scope`、`confidence` を追加
- Memory設計書 `docs/memory.md` を追加
- Ver0.13確認用スクリプト `scripts/check_ver013.py` を追加
- 短期記憶、知識、ベクトルDB、embedding検索の本格分離は今後の課題として維持

## Version 0.12

開始内容:

- Permission / Risk基礎を追加
- `core/permission_manager.py` を追加
- PersonalAI本体にPermissionManagerを接続
- Executor実行前にPermissionManagerの判断を通すように変更
- `self.last_permission_decision` を保存
- 許可が必要な操作は現時点では実行せず `blocked=True` とする方針を追加
- Ver0.12確認用スクリプト `scripts/check_ver012.py` を追加
- 実際の許可取得・許可後の再実行は今後の課題として維持

## Version 0.11

開始内容:

- Clarification基礎を追加
- 情報不足時に `ask_clarification` action を返すようにPlannerを更新
- YouTube / Web / PDF / 画像などの対象が不足している場合に追加質問するように変更
- Routerが `ask_clarification` を安全にQwenへルーティングするように更新
- Executorが必要最小限の固定質問文を返すように更新
- Ver0.11確認用スクリプト `scripts/check_ver011.py` を追加
- ClarificationManagerとしての本格分離は今後の課題として維持

## Version 0.10

開始内容:

- InputAnalyzer結果をPlannerのaction判定に反映
- YouTube URL + 要約を `summarize_youtube` に分類
- URL + 要約を `summarize_url` に分類
- 文書作成依頼を `create_document` に分類
- おすすめ依頼を `recommend`、質問を `answer_question` に分類
- Routerが新しいactionを安全にQwenへルーティングするように更新
- Executorが未実装の外部読み取り・実ファイル作成で読んだふり、作ったふりをしない固定メッセージを返すように更新

## Version 0.9.2

整理内容:

- docs/vision.mdを追加
- PersonalAIの完成形を「ユーザーが使う唯一のAI・作業入口」として明文化
- 短期記憶・長期記憶・知識の3層構造を整理
- 自律性と許可制の方針を整理
- 将来的にPersonalAI自身がコード実装・動作確認・Git管理まで行う方針を整理
- 開発中はChatGPT/Codex/Gitなどを使い、完成まではPersonalAIを普段使いしない方針を明記

## Version 0.9.1

整理内容:

- docsを現在のVer0.9状態に合わせて更新
- app_buckup.pyを旧テスト用コードとしてlegacy/app_buckup.pyへ移動
- .agentsフォルダは現時点ではPersonalAI本体で未使用であり、削除しない方針を明記
- system promptを整理し、記憶にないことを断定しない方針と未実装の外部読み取りを読んだふりしない方針を追加
- DBリセット手順をdocs/db_reset.mdに追加
- InputAnalyzerの判定語彙を少し追加
- 既存の会話、記憶、Qwen実行機能を壊さない安定化回として整理

## Version 0.9

開始内容:

- InputAnalyzerクラス追加
- ユーザー入力をinput_type、task_type、URL有無などに構造化
- InputAnalyzerをPersonalAI内部に接続
- 解析結果をself.last_input_analysisに保存
- まだWebやYouTubeの実読み取りは行わない方針を維持

## Version 0.8

開始内容:

- ExecutorをPersonalAI内部に接続
- PersonalAIからの直接 ask_llm 呼び出しを廃止
- planとrouteをExecutorへ渡し、ExecutorがQwen実行を担当する形へ変更
- 既存の会話履歴保存・記憶抽出・記憶保存フローを維持

## Version 0.7

開始内容:

- Executorクラス追加
- Executor設計書追加
- target=qwen のとき Qwen を実行する土台を追加
- target=openai_candidate のとき未実装メッセージを返す方針を追加

## Version 0.6

開始内容:

- Plan / Route データモデル追加
- PlannerがdictではなくPlanを返すように変更
- RouterがdictではなくRouteを返すように変更
- Routerは既存のdict形式planにも最低限対応

## Version 0.5

開始内容:

- CapabilityManager、Planner、RouterをPersonalAI内部に接続
- planとrouteを生成しつつ、既存のQwen回答生成フローを維持
- まだExecutorやOpenAI呼び出しは行わない方針を維持

## Version 0.4

開始内容:

- Router設計書追加
- Routerクラス追加
- ModelRouterではなく、道具選択全体を扱うRouter方針を採用

## Version 0.3

開始内容:

- Planner設計書追加
- Plannerクラス追加

## Version 0.2

開始内容:

- docs追加
- CapabilityManager追加

## Version 0.1

完了内容:

- Qwen接続
- 会話履歴保存
- 長期記憶
- 自動記憶抽出
- 複数記憶抽出
- categoryによる記憶更新
- PersonalAIクラス化
- Git/GitHub連携
