# Tool / Adapter Design

## 目的

Version 1.4では、Reader追加前のTool / Adapter受け口を追加した。

この段階では、Web Reader、PDF Reader、Image Reader、YouTube Reader、PC操作、Word / Excel / PDF作成などの実処理は行わない。
将来それらを安全に接続するために、依頼と結果の共通データ構造、Adapterの共通インターフェース、Registryだけを整理する。

## ToolRequest

`ToolRequest` は、PersonalAIがTool / Adapterへ渡す依頼内容を表す。

主な項目:

- `tool_name`: 使いたいTool名
- `action`: 実行したい操作
- `input_data`: Toolへ渡す入力データ
- `requires_permission`: 実行前に許可が必要か
- `risk_level`: 操作の危険度

`requires_permission` と `risk_level` は、Ver1.5で追加したTool Permission判定に使う。
Toolを実行する前に、ユーザー確認が必要か、危険度がどれくらいかを判断するための情報である。

将来的には、Planner / Router / Executorが作った判断をもとに `ToolRequest` を作り、Tool / Adapterへ渡す。
Ver1.6では `ToolRequestBuilder` が、入力から必要そうなToolRequestを作る準備を追加した。
ただし、Adapter実行はまだ行わない。

## ToolResult

`ToolResult` は、Tool / Adapterの実行結果を共通形式で表す。

主な項目:

- `success`: 成功したか
- `message`: ユーザーや上位処理へ返す説明
- `data`: 実行結果のデータ
- `error`: エラー内容
- `executed`: 実際に実行したか

`executed=False` は重要である。
未実装Toolや許可前の処理では、実行したふりをしないために `executed=False` を返す。
未許可、未実行、未実装を明確に分けるためにも `executed=False` を使う。
Ver1.7では、ToolResultは `ToolExecutionRecord` に記録される。
`executed` は実行済みかどうかを示す重要フィールドであり、`success` と混同しない。

## ToolAdapter

`ToolAdapter` は、将来の各Adapterが合わせる共通インターフェースである。

主なメソッド:

- `is_available()`: 今そのToolが利用可能かを返す
- `execute(request)`: `ToolRequest` を受け取り `ToolResult` を返す

Ver1.4では、実処理を持つAdapterはまだ追加しない。
Web Reader / PDF Reader / Image Reader / YouTube Reader はまだ未実装である。

## ToolRegistry

`ToolRegistry` は、登録済みAdapterを名前で管理する。

主な役割:

- Adapterを登録する
- `tool_name` でAdapterを取得する
- 登録済みTool一覧を返す
- Toolが利用可能か確認する
- 未登録Toolの場合は `UnimplementedToolAdapter` を返す

Ver1.4では、以下のToolを未実装Adapterとして扱う。

- `web_reader`
- `pdf_reader`
- `image_reader`
- `youtube_reader`
- `file_reader`
- `document_creator`
- `pc_operator`

## 未実装Toolの扱い

未実装Toolは、実行したふりをしない。

`UnimplementedToolAdapter` は以下の方針で動く。

- `is_available()` は `False` を返す
- `execute()` は `ToolResult` を返す
- `success=False`
- `executed=False`
- messageには「未実装」であることを含める

これにより、Web ReaderやPDF Readerが未実装の段階でも、PersonalAIが読んだふりや実行したふりをしない設計にできる。

## 今後の接続予定

将来的には、ExecutorやPlanner / RouterからToolRegistryへ接続していく。

想定フロー:

```text
InputAnalyzer
↓
Planner
↓
Router
↓
Executor
↓
ToolRegistry
↓
ToolAdapter
↓
ToolResult
```

PermissionManagerや `risk_level` とも連携する予定である。
外部読み取り、ファイル作成、PC操作など、ユーザーに影響する操作は実行前に許可確認する。

Ver1.4では実処理は行わない。
Readerや外部操作の本格実装はVer2.0以降の候補として扱う。
