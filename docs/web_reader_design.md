# Web Reader Design

## 目的

Ver2.0で、Web Reader最小実用版を追加した。
Ver2.1では、手動実行テストと会話UI接続方針を整理する。

Web Readerは、Reader方面の最初の実用テスト版である。
完成版ではなく、http / https URLを安全に読み取り、ToolRequest、Permission、ToolResult、ToolExecutionLogまでつなぐための最小実装である。

## Versionごとの位置づけ

- Ver2.0: Web Reader最小実用版
- Ver2.1: 手動実行テストと会話UI接続方針の整理
- Ver2.2: URL入力検出から確認メッセージ生成までのdry-run
- Ver2.3: URL確認メッセージを会話返答として表示するdry-run接続
- Ver2.4: 確認応答の前段処理とToolRequest候補作成dry-run
- Ver2.5: user_confirmed=True後にToolRunner経由でWeb Readerを実行
- Ver2.6: 実Web手動テスト結果をdocsへ整理
- Ver2.8: Web Reader結果の会話品質を改善
- Ver2.9: Reader結果のMemory保存方針をdocs化

Ver2.1では、会話UI自動接続はまだしない。
URLを検出しただけで自動Webアクセスしない。
自動チェックでは実Webアクセスしない。
実Webアクセスはユーザー確認つきの手動確認でのみ行う。
PDF Reader / Image Reader / YouTube Reader / File Reader は今後の段階追加とする。

Ver2.2では、URLを検出し、Web Reader実行前の確認メッセージ生成までをdry-runで扱う。
この段階ではToolRunnerは呼ばない。
WebReaderAdapterのfetchは実行しない。
会話UIへの実接続はまだしない。
`user_confirmed=True` による実行接続は今後扱う。

Ver2.3では、URL確認メッセージを会話返答として表示するdry-run接続を扱う。
この段階でもWebアクセスはまだしない。
ToolRunnerは会話UIから呼ばない。
WebReaderAdapterのfetchは実行しない。
`user_confirmed=True` 後の実行接続は今後扱う。

Ver2.4では、確認応答を肯定・否定・別話題に分け、肯定時にToolRequest候補をdry-runで作る。
この段階でも実行はまだしない。
ToolRunnerは会話UIから呼ばない。
run_tool_requestは会話UIから呼ばない。
WebReaderAdapterのfetchは実行しない。
実Webアクセスしない。

Ver2.5では、保留中の確認に対する肯定応答がある場合だけ、`user_confirmed=True` としてToolRunner経由でWeb Readerを実行する。
URL検出だけではWebアクセスしない。
自動チェックではfake fetcherを使い、実Webアクセスしない。
成功時はtitle / final_url / text_previewを返す。
失敗時は読めたふりをしない。
Reader結果のMemory保存はまだしない。

Ver2.6では、Ver2.5の会話UI接続を使い、ユーザー環境で `https://example.com` の実Web手動確認が成功したことをdocsへ記録した。
手動確認では、確認メッセージ表示後に `はい` と答えた場合だけWeb Readerが実行され、`Example Domain` と `text_preview` が返った。
自動チェックでは引き続きfake fetcherを使い、実Webアクセスしない。
Reader結果のMemory保存はまだしない。
PDF Reader / Image Reader / YouTube Reader / File Reader は今後の段階追加とする。

Ver2.8では、Web Reader成功時の会話返答を見やすくした。
タイトル、URL、本文プレビューを分けて表示し、本文プレビューの余分な空白を整理する。
長すぎる本文プレビューは短く表示する。
失敗時は読めたふりをせず、理由と次にできることを返す。
自動チェックではfake fetcherを使い、実Webアクセスしない。
Reader結果のMemory保存はまだしない。

Ver2.9では、Reader結果のMemory保存方針をdocs化した。
Web Reader結果を将来保存する場合は、本文全文を勝手に保存せず、Memory CandidateやProject Knowledgeなどの中間形式を使う。
保存前にユーザー確認が必要な条件を整理した。
Web Reader結果のMemory保存はまだしない。

## Web Readerの責務

Web Readerの責務:

- http / https URLを扱う
- ユーザー入力やToolRequestからURLを抽出する
- URLのHTMLを取得する
- HTMLから最低限の本文テキストを取り出す
- 成功時も失敗時もToolResultを返す
- 実行結果をToolExecutionLogに記録できる形にする
- 読めなかった場合に実行したふりをしない

## 対応範囲

対応するもの:

- `http://` URL
- `https://` URL
- 通常のHTMLページ
- `<title>`、`h1`、`p` などから取れる最低限のテキスト

対応しないもの:

- JavaScript実行が必要なページ
- ログインが必要なページ
- 動的に生成される本文の完全取得
- PDF Reader
- Image Reader
- YouTube Reader
- File Reader
- PC操作
- 文書作成

PDF Reader / Image Reader / YouTube Reader / File Reader はまだ未実装である。

## URL抽出方針

`extract_url_from_text` は、入力テキストから最初の http / https URLを取り出す。

URLが見つからない場合、Web Readerは実行しない。
この場合は `executed=False` とし、URLがないことをmessageとerrorで返す。

## HTMLテキスト化方針

`strip_html_to_text` は、HTMLから本文テキストを取り出す。

方針:

- 標準ライブラリの `html.parser` を使う
- script / style / noscript の中身は本文として扱わない
- JavaScriptは実行しない
- 取得できたテキストは長すぎないように制限する

## ToolRequestとの関係

Web Readerは、以下のToolRequestを想定する。

```text
tool_name: web_reader
action: read_url
risk_level: medium
requires_permission: True
```

URLは `request.input_data["url"]` を優先する。
なければ `request.input_data["original_input"]` から抽出する。

## Permissionとの関係

Web Readerは外部アクセスを行うため、Permission確認が必要である。

`run_tool_request` は `evaluate_tool_permission` を呼び、`user_confirmed=True` のときだけ実行へ進む。
`user_confirmed=False` の場合は未許可なら実行しない。

自動的に外部Webへアクセスしないことを重視する。

## ToolResultとの関係

Web Readerは必ずToolResultを返す。

成功時:

- `success=True`
- `executed=True`
- `data["url"]`
- `data["final_url"]`
- `data["title"]`
- `data["text"]`
- `data["text_preview"]`

URLなしや不正URLなど、fetch前に止まった場合:

- `success=False`
- `executed=False`

fetchを試みたあとに失敗した場合:

- `success=False`
- `executed=True`
- `error` に失敗理由を入れる

## ToolExecutionLogとの関係

`run_tool_request` は、ToolResultからToolExecutionLog用のrecordを作る。

`executed=True` は、実際にTool実行へ進んだことを表す。
`executed=False` は、未許可、URLなし、未実装、未実行などで実行していないことを表す。

successとexecutedは混同しない。
たとえば、Webアクセスを試みたが失敗した場合は `success=False` / `executed=True` になる。

## 実行したふりをしない方針

Web Readerは、読めないページを読めたとは言わない。
未許可なら実行しない。
未実装Readerは未実装と返す。
実行したふりをしない。

## 自動check方針

自動checkでは実Webアクセスしない。

`WebReaderAdapter(fetcher=fake_fetcher)` のようにfake fetcherを差し込み、固定HTMLで確認する。
実Webアクセスは、ユーザー確認つきの手動確認で行う。

## 今後の課題

- 文字コードやContent-Typeの扱い改善
- 取得失敗時の代替案提示
- Memory Candidate生成のdry-run設計
- PDF Reader / Image Reader / YouTube Reader / File Reader の段階追加
