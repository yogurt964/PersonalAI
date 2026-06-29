# PermissionManager

## 役割

PermissionManagerは、PlanやRouteを見て、ユーザー許可が必要かどうかを判断するための基礎モジュールである。

PersonalAIは将来的に、Web読み取り、ファイル操作、PC操作、Git操作、文書作成、外部API利用などを扱う予定である。
これらを安全に扱うため、早い段階で「どの操作が危険か」「どの操作に許可が必要か」を判断する土台を用意する。

## 返すdict

PermissionManagerは、以下のようなdictを返す。

```python
{
    "requires_permission": True,
    "risk": "high",
    "reason": "git_push は高リスク操作のため、ユーザー許可が必要です",
    "blocked": True,
}
```

各フィールドの意味:

- `requires_permission`: ユーザー許可が必要か
- `risk`: `low` / `medium` / `high`
- `reason`: 判断理由
- `blocked`: 現時点で実行を止めるべきか

現時点では、許可が必要な操作は基本的に `blocked=True` にする。
まだ、許可後に処理を再開する仕組みがないためである。

## リスク分類

### 低リスク

現在実装済み、または未実装メッセージだけを返すactionは低リスクとして扱う。

- `chat`
- `answer_question`
- `recommend`
- `memory_read`
- `memory_write`
- `ask_clarification`
- `summarize_youtube`
- `summarize_url`
- `create_document`
- `unsupported_external_reading`
- `unsupported_file_creation`

これらは現時点では `blocked=False` とする。

### 中リスク

将来、ファイル読み取り、ファイル作成、Web読み取り、テスト実行などは中リスクとして扱う。

例:

- `read_file`
- `create_file`
- `edit_file`
- `read_web`
- `read_pdf`
- `read_image`
- `create_pdf`
- `run_test`

これらは現時点では `requires_permission=True`、`risk="medium"`、`blocked=True` とする。

### 高リスク

削除、上書き、外部送信、Git push、コマンド実行、PC操作、個人情報処理、課金などは高リスクとして扱う。

例:

- `delete_file`
- `overwrite_file`
- `send_external`
- `git_push`
- `run_command`
- `pc_control`
- `handle_personal_info`
- `payment_or_billing`

これらは現時点では `requires_permission=True`、`risk="high"`、`blocked=True` とする。

### 未知のaction

未分類のactionは安全側に倒す。

現時点では `requires_permission=True`、`risk="medium"`、`blocked=True` とする。

## PersonalAIとの接続

Version 0.12で、PermissionManagerはPersonalAI本体に接続された。

現在の流れ:

```text
InputAnalyzer
→ Memory抽出
→ CapabilityManager
→ Planner
→ Router
→ PermissionManager
→ Executor
```

`blocked=True` の場合、PersonalAIはExecutorへ進まず、安全確認が必要であることを固定メッセージで返す。

実際の許可取得、許可待ち状態の管理、許可後の再実行はまだ未実装である。
