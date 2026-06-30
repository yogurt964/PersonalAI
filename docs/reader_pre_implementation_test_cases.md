# Reader Pre-Implementation Test Cases

## 目的

Version 1.8では、Ver2.0 Reader実装前の手動テストケースを整理した。

このドキュメントは、Web Reader、YouTube Reader、PDF Reader、Image Reader、File Reader、Document Creator、PC Operatorを実装する前に、現在のdry-run設計が期待通りに動くか確認するための基準である。

今回はReaderを実装しない。
実際のWebアクセス、YouTubeアクセス、PDF読み取り、画像解析、ローカルファイル読み取り、PC操作、Word / Excel / PDF作成はしない。

Ver2.0でReaderを実装するときは、このテストケースを実装前後の比較に使う。
実装後も、未許可の操作や未実装Toolを実行したふりをしないことを確認する。

## 基本方針

- 通常会話ではToolRequestを作らない
- Reader系入力ではToolRequest候補を作る
- ToolRequestを作っても `should_execute=False` を維持する
- medium以上のriskはToolPermissionで確認が必要になる
- PC操作や削除はhighまたはcriticalとして扱う
- ToolExecutionLogではdry-runでも `executed=False` を記録できる
- 未実装Toolは `success=False` / `executed=False` で記録する
- 実行したふりをしない

## 手動テストケース一覧

| No | 入力例 | 期待Tool | 期待Action | risk_level | requires_permission | should_execute | 実際に実行するか | 確認ポイント |
|---|---|---|---|---|---|---|---|---|
| 1 | こんにちは | なし | なし | none | False | False | 実行しない | 通常会話ではToolRequestを作らない |
| 2 | このURLを読んでください https://example.com | web_reader | read_url | medium | True | False | 実行しない | Webアクセスせず、web_reader候補になる |
| 3 | このYouTube動画を要約してください https://youtu.be/example | youtube_reader | summarize_video | medium | True | False | 実行しない | YouTubeをweb_readerに誤分類しない |
| 4 | このPDFを読んでください | pdf_reader | read_pdf | medium | True | False | 実行しない | PDF本文を読まず、pdf_reader候補になる |
| 5 | sample.pdf を読んでください | pdf_reader | read_pdf | medium | True | False | 実行しない | PDFファイル名らしき入力をpdf_reader候補にする |
| 6 | この画像を見てください | image_reader | analyze_image | medium | True | False | 実行しない | 画像解析せず、image_reader候補になる |
| 7 | image.png を解析してください | image_reader | analyze_image | medium | True | False | 実行しない | 画像ファイル名らしき入力をimage_reader候補にする |
| 8 | このファイルを読んでください | file_reader | read_file | medium | True | False | 実行しない | ローカルファイルを読まず、file_reader候補になる |
| 9 | Word文書を作ってください | document_creator | create_document | medium | True | False | 実行しない | Wordファイルを作らず、document_creator候補になる |
| 10 | Excelで表を作ってください | document_creator | create_document | medium | True | False | 実行しない | Excelファイルを作らず、document_creator候補になる |
| 11 | PCを操作してください | pc_operator | operate_pc | high | True | False | 実行しない | PC操作せず、permission_needed=Trueになる |
| 12 | ファイルを削除してください | pc_operator | operate_pc | highまたはcritical | True | False | 実行しない | 削除系は安全側に倒し、実行しない |

## 通常会話の確認

入力例:

```text
こんにちは
```

期待:

- ToolRequestを作らない
- `requires_tool=False`
- `tool_request=None`
- `should_execute=False`
- MemoryやPreferenceを無理に出さず、自然に短く返す

## URL Reader候補の確認

入力例:

```text
このURLを読んでください https://example.com
```

期待:

- `tool_name=web_reader`
- `action=read_url`
- `risk_level=medium`
- `requires_permission=True`
- `should_execute=False`
- 実際にWebアクセスしない

## YouTube Reader候補の確認

入力例:

```text
このYouTube動画を要約してください https://youtu.be/example
```

期待:

- `tool_name=youtube_reader`
- `action=summarize_video`
- `risk_level=medium`
- `requires_permission=True`
- `should_execute=False`
- `web_reader` に誤分類しない
- 実際にYouTubeへアクセスしない

## PDF Reader候補の確認

入力例:

```text
このPDFを読んでください
sample.pdf を読んでください
```

期待:

- `tool_name=pdf_reader`
- `action=read_pdf`
- `risk_level=medium`
- `requires_permission=True`
- `should_execute=False`
- 実際にPDFを読まない

## Image Reader候補の確認

入力例:

```text
この画像を見てください
image.png を解析してください
```

期待:

- `tool_name=image_reader`
- `action=analyze_image`
- `risk_level=medium`
- `requires_permission=True`
- `should_execute=False`
- 実際に画像解析しない

## File Reader候補の確認

入力例:

```text
このファイルを読んでください
```

期待:

- `tool_name=file_reader`
- `action=read_file`
- `risk_level=medium`
- `requires_permission=True`
- `should_execute=False`
- 実際にローカルファイルを読まない

## Document Creator候補の確認

入力例:

```text
Word文書を作ってください
Excelで表を作ってください
```

期待:

- `tool_name=document_creator`
- `action=create_document`
- `risk_level=medium`
- `requires_permission=True`
- `should_execute=False`
- 実際にWord / Excel / PDFファイルを作成しない

## PC Operator候補の確認

入力例:

```text
PCを操作してください
ファイルを削除してください
```

期待:

- `tool_name=pc_operator`
- `action=operate_pc`
- `risk_level=high` または `critical`
- `requires_permission=True`
- `permission_needed=True`
- `should_execute=False`
- 実際にPC操作しない

## ToolPermission確認

確認観点:

- URL、PDF、画像、ファイル、文書作成などのmedium riskは確認が必要
- PC操作や削除などのhigh / critical riskは確認が必要
- criticalは安全側に倒す
- 未許可なら実行しない
- Permission判定自体も `executed=False` を維持する

## ToolExecutionLog確認

確認観点:

- dry-runでも `ToolExecutionRecord` を作れる
- ToolRequestの `tool_name`、`action`、`risk_level` が記録される
- Permission判定の `permission_needed` が記録される
- ToolResultなしの場合は `success=False` / `executed=False`
- 未実装ToolResultの場合は `success=False` / `executed=False`
- `executed=False` により、実行したふりをしていないことを確認できる

## Ver2.0実装時の使い方

Ver2.0 Reader実装時は、この手動テストケースを以下のように使う。

1. 実装前にVer1.8の期待挙動を確認する
2. Reader実装後に、どのケースが実行可能になったか確認する
3. 実装後も、未許可なら実行しないことを確認する
4. 未実装のReaderやAdapterは、引き続き実行したふりをしないことを確認する
