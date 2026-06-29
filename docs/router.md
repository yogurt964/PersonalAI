# Router

## 役割

RouterはPersonalAIの道具選択を担当する。

Plannerが作ったplanを受け取り、そのplanをどのモデル、API、ツール、処理系に渡すべきかを判断する。

## Routerが扱う情報

Routerは主に以下の情報を使う。

- Plannerが返した `Plan`
- planに含まれるaction
- planに含まれるrisk
- 必要なモデルやツールの候補
- 許可が必要かどうか

## ModelRouterではなくRouterにした理由

以前はModelRouterという名前を想定していた。

しかし、今後はモデル選択だけでなく、PDF Reader、Vision、Web、YouTube Reader、Executorなど、さまざまな道具や処理系を選ぶ可能性がある。

そのため、モデルだけに限定しない広い名前としてRouterを採用する。

## 現在の実装

現時点では、Qwen中心の簡易Routerとして実装する。

基本的には以下のようにrouteを作る。

- `chat`: `qwen`
- `memory_read`: `qwen`
- `memory_write`: `qwen`
- `summarize_youtube`: `qwen`
- `summarize_url`: `qwen`
- `create_document`: `qwen`
- `recommend`: `qwen`
- `answer_question`: `qwen`
- `unsupported_external_reading`: `qwen`
- `unsupported_file_creation`: `qwen`
- `ask_clarification`: `qwen`
- 未定義のaction: `qwen`
- `risk` が `high`: `openai_candidate`

`openai_candidate` は、まだOpenAIを実行するという意味ではない。
高リスクな処理では、将来的にOpenAIを候補にできるようにするための目印である。
現時点ではOpenAI接続は未実装であり、Routerは候補を返すだけで実行しない。

Version 0.10では、外部読み取りや実ファイル作成が必要なactionも、現時点ではQwenにルーティングする。
ただし、実行時にはExecutorが未実装であることを説明し、読んだふり・作ったふりを避ける。

Version 0.11では、情報不足を表す `ask_clarification` もQwenにルーティングする。
Executor側で固定質問文を返すため、Qwenに自由生成させすぎない。

## Routerが返すroute

Version 0.6以降、Routerはdictではなく `Route` クラスのインスタンスを返す。

routeの例:

```python
Route(
    target="qwen",
    reason="通常の会話はQwenで対応できるため",
    model="qwen3:8b",
    tool=None,
    requires_permission=False,
    risk="low",
)
```

従来のdict形式が必要な場合は、`route.to_dict()` で変換できる。

## 今後の予定

将来的には、以下のような選択をできるようにする。

- OpenAI
- Vision
- PDF Reader
- Web
- YouTube Reader
- Executor

ユーザーの優先順位は「精度 → 安全性 → コスト → 速度」であり、Routerもこの方針に従う。

速さだけで選ぶのではなく、正確性、安全性、コスト、処理内容に合った道具を選ぶことを目指す。
