# PersonalAI Architecture

## 設計思想

PersonalAIはPythonで実装された統括システムである。

Qwen、OpenAI、Memory、Knowledge、Toolなどは、PersonalAIが目的に応じて使う道具である。
PersonalAI本体は、それらの道具を直接の目的にするのではなく、ユーザーを支援するために適切に選び、組み合わせて使う。

## 優先順位

PersonalAIの判断では、以下の優先順位を重視する。

1. 精度
2. 安全性
3. コスト
4. 速度

速く返すことも大切だが、まずは正確で安全な回答を優先する。

## 簡易フロー

現在想定している基本的な処理の流れは以下である。

```text
入力 → 解釈 → 読み取り → 文脈構築 → 行動選択 → 実行・出力 → 記憶
```

各ステップの役割は以下の通り。

- 入力: ユーザーの発言を受け取る
- 解釈: ユーザーが何を求めているかを考える
- 読み取り: 会話履歴や長期記憶を取得する
- 文脈構築: LLMに渡す情報を整理する
- 行動選択: 会話、記憶、ツール利用などの方針を決める
- 実行・出力: 必要な処理を実行し、回答する
- 記憶: 今後も役立つ情報を保存・更新する

## Version 0.5の内部接続

Version 0.5では、CapabilityManager、Planner、RouterがPersonalAI内部で接続された。

現在の会話処理では、ユーザー入力を受け取ったあと、以下の順番で内部情報を作る。

```text
ユーザー入力 → capability取得 → plan作成 → route作成 → messages作成 → Qwen呼び出し → 履歴保存
```

現時点では、planとrouteは将来のExecutor連携に向けて生成・保持するだけである。
まだplanやrouteによる処理分岐は行わず、既存のQwenを使った回答生成フローを維持する。

## Version 0.6のデータモデル

Version 0.6では、モジュール間で使うデータ構造を明確にするため、`Plan` と `Route` を追加した。

- `Plan`: Plannerが作る行動計画を表す
- `Route`: Routerが作る処理先情報を表す

これにより、Executor、Evaluator、OpenAI、Vision、PDF Readerなどを追加するときに、受け渡す情報の形をそろえやすくする。

## Version 0.8のExecutor接続

Version 0.8では、ExecutorがPersonalAI内部で実際に使われるようになった。

現在の会話処理では、Routerが作ったrouteをExecutorへ渡し、ExecutorがQwenを実行する。

```text
ユーザー入力 → capability取得 → plan作成 → route作成 → messages作成 → Executor → Qwen → 履歴保存
```

これにより、PersonalAI本体はLLMを直接呼び出すのではなく、Executorに実行を任せる構造になった。
現時点では通常のtargetは `qwen` のままであり、既存の会話機能と記憶機能は維持する。

## Version 0.9のInputAnalyzer接続

Version 0.9では、InputAnalyzerがPersonalAI内部に接続された。

現在の会話処理では、ユーザー発言を保存したあと、InputAnalyzerが入力を簡単に構造化する。

```text
ユーザー入力 → 入力保存 → input_analysis作成 → capability取得 → plan作成 → route作成 → Executor → Qwen
```

input_analysisには、入力の種類、依頼の種類、URL有無、外部読み取りやファイル作成が必要そうか、といった情報を保存する。
現時点ではWebやYouTubeを実際に読みに行かず、将来のPlanner、Router、Executor拡張に向けた土台として扱う。

## Version 0.9.1の安定化

Version 0.9.1では、新機能を大きく追加せず、現在状態の整理と安定化を行った。

現在の実行フローは以下である。

```text
ユーザー入力 → 入力保存 → InputAnalyzer → 記憶抽出・保存 → CapabilityManager → Planner → Router → messages作成 → Executor → Qwen → 応答保存
```

PersonalAI本体はQwenを直接呼び出さず、Executor経由でQwenを実行する。

現時点では、OpenAI、Web読み取り、YouTube読み取り、PDF読み取り、画像読み取り、PC画面読み取り、Word/PDFなどの実ファイル作成は未実装である。
InputAnalyzerは、それらが必要そうかを判定するだけで、実際の読み取りや作成は行わない。

`.agents` フォルダは現時点では用途不明であり、現在のPersonalAI本体では未使用扱いである。
ただし、今後Codexやエージェント設定で使う可能性があるため削除しない。

`legacy/app_buckup.py` は、category導入前の旧テスト用コードであり、現在の実行対象ではない。
現在の起動ファイルは `app.py` である。

## Version 0.10のPlan反映

Version 0.10では、InputAnalyzerの解析結果をPlannerのaction判定に反映した。

現在は、以下のような分類を行う。

- YouTube URL + 要約: `summarize_youtube`
- URL + 要約: `summarize_url`
- 文書作成依頼: `create_document`
- おすすめ・提案依頼: `recommend`
- 質問: `answer_question`
- 記憶参照: `memory_read`
- 記憶保存・更新: `memory_write`

Routerはこれらのactionを安全にQwenへルーティングする。
Executorは、YouTube読み取り、Web読み取り、実ファイル作成が未実装である場合、固定メッセージで正直に説明し、読んだふり・作ったふりをしない。

デバッグ時は、`PersonalAI.last_input_analysis`、`PersonalAI.last_plan`、`PersonalAI.last_route`、`PersonalAI.last_response` を確認する。

## Version 0.11のClarification基礎

Version 0.11では、情報不足時に必要最小限の追加質問を返すClarification基礎を追加した。

現在は、以下のような入力で `ask_clarification` を返す。

- YouTube / 動画に関する依頼だがURLがない
- Webページ / URLに関する依頼だがURLがない
- PDF / 画像 / 資料の読み取り依頼だが対象ファイルやURLがない

Routerは `ask_clarification` をQwenへルーティングし、Executorは固定質問文を返す。
ただし、ClarificationManagerとしての本格分離、複数ターンの状態管理、外部読み取り、実ファイル作成はまだ未実装である。

確認用スクリプトとして `scripts/check_ver011.py` を追加した。

## Version 0.12のPermission / Risk基礎

Version 0.12では、PermissionManagerを追加し、Executor実行前に安全確認の判断を通すようにした。

現在の流れは以下である。

```text
ユーザー入力 → InputAnalyzer → 記憶抽出・保存 → CapabilityManager → Planner → Router → PermissionManager → Executor → 応答保存
```

PermissionManagerは、PlanやRouteのactionを見て、許可が必要か、riskはどの程度か、現時点でblockedにすべきかを判断する。

現在実装済みの通常会話、質問、おすすめ、記憶、Clarification、未実装説明だけを返すactionは `blocked=False` とする。
将来のファイル操作、Web読み取り、Git操作、PC操作、外部送信などは許可が必要な操作として `blocked=True` とする。

現時点では、実際の許可取得、許可待ち状態の管理、許可後の再実行は未実装である。

## Version 0.13のMemory強化

Version 0.13では、長期記憶を将来拡張しやすくするために、`memories` テーブルの構造を強化した。

追加した主な項目は以下である。

- `memory_key`: 同じ記憶を安全に更新するためのキー
- `subcategory`: categoryより細かい分類
- `scope`: `global`、`user`、`project`、`knowledge` などの記憶範囲
- `confidence`: 記憶の確からしさ
- `updated_at`: 最終更新日時
- `expires_at`: 期限付き記憶の期限
- `is_active`: 有効な記憶かどうか

既存の `data/personal_ai.db` は削除せず、`create_database()` 実行時に足りない列だけを追加する。
これにより、既存の会話履歴や長期記憶を残したまま、保存構造を更新できる。

また、`project`、`preference`、`goal`、`personality`、`other`、`knowledge` のように複数持てるcategoryは、memory_keyがない場合にcategoryだけで上書きしない。
一方で、`name`、`favorite_food`、`current_activity` のように1つにまとまりやすいcategoryは、従来通りcategory単位で更新する。

現時点では、短期記憶・長期記憶・知識の完全分離、ベクトルDB、embedding検索はまだ導入しない。
まずは既存機能を壊さず、MemoryManagerを強化するための土台を作る。

## Version 0.14のMemoryContext強化

Version 0.14では、保存された長期記憶をLLMへ渡す `MemoryContext` を強化した。

これまでは主に記憶の本文だけを箇条書きで渡していた。
現在は、`category` と `scope` を使って、以下の分類に整理して渡す。

- ユーザー情報
- 好み・方針
- プロジェクト
- 現在の作業
- 知識
- その他

MemoryContextでは、重要度の高い記憶を優先する。
並び順は、できる範囲で `importance`、`confidence`、`updated_at`、`created_at` を考慮する。

`is_active=False` の記憶はLLMへ渡さない。
古いDBやテスト用オブジェクトで `is_active` が存在しない場合や `None` の場合は、有効な記憶として扱う。

`confidence` が50未満の記憶は、現時点では完全には除外しない。
ただし、`低確信` と表示し、確定情報として扱いすぎないようにする。

MemoryContextが長くなりすぎないよう、全体件数と分類ごとの件数に簡単な上限を設ける。
短期記憶テーブル、知識DB、ベクトルDB、Embedding検索はまだ未実装である。

## 現在の構成

現在のコードは、主に以下のフォルダに分かれている。

- `ai`: LLM呼び出し、記憶抽出、記憶コンテキスト作成
- `database`: 会話履歴と長期記憶の保存・取得
- `core`: PersonalAI本体と、今後の中核機能
- `docs`: 設計書、変更履歴、Memory設計、DBリセット手順
- `legacy`: 現在は実行対象外の旧テスト用コード

## 今後追加予定の構成

今後のエージェント化に向けて、以下の要素を追加予定である。

- `CapabilityManager`: PersonalAIが使える能力を管理する。Version 0.5でPersonalAI内部に接続済み
- `InputAnalyzer`: ユーザー入力を構造化する。Version 0.9でPersonalAI内部に接続済み
- `Planner`: ユーザーの目的に対して実行計画を立てる。Version 0.5でPersonalAI内部に接続済み
- `Router`: 用途に応じて使う道具や処理系を選ぶ。Version 0.5でPersonalAI内部に接続済み
- `Executor`: 選ばれた行動やツールを実行する。Version 0.8でPersonalAI内部に接続済み
- `Evaluator`: 出力や行動結果を評価する
