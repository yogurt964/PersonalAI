# Tool Input Integration

## 目的

Version 1.6では、Reader実装前に InputAnalyzer / CapabilityManager / Tool の連携をdry-runで確認できる土台を追加した。

この段階では、Web Reader、PDF Reader、Image Reader、YouTube Reader、PC操作、Word / Excel / PDF作成などの実処理は行わない。
ユーザー入力から「どのToolが必要そうか」「ToolRequestにするとどうなるか」「実行前確認が必要か」だけを確認する。

## InputAnalyzerの役割

InputAnalyzer は、ユーザー入力の種類を判定する。

例:

- 通常テキスト
- URL
- YouTube URL
- 要約依頼
- 文書作成依頼
- 質問

Ver1.6では、InputAnalyzerの結果をToolRequestBuilderへ渡せるようにする。
ただし、InputAnalyzerだけでToolを実行することはない。

## CapabilityManagerの役割

CapabilityManager は、PersonalAIが現在できること、できないことを判断する。

例:

- 通常会話は現在対応できる
- Memory参照やMemory保存は現在対応できる
- Web Reader / PDF Reader / Image Reader / YouTube Reader はまだ未実装
- PC操作や実ファイル作成はまだ未実装

CapabilityManagerは「能力として必要か」「今できるか」を判断する。
ToolRequestBuilderは、その判断を使って「どのToolRequestにするか」を整理する。

## ToolRequestBuilderの役割

ToolRequestBuilder は、入力から必要そうなToolRequestを作る。

Ver1.6で追加した主な要素:

- `ToolRequestDecision`
- `infer_tool_name_and_action`
- `build_tool_request_decision`

通常会話ではToolRequestを作らない。
Reader系入力やToolが必要そうな入力ではToolRequestを作るが、実行はしない。

例:

```text
こんにちは -> ToolRequestなし
URL読み取り依頼 -> web_reader / read_url / medium
YouTube要約依頼 -> youtube_reader / summarize_video / medium
PDF読み取り依頼 -> pdf_reader / read_pdf / medium
画像確認依頼 -> image_reader / analyze_image / medium
Word文書作成依頼 -> document_creator / create_document / medium
PC操作依頼 -> pc_operator / operate_pc / high または critical
```

すべて `should_execute=False` として扱う。

## ToolRegistryの役割

ToolRegistry は、Tool名からAdapterを探す役割を持つ。

Ver1.6では、ToolRegistryからAdapterを取得して利用可能性を確認できる。
ただし、Adapterの `execute()` は呼ばない。

Web Reader / PDF Reader / Image Reader / YouTube Reader はまだ未実装であり、未実装Adapterとして扱う。

## ToolPermissionの役割

ToolPermission は、ToolRequestを実行する前に確認が必要かを判断する。

判断に使う主な情報:

- `requires_permission`
- `risk_level`

medium以上のriskは原則として確認が必要である。
high / critical risk は、必ず明示確認またはブロックする。

Ver1.6ではToolPermissionの判定結果を確認するだけで、実際のTool実行はしない。

## dry-run方針

Ver1.6ではdry-runのみを行う。

dry-runで確認すること:

- Toolが必要そうか
- どのToolが必要そうか
- どのactionに相当するか
- Adapterが利用可能か
- Permission確認が必要か
- risk_levelは何か
- 実行しないこと

未実装Toolを実行したふりしない。
外部アクセス、ファイル読み取り、PC操作、文書作成は行わない。

## 将来の理想フロー

```text
入力
↓
InputAnalyzer
↓
CapabilityManager
↓
ToolRequestBuilder
↓
ToolPermission
↓
ToolRegistry
↓
Executor
↓
ToolResult
```

Ver1.6では Executor への本接続はまだ行わない。
まずはReaderやAdapterを追加する前に、入力からToolRequest、Permission、Registryまでの流れを確認できる状態にする。
Ver1.7では、dry-runやToolRequestの結果を `ToolExecutionRecord` として記録できる土台を追加した。
ただし、Ver1.7でも実際のTool実行はまだ行わない。
Ver1.8では、Reader実装前の手動テストケースを整理した。
Ver2.0 Reader実装時には、このテストケースを基準に実装前後の挙動を比較する。
