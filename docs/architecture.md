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

## 現在の構成

現在のコードは、主に以下のフォルダに分かれている。

- `ai`: LLM呼び出し、記憶抽出、記憶コンテキスト作成
- `database`: 会話履歴と長期記憶の保存・取得
- `core`: PersonalAI本体と、今後の中核機能

## 今後追加予定の構成

今後のエージェント化に向けて、以下の要素を追加予定である。

- `CapabilityManager`: PersonalAIが使える能力を管理する。Version 0.5でPersonalAI内部に接続済み
- `InputAnalyzer`: ユーザー入力を構造化する。Version 0.9でPersonalAI内部に接続済み
- `Planner`: ユーザーの目的に対して実行計画を立てる。Version 0.5でPersonalAI内部に接続済み
- `Router`: 用途に応じて使う道具や処理系を選ぶ。Version 0.5でPersonalAI内部に接続済み
- `Executor`: 選ばれた行動やツールを実行する。Version 0.8でPersonalAI内部に接続済み
- `Evaluator`: 出力や行動結果を評価する
