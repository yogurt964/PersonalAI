# Reader Implementation Plan v2

## 目的

Ver1.9では、Ver2.0 Reader実装計画を整理した。

Ver2.0は、Reader方面の最初の実用テスト版である。
完成版を目指すのではなく、少なくとも1つのReaderが実際に動き、ToolRequest、Permission、ToolResult、ToolExecutionLogまで安全につながる状態を目指す。

Ver1.9ではReaderを実装せず、計画整理だけを行った。
Ver2.0ではWeb Reader最小実用版を実装した。
PDF / Image / YouTube / File Reader は次段階である。

## Ver2.0を付ける条件

Ver2.0を付ける最低条件は以下とする。

- 少なくとも1つのReaderが実際に動く
- ToolRequestからReader Adapterへつながる
- Reader実行前にPermission確認を通る
- ReaderがToolResultを返す
- Reader実行結果をToolExecutionLogに記録する
- 未実装Readerは未実装と返す
- 実行したふりをしない
- `docs/reader_pre_implementation_test_cases.md` の手動テストケースを通る
- docsに「できること / できないこと」が整理されている

Ver2.0は完成版ではない。
「最低限使えるReaderが1つあり、できないことを正直に扱える」状態を区切りにする。

## 最初の実装対象

最初の候補は Web Reader とする。

おすすめの最初の実装対象は、Web Readerの最小実用版である。

理由:

- URL入力の需要が高い
- Ver1.6のToolRequest dry-runで `web_reader / read_url` がすでに整理されている
- Permission確認、ToolResult、ToolExecutionLogまでの接続確認がしやすい
- 失敗時や未対応サイトで「読めたふりをしない」設計を確認しやすい

## Reader実装順序

Ver2.0では、Web Readerを最初の実装候補にする。

段階的な追加方針:

1. Web Reader
2. PDF Reader は段階的に追加
3. File Reader はPDF Readerと前後して段階的に追加
4. Image Reader は段階的に追加
5. YouTube Reader は段階的に追加

YouTube Readerは、URL処理、動画情報取得、字幕取得など分岐が多いため、Web Readerより後に回してよい。
Image Readerも専用処理が必要になる可能性があるため、段階的に追加する。

## Reader共通方針

Readerは、Tool / Adapterとして扱う。

共通の流れ:

```text
ユーザー入力
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
Reader Adapter
↓
ToolResult
↓
ToolExecutionLog
```

共通入力:

- `ToolRequest.tool_name`
- `ToolRequest.action`
- `ToolRequest.input_data`
- `ToolRequest.requires_permission`
- `ToolRequest.risk_level`

共通出力:

- `ToolResult.success`
- `ToolResult.message`
- `ToolResult.data`
- `ToolResult.error`
- `ToolResult.executed`

Permission方針:

- Reader実行前にはPermission確認を行う
- 外部アクセスやファイル読み取りは原則 `risk_level=medium`
- `requires_permission=True` を基本とする
- 許可なしの外部アクセスは行わない

ToolExecutionLog方針:

- 実行した場合はToolExecutionLogに記録する
- 失敗時もToolExecutionLogに記録する
- 未実装Readerや未許可Readerも `executed=False` として記録する
- 実行したふりをしない

## Reader設計マトリクス

| Reader名 | tool_name | action | 入力例 | 出力例 | risk_level | requires_permission | ToolResult方針 | ToolExecutionLog方針 | Ver2.0対象か | 備考 |
|---|---|---|---|---|---|---|---|---|---|---|
| Web Reader | `web_reader` | `read_url` | `https://example.com` | ページ本文、タイトル、取得失敗理由 | medium | True | 成功時は本文要約用データ、失敗時は理由を返す | 成功/失敗/未許可を記録 | 対象 | Ver2.0の最初の候補 |
| PDF Reader | `pdf_reader` | `read_pdf` | `sample.pdf` | 抽出テキスト、ページ情報、失敗理由 | medium | True | 読めた範囲と失敗理由を返す | 実行結果とページ数などを記録 | Ver2.x | PDF Reader は段階的に追加 |
| Image Reader | `image_reader` | `analyze_image` | `image.png` | 画像説明、OCR候補、失敗理由 | medium | True | 画像解析結果または未対応理由を返す | 解析有無と失敗理由を記録 | Ver2.x | Image Reader は段階的に追加 |
| YouTube Reader | `youtube_reader` | `summarize_video` | `https://youtu.be/example` | 動画情報、字幕、要約、失敗理由 | medium | True | 字幕や動画情報の取得可否を返す | 取得できた情報と失敗理由を記録 | Ver2.x | YouTube Reader は段階的に追加 |
| File Reader | `file_reader` | `read_file` | `notes.txt` | ファイル本文、文字コード、失敗理由 | medium | True | 読めた本文と失敗理由を返す | ファイル種別、成功/失敗を記録 | Ver2.x | ローカルファイル読み取りの基礎 |
| Document Creator | `document_creator` | `create_document` | `Word文書を作って` | 作成予定内容、実ファイル作成結果 | medium/high | True | Ver2.0では実作成しない | 未実行として記録 | 対象外 | Readerではない比較対象 |
| PC Operator | `pc_operator` | `operate_pc` | `PCを操作して` | 操作結果またはブロック理由 | high/critical | True | Ver2.0では実操作しない | 未実行またはブロックを記録 | 対象外 | Readerではない高リスク対象 |

## Ver2.0でやること

Ver2.0でやること:

- Web Readerの最小実用版を実装
- URL入力から `web_reader` ToolRequestを作る
- Permission確認を行う
- Web Reader Adapterが実際にURLを読み取る
- ToolResultを返す
- ToolExecutionLogに記録する
- 失敗時はエラーを正直に返す
- 未対応サイトや失敗をできたふりしない
- できること / できないことをdocsに整理する

## Ver2.0でやらないこと

Ver2.0でやらないこと:

- YouTube動画の完全要約
- 複雑なPDF解析
- 画像認識の高度化
- PC自動操作
- Word / Excel / PDF生成
- 自動で外部送信する処理
- 許可なしの外部アクセス
- すべてのサイトを完全に読めると見なすこと

## Ver2.x以降でやること

Ver2.x以降でやること:

- Ver2.1: PDF Reader
- Ver2.2: File Reader
- Ver2.3: Image Reader
- Ver2.4: YouTube Reader
- Ver2.x: Reader結果のMemory保存方針
- Ver2.x: Reader結果の要約品質改善
- Ver2.x: Reader失敗時の再試行や代替案提示

## 手動テストとの関係

Reader実装時は、`docs/reader_pre_implementation_test_cases.md` を基準にする。

Ver2.0実装前:

- dry-runで期待Toolが選ばれることを確認する
- `should_execute=False` と `executed=False` が維持されることを確認する
- 未実装Readerを実行したふりしないことを確認する

Ver2.0実装後:

- 実装したReaderだけが実行可能になることを確認する
- 未実装Readerは引き続き未実装と返すことを確認する
- Permission確認なしに外部アクセスしないことを確認する
- ToolResultとToolExecutionLogに結果が残ることを確認する

## Ver1.10で確認してから進む案

Ver2.0実装へ進む前に、Ver1.10でVer1.x総仕上げ確認を行う案を推奨する。

Ver1.10で確認したいこと:

- Ver1.xで追加したTool受け口、Permission、dry-run、ExecutionLog、手動テストdocsがそろっている
- `scripts/run_ver1_checks.py` が通る
- Reader実装前の未実装扱いが正直に保たれている
- DB、Memory、会話品質が壊れていない

この確認後に、Ver2.0としてWeb Reader最小実用版へ進む。
Ver1.10後は、Ver2.0 Web Reader最小実用版の実装へ進む候補とする。
Ver2.0ではWeb Reader最小実用版を実装し、PDF / Image / YouTube / File Reader はVer2.xで段階的に追加する。
