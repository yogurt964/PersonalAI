# Web Reader Manual Test

## 目的

Ver2.0で、Web Reader最小実用版を追加した。

Ver2.1では、Web Readerを会話UIへ接続する前に、実Webアクセスを安全に手動確認するための手順を整理する。
目的は便利に自動実行することではなく、`user_confirmed`、Permission、ToolResult、ToolExecutionLogの扱いを明確にすることである。
実行はToolRunner経由で行い、WebReaderAdapterを明示登録した場合だけ進める。

## 実Webアクセスを行う前提条件

実Webアクセスを行う前提条件:

- ユーザーが実Webアクセスを明示的に許可している
- `user_confirmed=True` を明示している
- `WebReaderAdapter` を `ToolRegistry` に明示登録している
- 対象URLが http / https URLである
- 実Webアクセス結果を `ToolExecutionLog` に残す

`user_confirmed=False` ではWebアクセスしない。
URLを検出しただけで自動Webアクセスしない。

## 推奨テストURL

推奨テストURL:

```text
https://example.com
```

このURLは手動実行テストの対象として扱う。
自動チェックでは実Webアクセスしない。

## 期待される確認項目

実Webアクセスの手動確認では、以下を見る。

- `success`
- `executed`
- `title`
- `ToolExecutionLog`

成功時の目安:

- `result.success=True`
- `result.executed=True`
- `data.title` に `Example Domain` が入る
- log recordにも `success=True` / `executed=True` が残る
- `logger.count` が増える

## 手動確認の流れ

手動確認の想定:

1. `ToolRequest` を作る
2. `ToolRegistry` に `WebReaderAdapter` を登録する
3. `ToolExecutionLogger` を用意する
4. `run_tool_request(..., user_confirmed=True)` を呼ぶ
5. `ToolResult` と log record を確認する

`user_confirmed=False` の確認も先に行い、Webアクセスしないことを確認する。

## 失敗時の確認ポイント

失敗時は、以下を確認する。

- ネットワークに接続できるか
- fetcherが正しく動いているか
- Permission / confirmation が正しいか
- `user_confirmed=True` になっているか
- URL抽出が成功しているか
- 例外処理で `success=False` / `executed=True` または `executed=False` が正しく返っているか

Webアクセスを試みた後に失敗した場合は `success=False` / `executed=True` である。
fetch前にURLなしや未許可で止まった場合は `executed=False` である。

## 自動チェック方針

自動チェックでは実Webアクセスしない。

`scripts/check_ver200.py` や `scripts/check_ver210.py` では、fake fetcherやdocs確認のみを使う。
DBに書き込まない。
`data/personal_ai.db` を変更しない。

## 会話UIとの関係

Ver2.5では、会話UIからWeb Readerを実行できる。

URLを入力しただけでWeb Readerを実行しない。
ユーザーに「Webを読み取ってよいか」を確認し、保留中の確認に対して肯定応答がある場合だけ `user_confirmed=True` にする。
その場合だけToolRunner経由でWeb Readerを実行する。

読めなかった場合は、読めたふりをしない。
成功時はtitle / final_url / text_previewを確認する。
Reader結果のMemory保存はまだ行わない。

## Ver2.5 実Web手動確認結果

Ver2.5で、会話UIからのWeb Reader実行をユーザー環境で手動確認した。

確認URL:

```text
https://example.com
```

実行コマンド:

```powershell
venv\Scripts\python.exe -B app.py
```

入力:

```text
このURLを読んで https://example.com
```

確認メッセージ:

```text
このURLをWeb Readerで読み取ってもよいですか？
https://example.com

外部Webへアクセスするため、実行前に確認が必要です。
```

続けて入力:

```text
はい
```

結果:

- 確認メッセージが表示された
- `はい` の後にWeb Readerが実行された
- タイトルとして `Example Domain` が返った
- `text_preview` が返った
- `git status` は clean だった

実際の返答要点:

```text
Web Readerで読み取りました。

タイトル: Example Domain
URL: https://example.com
本文プレビュー:
Example Domain This domain is for use in documentation examples without needing permission. Avoid use in operations. Learn more
```

## Ver2.6で記録した安全方針

Ver2.6では、上記の実Web手動確認結果をdocsに整理した。

自動チェックでは引き続きfake fetcherを使い、実Webアクセスしない。
実Webアクセスは、ユーザー確認つきの手動確認でのみ行う。
Reader結果のMemory保存はまだ行わない。

## Ver2.8での表示改善

Ver2.8では、Web Reader結果の会話品質を改善した。

成功時は、タイトル、URL、本文プレビューを分けて表示する。
本文プレビューの余分な空白を整理し、長すぎる場合は短く表示する。
失敗時は読めたふりをせず、理由と次にできることを返す。

Ver2.8以降の表示例:

```text
Web Readerで読み取りました。

タイトル:
Example Domain

URL:
https://example.com

本文プレビュー:
Example Domain
This domain is for use in documentation examples without needing permission.
Avoid use in operations.
Learn more
```

自動チェックではfake fetcherを使い、実Webアクセスしない。
Reader結果のMemory保存はまだ行わない。
