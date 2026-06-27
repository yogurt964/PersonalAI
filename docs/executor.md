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

まだPersonalAI本体には統合しない。
そのため、既存の会話処理や記憶処理は変更されない。

## 将来追加予定

将来的には、以下のような実行処理を追加する予定である。

- `_execute_openai()`
- `_execute_browser()`
- `_execute_pdf()`
- `_execute_vision()`
- `_execute_tool()`

OpenAI、Browser、Vision、PDF Readerなどを追加するときも、Executorに実行処理を集めることで、PersonalAI本体を複雑にしすぎない構造を目指す。
