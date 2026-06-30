# Tool Execution Log Design

## 目的

Version 1.7では、Tool実行ログと結果記録の設計を追加した。

この段階では、Web Reader、PDF Reader、Image Reader、YouTube Reader、PC操作、Word / Excel / PDF作成などの実処理は行わない。
DB保存もまだ行わず、Tool実行前判断、許可確認、実行結果、未実装扱いを記録できるデータ構造とインメモリ記録だけを用意する。

## ToolExecutionRecord

`ToolExecutionRecord` は、1回のTool実行、dry-run、または未実装Tool確認を記録するデータである。

主な項目:

- `record_id`: ログ1件ごとのID
- `tool_name`: 対象Tool名
- `action`: 実行しようとした操作
- `risk_level`: 危険度
- `requires_permission`: 実行前許可が必要か
- `permission_needed`: Permission判定上、確認が必要か
- `permission_allowed`: Permission判定上、実行候補として許可できるか
- `adapter_available`: Adapterが利用可能か
- `attempted`: 実行を試みたか
- `executed`: 実際に実行されたか
- `success`: 処理結果として成功扱いか
- `message`: 結果や未実行理由
- `error`: エラー情報
- `original_input`: 元のユーザー入力
- `created_at`: 作成日時
- `data`: 結果データ

## ToolExecutionLogger

`ToolExecutionLogger` は、`ToolExecutionRecord` をインメモリで一時的に保持する軽量ロガーである。

主なメソッド:

- `add(record)`: recordを追加する
- `list_records()`: 記録済みrecord一覧を返す
- `latest()`: 最新recordを返す
- `clear()`: インメモリrecordを消す
- `count()`: record数を返す

Ver1.7ではDB保存を行わないため、アプリを終了すればこのログは失われる。
永続保存は将来Versionで検討する。

## build_tool_execution_record

`build_tool_execution_record` は、以下をまとめて `ToolExecutionRecord` を作る。

- `ToolRequest`
- `ToolPermissionDecision`
- `ToolResult`

`ToolRequest` からは、`tool_name`、`action`、`risk_level`、`requires_permission` を記録する。
`ToolPermissionDecision` からは、Permission確認が必要か、実行候補として許可できるかを記録する。
`ToolResult` からは、`success`、`executed`、`message`、`error`、`data` を記録する。

## executed=Falseを重視する理由

Toolログでは `executed=False` を重要視する。

実際にexecuteしていないなら `executed=False` として記録する。
dry-runなら `attempted=False` または `executed=False` として記録する。
未許可なら `executed=False` として記録する。
未実装Toolは `success=False` / `executed=False` として記録する。

これにより、実行したふりをしない状態をログ上でも確認できる。

## successとexecutedの違い

`success=True` でも `executed=False` の場合があり得る。

例:

- dry-run previewとしては成功した
- Permission判定の整理は成功した
- 実際のTool実行はしていない

そのため、`success` は処理結果の成否、`executed` は実際にToolを実行したかを表す。
この2つを混同しない。

## DB保存について

Ver1.7ではDB保存はまだ行わない。
`data/personal_ai.db` は今回変更しない。

将来DB保存を追加する場合は、既存DBやMemoryを壊さないmigration方針が必要である。
Tool実行ログ用テーブルを追加する場合も、既存Memoryや会話履歴とは分けて設計する。

## 今後の接続予定

将来的には、以下の流れでTool実行ログを使う。

```text
ToolRequest
↓
ToolPermissionDecision
↓
ToolRegistry / ToolAdapter
↓
ToolResult
↓
ToolExecutionRecord
↓
ToolExecutionLogger または DB保存
```

Ver1.7では、ログの形を整えるだけで、外部アクセス、ファイル読み取り、PC操作、文書作成、DB保存は行わない。
