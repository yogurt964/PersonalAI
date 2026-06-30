# Tool Permission Design

## 目的

Version 1.5では、Toolを実行する前に安全確認するための土台を追加した。

この段階では、Web Reader、PDF Reader、Image Reader、YouTube Reader、PC操作、Word / Excel / PDF作成などの実処理は行わない。
実際のReaderやAdapterを動かす前に、ToolRequestの `requires_permission` と `risk_level` を見て、確認が必要か、ブロックすべきかを判断できるようにする。

## ToolPermissionDecision

`ToolPermissionDecision` は、Tool実行前の安全判定結果を表す。

主な項目:

- `allowed`: 実行候補として許可できるか
- `needs_user_confirmation`: ユーザー確認が必要か
- `risk_level`: 判定に使った危険度
- `reason`: 判定理由
- `executed`: 実際に実行したか

Ver1.5では、判定上 `allowed=True` でも `executed=False` のままにする。
これは、Permission判定は「実行前確認」であり、Tool実行そのものではないためである。

## evaluate_tool_permission

`evaluate_tool_permission(request, permission_manager=None)` は、`ToolRequest` を受け取り `ToolPermissionDecision` を返す。

基本方針:

- `risk_level=none`: 実行なしの説明として確認不要
- `risk_level=low` かつ `requires_permission=False`: 確認不要
- `risk_level=medium`: 原則として確認が必要
- `risk_level=high`: 必ず明示確認が必要
- `risk_level=critical`: 原則ブロック、または強い確認が必要
- 未知の `risk_level`: 安全側に倒して確認が必要

## build_permission_message

`build_permission_message(decision, request)` は、ユーザーに確認するための短い説明文を作る。

説明文には以下を含める。

- どのToolを使おうとしているか
- 何をしようとしているか
- `risk_level`
- 確認が必要か
- 未許可なら実行しないこと

## ToolRequestとの関係

`ToolRequest` には、Ver1.4時点で以下の項目がある。

- `requires_permission`
- `risk_level`

Ver1.5では、この2つをTool Permission判定に使う。
ToolRequestは「何をしたいか」を表し、ToolPermissionDecisionは「実行前にどう扱うか」を表す。

## PermissionManagerとの関係

既存の `core/permission_manager.py` は、PlanやRouteのactionを見て許可が必要か判断するための基礎である。

Ver1.5の `core/tool_permission.py` は、ToolRequest向けの軽量な判定として独立して動く。
現時点では既存PermissionManagerを大きく改造しない。

将来的には、以下のように役割を整理して統合する予定である。

- CapabilityManager: その能力があるかを判断する
- PermissionManager: 操作全体の許可方針を判断する
- Tool Permission: ToolRequest単位で実行前確認を判断する
- ToolRegistry / ToolAdapter: 実際に使うAdapterを選び、実行する

## 未許可Toolの扱い

未許可ならToolを実行しない。

また、実行していないToolを実行したと言わない。
Web Reader、PDF Reader、Image Reader、YouTube Readerが未実装の段階では、読んだふりや実行したふりをしない。

ToolResultの `executed=False` は、未実行、未許可、未実装を明確にするために使う。

## risk_levelの方針

```text
none: 実行なし、説明のみ
low: 読み取りや安全な内部確認など。場合によっては確認不要
medium: ファイル読み取り、外部情報取得、文書作成準備など。原則確認が必要
high: ファイル変更、送信、削除、PC操作、外部への書き込みなど。必ず明示確認が必要
critical: 削除、公開、送信、課金、認証情報、危険操作など。原則ブロックまたは強い確認が必要
```

Ver1.5では実処理は行わない。
ReaderやAdapterの本格実装は、Ver2.0以降の候補として扱う。
