# PersonalAI システム設計書 Ver1.0

## 1. PersonalAIとは何か

PersonalAIは、Pythonで実装された統括システムである。

Qwen、OpenAI、Memory、Knowledge、Toolは、PersonalAIそのものではなく、PersonalAIが目的に応じて使う道具である。PersonalAI自身は、ユーザーの入力を理解し、必要な道具を選び、組み合わせ、実行結果を評価する役割を持つ。

たとえば、Qwenは回答生成や記憶抽出に使うモデルであり、Memoryはユーザーについて覚えておくための仕組みである。将来的には、Web、YouTube Reader、PDF Reader、Vision、Word作成ツールなども、PersonalAIが選んで使う道具になる。

PersonalAIの中心的な責務は、単にLLMへ文章を渡すことではない。ユーザーが本当に達成したいことを考え、必要な文脈を集め、適切な処理を選び、結果が妥当かを確認し、今後も役立つ情報を記憶することである。

現在のVer0.9.1では、PersonalAI本体はQwenを直接呼び出さず、Routerが作ったRouteをExecutorへ渡し、ExecutorがQwenを実行する。
OpenAI、Web、YouTube、PDF、画像、PC画面などの実読み取りや実行はまだ未実装である。

## 2. 基本優先順位

PersonalAIは、以下の優先順位で判断する。

1. 精度
2. 安全性
3. コスト
4. 速度

速度は大切だが、最優先ではない。まず正確であること、次に安全であることを重視する。そのうえで、無駄なコストを避け、必要十分な速度で応答する。

この優先順位は、Planner、Router、Executor、Evaluatorなど、すべての中核モジュールに共通する判断基準である。

## 3. 全体処理フロー

PersonalAIの将来的な全体フローは以下の通りである。

```text
入力
↓
InputAnalyzer
↓
Context Builder / Memory
↓
Goal推定
↓
Confidence判定
↓
Planner
↓
Clarification生成
↓
Router
↓
Executor
↓
Evaluator
↓
Memory保存
↓
出力
```

この流れは、すべての処理を毎回重く実行するという意味ではない。単純な会話では短い経路で応答し、複雑な依頼では多くのモジュールを使う。重要なのは、責務を分けておくことで、将来的な拡張を安全に行えるようにすることである。

## 4. 各モジュールの役割

### InputAnalyzer

InputAnalyzerは、ユーザー入力を構造化する。

ユーザーの入力が通常のテキストなのか、URLなのか、PDFなのか、画像なのか、YouTubeなのか、Word文書の作成依頼なのかを判定する。これにより、後続のPlannerやRouterが適切な処理を選びやすくなる。

Version 0.9では、InputAnalyzerの初期実装がPersonalAI本体に接続された。現時点では、入力の種類やURL有無を判定するだけで、WebやYouTubeを実際に読み取りには行かない。
Version 0.9.1では、要約、文書作成、おすすめ、記憶、質問を判定するキーワードを少し追加した。

例:

- 通常会話
- URLの要約依頼
- PDFの読み取り依頼
- 画像の解析依頼
- YouTube動画の要約依頼
- Word文書やレポートの作成依頼

### Context Builder / Memory

Context Builder / Memoryは、判断に必要な文脈を集める。

具体的には、会話履歴、長期記憶、ユーザーの好み、価値観、過去のプロジェクト、関連する知識などを取得する。PersonalAIがユーザーに合わせた回答をするためには、この文脈が重要になる。

現在は、会話履歴と長期記憶の基礎が実装されている。今後は、知識ベースやプロジェクト単位の記憶なども扱えるようにする。

### Goal Manager

Goal Managerは、ユーザーの本当の目的を推定する。

ユーザーの発言は、表面的な依頼だけでは目的が分からない場合がある。たとえば「YouTubeをWordにまとめて」という依頼でも、目的は複数考えられる。

例:

- 学校や仕事に提出するレポートを作りたい
- チームに共有するための要点メモが欲しい
- 自分の勉強用に復習しやすくまとめたい
- ブログやSNS投稿の下書きにしたい

Goal Managerは、このような目的の違いを推定し、出力形式や詳しさ、言葉遣い、必要な確認質問に影響を与える。

### Confidence Estimator

Confidence Estimatorは、現在の情報だけで判断してよいかを判定する。

情報が十分であれば、そのままPlannerへ進む。情報が不足している場合は、追加質問が必要だと判断する。

例:

- PDFが添付されていないのに「このPDFを要約して」と言われた
- 「いい感じにまとめて」と言われたが、用途や形式が分からない
- 高リスクな判断なのに根拠情報が少ない

Confidence Estimatorは、答えを作るモジュールではない。「今の情報で進んでよいか」を見るモジュールである。

### Planner

Plannerは、何をするかを決める。

ユーザー入力、文脈、利用可能なcapabilityをもとに、PersonalAIの行動計画であるPlanを作成する。現在はルールベースの簡易Plannerが実装されており、通常会話、記憶読み取り、記憶書き込みなどを判定する。

将来的には、QwenやOpenAIを使って、より複雑な計画を立てられるようにする。

### Clarification Manager

Clarification Managerは、情報が足りない場合に、ユーザーへ何を質問すべきかを作る。

Confidence Estimatorが「このまま進むには情報が足りない」と判断したとき、Clarification Managerが具体的な質問文を生成する。

例:

- 「このWord文書は提出用ですか、共有用ですか？」
- 「PDFファイルをアップロードしてください」
- 「要約は短め、詳しめ、箇条書きのどれがよいですか？」

質問は多すぎるとユーザーの負担になるため、必要最小限にする。

### Router

Routerは、Planをもとに、使うモデル・API・ツールを選ぶ。

たとえば、通常会話や記憶を使う回答はQwenへ渡す。将来的には、画像ならVision、PDFならPDF Reader、Web調査ならBrowser、高リスクな推論ならOpenAI候補、というように処理先を選べるようにする。

Routerは「どの道具を使うか」を決めるが、実行そのものは行わない。

### Executor

Executorは、Routerが選んだ処理を実行する。

現在は、targetがQwenの場合に `ask_llm(messages)` を呼び出す土台がある。OpenAI候補は、まだ実行せず未実装メッセージを返す。
PersonalAI本体は `ask_llm()` を直接呼ばず、Executorに実行を任せる。

将来的には、OpenAI、Browser、PDF Reader、Vision、YouTube Reader、Tool実行などをここに追加していく。

### Evaluator

Evaluatorは、出力や実行結果が妥当か確認する。

回答がユーザーの目的に合っているか、根拠が不足していないか、危険な内容になっていないか、形式が要求通りかを確認する。必要であれば、再実行や追加質問につなげる。

Evaluatorは、PersonalAIの品質を安定させるための重要なモジュールである。

### Memory

Memoryは、今後も役立つ情報を保存・更新する。

ユーザーの名前、好きな食べ物、好み、目標、現在取り組んでいるプロジェクトなどを長期記憶として扱う。現在は、自動記憶抽出、複数記憶抽出、categoryによる記憶更新の基礎が実装されている。

将来的には、MemoryManagerとしてより明確に責務を分け、記憶の重要度、期限、信頼度、ユーザー確認なども扱えるようにする。

Version 0.13では、長期記憶の保存構造を強化した。
`memory_key`、`subcategory`、`scope`、`confidence`、`updated_at`、`expires_at`、`is_active` を追加し、同じ記憶を安全に更新したり、複数持てる記憶を上書きせず保存したりできる土台を作った。

`memory_key` がある場合は、`memory_type + scope + memory_key` が同じ記憶を更新する。
`project`、`preference`、`goal`、`personality`、`other`、`knowledge` のように複数持てるcategoryは、memory_keyがない場合にcategoryだけで上書きしない。
一方で、`name`、`favorite_food`、`current_activity` のように1つにまとまりやすいcategoryは、従来通りcategory単位で更新する。

現時点では、短期記憶・長期記憶・知識の完全分離、ベクトルDB、embedding検索はまだ行わない。
まずは既存の記憶機能を壊さず、将来のMemoryManager強化へ進める状態にする。

Version 0.14では、保存された長期記憶をLLMへ渡す `MemoryContext` を強化した。
MemoryContextは、記憶をただの箇条書きにするのではなく、ユーザー情報、好み・方針、プロジェクト、現在の作業、知識、その他に整理する。

LLMへ渡す文脈には、`importance`、`confidence`、`scope`、`memory_key` も必要に応じて含める。
`is_active=False` の記憶は渡さず、`confidence` が50未満の記憶は `低確信` と表示する。
これにより、PersonalAIが記憶を使うときに、重要な情報と不確かな情報を区別しやすくなる。

短期記憶テーブル、知識DB、ベクトルDB、Embedding検索はまだ未実装であり、今回は長期記憶をLLMへ渡す文章の整理に集中している。

Version 0.15では、MemoryContextの実用確認用スクリプトを追加した。
`scripts/show_memory_context.py` を使うと、現在DBに保存されている長期記憶が、どのようなsystem messageとしてLLMへ渡されるかを確認できる。

この確認スクリプトは読み取り専用であり、既存記憶を削除・更新しない。
`scripts/check_ver015.py` では、現在DBの記憶からMemoryContextを生成できることと、プレビュー用スクリプトが動くことを確認する。
これはデバッグ補助であり、短期記憶、Knowledge DB、Embedding検索の本格実装ではない。

Version 0.16では、Memory一覧・手動確認用スクリプトを追加した。
`scripts/list_memories.py` を使うと、現在DBに保存されている長期記憶を、`content`、`memory_type`、`category`、`scope`、`memory_key`、`confidence`、`is_active` などの項目と一緒に一覧確認できる。

この一覧スクリプトは読み取り専用であり、記憶の削除・更新・無効化は行わない。
`--limit`、`--category`、`--scope`、`--include-inactive`、`--search` などで確認範囲を絞れる。
`scripts/check_ver016.py` では、一覧表示スクリプトの基本実行と絞り込みが動くことを確認する。
記憶編集、記憶削除、短期記憶、Knowledge DB、Embedding検索はまだ未実装である。

Version 0.17では、Memoryの手動無効化・復元機能を追加した。
不要になった記憶を物理削除するのではなく、`is_active=False` にしてLLMへ渡さないようにする。
必要になった場合は、`is_active=True` に戻して復元できる。

`scripts/manage_memory_status.py` は、対象MemoryのIDを指定して無効化または復元を行う。
デフォルトはdry-runであり、実際にDBを変更するには `--apply` が必要である。
操作前には対象Memoryの内容を表示するため、間違ったIDを変更しにくい。

無効化済みMemoryは `scripts/list_memories.py --include-inactive` で確認できる。
Memory内容の編集、物理削除、一括無効化、自動無効化はまだ未実装である。

Version 0.18では、無効化したMemoryがMemoryContextから除外され、復元するとMemoryContextに戻ることを確認するスクリプトを追加した。
`scripts/check_ver018.py` は、テスト用Memoryを作成し、active、inactive、restoreの各状態でMemoryContextへの反映を確認する。

この確認により、`is_active=False` のMemoryがLLMへ渡されないことを、DB取得側とMemoryContext側の両方で検証できる。

また、`docs/version_1_0_test_plan.md` を追加し、Ver1.0の位置づけとテスト計画を整理した。
Ver1.0は完成版ではなく、最低限の会話、記憶、安全確認、未実装機能の正直な扱い、軽量性を実用に近い形でテストする版である。

Ver1.0テスト計画では、Preference記憶、矛盾する記憶、記憶確認頻度、自動忘却、Capability判定、ユーザー応答調整、PC上での軽量性評価を今後の重要項目として扱う。

Version 0.19では、Preference記憶の最小実装を追加した。
`ai/preference_memory.py` は、明確な「好き」「好きじゃない」「嫌い」を抽出し、`memory_key=preference:food:<target>` で保存する。

同じ対象について状態が変わった場合は、同じmemory_keyを更新する。
別の対象について好きなものが増えた場合は、別memory_keyとして複数保持する。

PersonalAI本体では、「覚えて」を含む入力からPreferenceが抽出できた場合、Preference記憶として先に保存する。
これにより、好き嫌いの単純文が二重保存されにくくなる。

記憶確認はしすぎない方針とし、曖昧な場合や矛盾が強い場合にだけ確認を検討する。
food以外のdomain、複雑なPreference抽出、自動忘却は今後の課題である。

Version 0.20では、Preference保存前の確認質問判定を追加した。
`ai/preference_confirmation.py` は、好きなものの単純追加や明確な否定では確認せず、`一番好き`、`今は / 前は`、`変更` のような更新意図がありそうな入力だけ確認候補にする。

PersonalAI本体では、`should_ask=True` の場合にPreferenceを保存せず確認質問を返す。
これにより、確認しすぎを避けつつ、曖昧なPreference更新だけユーザーに確認できる。
確認頻度は将来的にユーザーとの会話から調整する予定である。

Version 0.21では、Project Handoff、Recovery Guide、Core Principlesを追加した。
これは機能追加ではなく、PersonalAIプロジェクトを長期的に継続しやすくするための運用docsである。

`docs/project_handoff.md` は、現在状態、実装済み機能、未実装機能、主要ファイル、確認スクリプト、次の作業候補、ChatGPT / Codex再開用プロンプトをまとめる。
`docs/recovery_guide.md` は、VS Codeで開く手順、venv確認、import確認、app起動確認、checkスクリプト、Git確認、GitHub復旧、DB注意点をまとめる。
`docs/core_principles.md` は、PersonalAIの最終目標、回答精度重視、安全方針、開発方針、自律性、記憶方針、未実装機能の扱いをまとめる。

これにより、会話履歴や作業文脈が消えても、docsから再開できる状態を目指す。

## 5. Confidence Estimator と Clarification Manager の違い

Confidence EstimatorとClarification Managerは似ているが、役割が違う。

Confidence Estimatorは、「情報が足りているか」を判定する。

Clarification Managerは、「足りない場合に何を聞くか」を作る。

例:

```text
ユーザー: YouTubeをWordにまとめて
```

このとき、Confidence Estimatorは以下を判断する。

- YouTubeのURLはあるか
- Word文書の用途は分かるか
- 要約の詳しさは分かるか
- このまま進めてよいか

情報が足りない場合、Clarification Managerが以下のような質問を作る。

```text
YouTubeのURLを送ってください。提出用・共有用・勉強用のどれに近いですか？
```

初期実装では、Confidence EstimatorとClarification ManagerはPlanner周辺に統合してよい。最初から細かく分けすぎると、コードが複雑になりすぎるためである。処理が大きくなり、独立した責務として扱う必要が出てきた段階で、別クラスとして分離する。

Version 0.11では、ClarificationManagerを独立させず、Planner / Router / Executorの中に最小実装として追加した。
対象URLや対象ファイルが不足している場合、`ask_clarification` actionを作り、Executorが必要最小限の質問文を返す。

Version 0.12では、PermissionManagerを追加し、Executor実行前に許可要否とriskを確認する土台を作った。
現時点では、許可が必要な操作は実行せず `blocked=True` として止める。
実際の許可取得や許可後の再実行は今後の課題である。

## 6. 複雑性への対応方針

PersonalAIは、将来的に多くの能力を持つ可能性がある。そのため、設計上は役割を分ける。

ただし、初期実装では、すべてを最初から独立クラスにしない。まだ処理が小さい段階では、統合できるものは統合し、実装をシンプルに保つ。

方針は以下の通り。

- 設計上は責務を明確に分ける
- 初期実装では小さく始める
- 同じ責務の処理が増えたら独立クラスに分離する
- 既存機能を壊さず、少しずつ接続する
- OpenAIや外部ツールは、必要な段階で安全に追加する

この方針により、理解しやすさと拡張性の両方を保つ。

## 7. 現在実装済みのもの

現在、以下が実装済みである。

- InputAnalyzer
- CapabilityManager
- Planner
- Router
- Executor
- PermissionManager
- Plan
- Route
- Memory基礎
- Memory追加項目
- MemoryContext分類
- MemoryContext確認スクリプト
- Memory一覧表示スクリプト
- Memory手動無効化・復元
- 無効化MemoryのContext反映確認
- Ver1.0テスト計画
- Preference記憶の最小実装
- Preference確認質問の最小実装
- Project Handoff / Recovery / Core Principles
- Qwen接続

Memory基礎には、会話履歴保存、長期記憶保存、自動記憶抽出、複数記憶抽出、categoryによる記憶更新、memory_keyによる記憶更新、カテゴリ別MemoryContext作成、MemoryContextプレビュー、Memory一覧表示、手動無効化・復元、無効化MemoryのContext反映確認、Preference記憶の最小保存、Preference確認質問の最小判定が含まれる。

`.agents` フォルダは現時点では用途不明であり、現在のPersonalAI本体では未使用扱いである。
今後、Codexやエージェント設定で使う可能性があるため削除しない。

`legacy/app_buckup.py` は旧テスト用コードであり、現在の実行対象ではない。

## 8. 今後実装予定

今後、以下を追加予定である。

- GoalManager
- ConfidenceEstimator
- ClarificationManager
- Evaluator
- OpenAI連携
- Web / YouTube / PDF / Word / Vision などのTool

まずは現在のQwen、Memory、Planner、Router、Executorの流れを安定させる。その後、入力の種類やユーザーの目的に応じて、必要なモジュールを少しずつ追加していく。
