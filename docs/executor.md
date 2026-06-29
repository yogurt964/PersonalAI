# Executor

## 役割

Executorは、Routerが選択したRouteを実際に実行する担当である。

Plannerは「何をするか」を決め、Routerは「どの処理系に渡すか」を決める。
Executorは、その結果を受け取って実際の処理を呼び出す。

## 現在の実装

現時点では、Qwenだけを実行対象とする。

`execute(plan, route, messages)` は、`route.target` を見て以下のように処理を分ける。

- `qwen`: `_execute_qwen(messages)` を呼び、`ask_llm(messages)` で回答を生成する
- `openai_candidate`: `_execute_openai_candidate()` を呼び、未実装メッセージを返す
- その他: 未対応の実行先であることを返す

Version 0.8で、ExecutorはPersonalAI本体に接続された。
PersonalAIは直接 `ask_llm(messages)` を呼ばず、`executor.execute(plan, route, messages)` に実行を任せる。

現時点では通常のrouteは `qwen` なので、既存の会話処理や記憶処理は維持される。
OpenAI、Browser、Vision、PDF Reader、YouTube Readerはまだ接続されていない。

Version 0.10では、以下のactionに対して固定メッセージを返し、読んだふり・作ったふりを避ける。

- `summarize_youtube`: YouTube動画の直接読み取りは未実装であることを返す
- `summarize_url`: Webページの直接読み取りは未実装であることを返す
- `create_document`: Word / PDFなどの実ファイル作成は未実装であることを返す
- `unsupported_external_reading`: 外部情報読み取りは未実装であることを返す
- `unsupported_file_creation`: 実ファイル作成は未実装であることを返す

通常会話、記憶読み取り、記憶書き込み、おすすめ依頼、質問は従来通りQwenに渡す。

Version 0.11では、`ask_clarification` に対して必要最小限の質問文を返す。

例:

- YouTube / 動画URL不足: 動画URLを求める
- Web / URL不足: 対象ページのURLを求める
- PDF / 画像 / 資料不足: 対象ファイルまたはURLを求める

現時点では、複数ターンのClarification状態管理やClarificationManagerの本格分離は行わない。

## 将来追加予定

将来的には、以下のような実行処理を追加する予定である。

- `_execute_openai()`
- `_execute_browser()`
- `_execute_pdf()`
- `_execute_vision()`
- `_execute_tool()`

OpenAI、Browser、Vision、PDF Readerなどを追加するときも、Executorに実行処理を集めることで、PersonalAI本体を複雑にしすぎない構造を目指す。
