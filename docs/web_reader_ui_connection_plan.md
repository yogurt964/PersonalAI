# Web Reader UI Connection Plan

## 目的

Ver2.1では、Web Readerを会話UIへ接続する前の方針を整理する。

現時点では、会話UIから自動Webアクセスしない。
URLを検出しただけで勝手にアクセスしない。
今回の作業は実装ではなく方針整理に留める。
手動テストの代表URLは `https://example.com` とし、会話UIからはまだ自動実行しない。

Ver2.2では、URL入力検出から確認メッセージ生成までのdry-runを追加する。
この段階ではWebアクセスはまだしない。
会話UIへの実接続はまだしない。
`user_confirmed=True` による実行接続は今後扱う。
URLを見つけただけで勝手にアクセスしない。
Ver2.2 checkは実Webアクセスしない。

Ver2.3では、URL確認メッセージを会話返答として表示するdry-run接続を追加する。
この段階でもWebアクセスはまだしない。
ToolRunnerはまだ会話UIから呼ばない。
`user_confirmed=True` 後の実行接続は今後扱う。
URLを見つけただけで勝手にWebアクセスしない。
Ver2.3 checkは実Webアクセスしない。

## 将来の接続案

将来の接続案:

1. `InputAnalyzer` がURL入力を検出する
2. URL確認メッセージ生成dry-runで「Webを読み取ってよいか」を作る
3. `PersonalAI` が確認メッセージを会話UIに表示する
4. ユーザー確認応答を受け取る前段設計を追加する
5. ユーザーが明示許可した場合のみ `user_confirmed=True` にする
6. `ToolRunner` 経由で `WebReaderAdapter` を実行する
7. 結果を会話文脈に渡す
8. `ToolExecutionLog` に実行結果を残す

この流れができるまでは、会話UIからWeb Readerを自動実行しない。

## 安全方針

- URL検出だけでは自動Webアクセスしない
- `user_confirmed=False` ではWebアクセスしない
- `user_confirmed=True` はユーザーの明示許可がある場合だけ使う
- 未許可なら `executed=False`
- 自動チェックでは実Webアクセスしない
- DBに書き込まない
- `data/personal_ai.db` を変更しない

## success と executed

`success` と `executed` は混同しない。

- Webアクセスを試み、取得や解析に成功した場合: `success=True` / `executed=True`
- Webアクセスを試みたが失敗した場合: `success=False` / `executed=True`
- 未許可、URLなし、未実行の場合: `success=False` / `executed=False`

失敗時は、正直に失敗理由を返す。
読めなかったページを読めたふりしない。

## Memoryとの関係

取得内容をMemoryに保存するかどうかは別機能として後回しにする。

Web Readerの会話UI接続では、まず読み取り、確認、実行ログまでを安全に扱う。
Reader結果のMemory保存方針は、Ver2.xの別作業として整理する。

## 未実装の範囲

以下はまだ実装しない。

- Web Readerの会話UI自動実行
- `user_confirmed=True` 後の実行接続
- PDF Reader
- Image Reader
- YouTube Reader
- File Reader
- PC操作
- Word / Excel / PDF作成
