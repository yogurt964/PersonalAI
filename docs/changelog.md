# Changelog

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
