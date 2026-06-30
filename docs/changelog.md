# Changelog

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
