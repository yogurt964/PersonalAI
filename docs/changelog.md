# Changelog

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
