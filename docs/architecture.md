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

## Version 0.15のMemoryContext確認

Version 0.15では、MemoryContextが実際にどのようなsystem messageとしてLLMへ渡されるかを確認するためのデバッグ補助を追加した。

`scripts/show_memory_context.py` は、現在DBに保存されている長期記憶を `get_memories()` で取得し、`build_memory_context(memories)` の結果を表示する。

```text
現在DBの記憶 → get_memories() → build_memory_context() → Preview表示
```

このスクリプトは読み取り専用であり、既存記憶を削除・更新しない。
`--limit`、`--category`、`--scope` の簡易オプションで、確認したい記憶を絞り込める。

また、`scripts/check_ver015.py` で、MemoryContext生成とプレビュー用スクリプトの基本動作を確認できる。
これはデバッグ補助であり、短期記憶、Knowledge DB、ベクトルDB、Embedding検索はまだ未実装である。

## Version 0.16のMemory一覧表示

Version 0.16では、DB内の長期記憶そのものを人間が確認しやすくするために、`scripts/list_memories.py` を追加した。

このスクリプトは、現在DBに保存されている `memories` を読み取り、1件ごとのブロック形式で表示する。

```text
現在DBの記憶 → get_memories() → list_memories.py → 一覧表示
```

表示対象には、`content` だけでなく、`memory_type`、`category`、`subcategory`、`scope`、`memory_key`、`importance`、`confidence`、`is_active`、`source`、`tags`、作成日時、更新日時などを含める。

`--limit`、`--memory-type`、`--category`、`--scope`、`--include-inactive`、`--search` で確認範囲を絞り込める。
既定では有効な記憶だけを表示し、`--include-inactive` が指定された場合だけ無効な記憶も表示する。

このスクリプトは読み取り専用であり、記憶の削除、更新、無効化、DBリセットは行わない。
記憶編集、無効化、削除、短期記憶、Knowledge DB、ベクトルDB、Embedding検索はまだ未実装である。

また、`scripts/check_ver016.py` で、一覧表示スクリプトの存在、基本実行、絞り込み、検索がエラーなく動くことを確認できる。

## Version 0.17のMemory手動無効化・復元

Version 0.17では、Memoryを物理削除せず、`is_active` を切り替える手動無効化・復元機能を追加した。

`scripts/manage_memory_status.py` は、IDで対象Memoryを指定し、無効化または復元を行う。

```text
対象ID → Memory内容表示 → dry-run確認 → --apply時だけis_active変更
```

デフォルトはdry-runであり、DBは変更しない。
実際に変更する場合は `--apply` が必要である。

- 無効化: `is_active=False`
- 復元: `is_active=True`

この機能は、Memoryの内容編集や物理削除を行わない。
無効化済みのMemoryは、`scripts/list_memories.py --include-inactive` で確認できる。

`scripts/check_ver017.py` では、テスト用Memoryだけを作成し、dry-run、無効化apply、復元applyを確認する。
テスト後は `source="ver017_test"` または `tags="ver017_test"` のデータだけを削除し、ユーザーの既存記憶には触れない。

記憶内容の編集、物理削除、一括無効化、自動無効化、短期記憶、Knowledge DB、ベクトルDB、Embedding検索はまだ未実装である。

## Version 0.18のMemoryContext反映確認

Version 0.18では、`is_active` による無効化・復元がMemoryContextへ正しく反映されることを確認した。

`scripts/check_ver018.py` は、テスト用Memoryを作成し、以下の流れを確認する。

```text
active Memory作成 → MemoryContextに出る
↓
is_active=Falseへ変更 → MemoryContextから消える
↓
is_active=Trueへ復元 → MemoryContextに戻る
```

また、inactiveなMemoryを直接 `build_memory_context([memory])` に渡した場合でも出力されないことを確認する。
これにより、DB取得側とMemoryContext側の両方で、無効化MemoryがLLMへ渡らないことを確認できる。

## Version 1.0テスト計画

Version 0.18では、`docs/version_1_0_test_plan.md` を追加した。

Ver1.0は完成版ではなく、最低限の会話・記憶・安全確認をテストできる最初の実用テスト版とする。

Ver1.0テスト計画では、以下を重点項目として扱う。

- 会話安定性
- 記憶保存と記憶利用
- Memoryの無効化・復元
- Preference記憶
- 矛盾する記憶の扱い
- 記憶確認のしすぎを防ぐ方針
- Capability判定と未実装機能をできたふりしない方針
- PermissionManagerによる安全性
- 記憶の重要度判定
- 自動忘却のdry-run方針
- ユーザーとの会話による応答調整
- PC上で軽量に動くかの評価

Preference記憶、矛盾記憶、自動忘却、Knowledge DB、ベクトルDB、Embedding検索、Web/PDF/YouTube読み取り、OpenAI接続は、Ver1.0時点では未完成でもよいが、テスト計画上の重要項目として扱う。

## Version 0.19のPreference記憶

Version 0.19では、Preference記憶の最小実装を追加した。

`ai/preference_memory.py` は、明確な好き嫌い表現からPreference候補を抽出する。

```text
ラーメンが好き → like
ラーメンは好きじゃない → not_like
寿司は嫌い → dislike
```

Preference記憶は、以下の形式の `memory_key` を使う。

```text
preference:food:<target>
```

これにより、同じ対象について好き、好きじゃない、嫌いが変わった場合は、同じmemory_keyの現在状態を更新できる。
一方で、ラーメンと寿司のように対象が違う場合は、別々のPreferenceとして保持できる。

PersonalAI本体では、「覚えて」を含む入力からPreferenceが抽出できた場合、Preference記憶として先に保存する。
これは、好き嫌いの単純文が汎用Memory抽出と重複保存されにくくするためである。

記憶確認については、毎回聞きすぎない方針とする。
好きなものが増えたように見える場合は基本的に追加記憶とし、「一番好き」「今は」「前は」など更新意図がありそうな場合だけ確認を検討する。

現時点では、food以外のdomain、複雑な自然言語理解、自動忘却、Embedding検索は未実装である。

## Version 0.20のPreference確認質問

Version 0.20では、Preference記憶を保存する前に、確認質問が必要か判断する補助モジュールを追加した。

`ai/preference_confirmation.py` は、ユーザー入力を見て、以下を判定する。

```text
確認不要 → Preferenceを保存
確認必要 → 保存せず確認質問を返す
```

確認しないケース:

- 好きなものの単純追加
- 明確な `not_like`
- 明確な `dislike`

確認候補にするケース:

- 一番好き
- 今は / 前は
- 変更

PersonalAI本体では、Preference保存前に `analyze_preference_confirmation()` を呼ぶ。
`should_ask=True` の場合は、Preferenceを保存せず固定の確認質問を返す。
`should_ask=False` の場合は、Ver0.19と同じように保存する。

これは確認しすぎを避けるための最小実装であり、LLMによる高度な矛盾判定や完全な自然言語理解はまだ行わない。

## Version 0.21のHandoff / Recovery / Core Principles

Version 0.21では、機能追加ではなく、プロジェクトを安全に継続するためのドキュメント整備を行った。

追加した主なdocsは以下である。

- `docs/project_handoff.md`: ChatGPT / Codexへ渡せるプロジェクト引き継ぎ書
- `docs/recovery_guide.md`: PC、VS Code、GitHub、venv、checkスクリプトの復旧手順
- `docs/core_principles.md`: PersonalAIの最終目標、回答精度重視、安全方針、開発方針

これにより、会話履歴や作業文脈が消えても、docsを読めば現在状態、未実装機能、次の作業候補、復旧手順を把握できる。

Ver0.21時点では、PersonalAIの最終目標を「ユーザーの作業の中心入口」とし、回答精度、安全確認、未実装機能をできたふりしないことを最重要方針として整理した。

## Version 0.22のPreference確認回答

Version 0.22では、Preference確認質問のあとにユーザーが答えた場合、その回答を通常処理より先に扱うようにした。

現在の流れは以下である。

```text
ユーザー入力 → 入力保存 → pending preference確認 → InputAnalyzer → 記憶抽出・保存 → Planner → Router → PermissionManager → Executor
```

`pending_preference_confirmation` はPersonalAIインスタンス内で1件だけ保持する。
DBには保存しないため、アプリを終了すると消える一時状態である。

確認回答では、`save_primary`、`save_addition`、`save_change`、`cancel`、`ask_again` を扱う。
一番好きな食べ物は `preference:food:primary` に保存する。

この機能は、ユーザーに影響する大きな操作ではなく、Preference記憶の保存に限定した確認回答処理である。
完全な自然言語理解や複数pending管理はまだ行わない。

## Version 0.23のCapability判定強化

Version 0.23では、CapabilityManagerがユーザー入力に必要な能力と、現在のPersonalAIで対応できるかを判定するようになった。

現在の流れは以下である。

```text
ユーザー入力 → 入力保存 → pending preference確認 → InputAnalyzer → CapabilityManager → 記憶抽出・保存 → Planner → Router → PermissionManager → Executor
```

CapabilityManagerは「できるかどうか」を判断する。
PermissionManagerは「実行してよいか」を判断する。

現時点で、通常会話、記憶参照、記憶保存、Preference記憶は現在のQwenとMemoryで対応可能とする。
一方で、Web、YouTube、PDF、画像、ファイル読み取り、Word / Excel / PDF作成、PC操作、外部API、OpenAIが必要な高精度判断は、未実装または不足能力として扱う。

未実装機能が必要な場合、PersonalAIはPlanner / Router / Executorへ進む前に、CapabilityManagerの `user_message` を返す。
これにより、読んでいないWebページやPDF、YouTube、画像を読んだふりせず、実行していないファイル作成やPC操作を実行したふりしない。

将来的には、OpenAI、Web Reader、YouTube Reader、PDF Reader、Image Reader、Document Creator、PC Operatorを追加し、Capability判定結果をもとに安全に実行へ進める。

## Version 0.24の自動忘却dry-run

Version 0.24では、自動忘却候補を提案するdry-runを追加した。

`ai/memory_forgetting.py` は、Memory一覧を読み取り、低重要度、低信頼度、一時記憶、test/debug系、期限切れ記憶などを候補としてスコア化する。

この処理は読み取り専用である。
Memoryの物理削除は行わない。
自動で `is_active=False` にもしない。
ユーザー確認なしに記憶を忘れない。

将来的には、以下の流れを目指す。

```text
忘却候補表示 → ユーザー確認 → is_active=False
```

高重要度のユーザー情報、Preference、project情報、core方針、安全方針は候補にしにくくする。

## Version 0.25の軽量性ベンチマーク

Version 0.25では、PersonalAIが重くなりすぎていないか確認するための軽量性ベンチマークを追加した。

`scripts/benchmark_lightweight.py` は、以下の時間を測定する。

- PersonalAI import
- PersonalAI初期化
- Capability判定
- Preference抽出
- Preference確認判定
- MemoryContext生成
- 自動忘却dry-run

これは高速化ではなく、まず測定できる状態にするための基盤である。
Qwen / Ollamaへの問い合わせ、外部通信、DB削除、Memory物理削除、`is_active` 変更は行わない。

将来的には、OpenAI、Web Reader、PDF Reader、Image Readerなどを追加したあとに、機能追加で重くなっていないか比較するために使う。

## Version 0.26のFuture App Integrations / Ver1.0手動テスト

Version 0.26では、将来的にPersonalAIへ追加したいアプリ・ツール連携の方針を整理した。

PersonalAI本体に個別アプリ連携を詰め込むのではなく、Reader、Creator、Operator、ManagerなどのTool / Adapterとして追加する方針である。

また、Ver1.0前に人間が確認するための手動テスト表を追加した。
通常会話、記憶保存、記憶参照、Preference、確認質問、未実装機能、Capability、Permission、MemoryContext、忘却dry-run、軽量性ベンチマーク、引き継ぎを確認対象にする。

インストール、購入、外部投稿、配信開始、ファイル削除、Git push、個人情報入力などは必ずPermission方針に従う。
今回もコード機能本体は変更しない。

## Version 0.27のVer1.0前総合チェック

Version 0.27では、Ver1.0へ進む前の総合チェック手順を整理した。

`docs/version_1_0_final_check.md` では、Git状態確認、import確認、app.py起動確認、自動check、軽量性ベンチマーク、手動テスト、未実装機能の扱い、Memory / Preference / Forgetting安全確認、引き継ぎ・復旧確認、Ver1.0判定基準を順番にまとめる。

`scripts/run_pre_v1_checks.py` は、Ver0.11〜Ver0.26のcheckと軽量性ベンチマークを順番に実行し、途中で失敗しても最後に成功数・失敗数を表示する。

今回もコード機能本体は変更しない。

## 現在の構成

現在のコードは、主に以下のフォルダに分かれている。

- `ai`: LLM呼び出し、記憶抽出、記憶コンテキスト作成
- `database`: 会話履歴と長期記憶の保存・取得
- `core`: PersonalAI本体と、今後の中核機能
- `docs`: 設計書、変更履歴、Memory設計、DBリセット手順
- `legacy`: 現在は実行対象外の旧テスト用コード

## 今後追加予定の構成

今後のエージェント化に向けて、以下の要素を追加予定である。

- `CapabilityManager`: PersonalAIが使える能力と不足機能を判定する。Version 0.23でCapability判定を強化済み
- `InputAnalyzer`: ユーザー入力を構造化する。Version 0.9でPersonalAI内部に接続済み
- `Planner`: ユーザーの目的に対して実行計画を立てる。Version 0.5でPersonalAI内部に接続済み
- `Router`: 用途に応じて使う道具や処理系を選ぶ。Version 0.5でPersonalAI内部に接続済み
- `Executor`: 選ばれた行動やツールを実行する。Version 0.8でPersonalAI内部に接続済み
- `Evaluator`: 出力や行動結果を評価する
