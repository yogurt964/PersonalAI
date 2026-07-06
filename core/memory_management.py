from core.confirmation_intent import resolve_confirmation_intent


MEMORY_LIST_PREVIEW_MAX_CHARS = 120
MEMORY_LIST_LIMIT = 20


def build_memory_list_response(memories):
    """保存されているMemoryの一覧を、IDつきで見やすく表示します。

    削除操作はここで得たIDを使って指定します（物理削除ではなく無効化です）。
    """
    memories = list(memories or [])[:MEMORY_LIST_LIMIT]

    if not memories:
        return "保存されている記憶はまだありません。"

    lines = ["保存されている記憶（新しい順、上限20件）:", ""]

    for memory in memories:
        memory_id = _get_value(memory, "id")
        content_preview = _shorten_text(_get_value(memory, "content"))
        category = _get_value(memory, "category") or "未分類"
        importance = _get_value(memory, "importance")
        lines.append(f"[{memory_id}] {content_preview}（カテゴリ: {category}, 重要度: {importance}）")

    lines.append("")
    lines.append("削除する場合は「(番号)の記憶を削除して」のように送ってください。")

    return "\n".join(lines)


def build_memory_delete_confirmation(memory_id, memory):
    """指定されたIDのMemoryを削除（無効化）してよいか確認するメッセージを作ります。

    この関数はDBへ一切アクセスせず、メッセージだけを作ります。
    「削除」は物理削除ではなく、is_active=Falseへの無効化です（元に戻せます）。
    """
    if memory_id is None:
        return {
            "needs_confirmation": False,
            "memory_id": None,
            "message": (
                "どの記憶を削除するか、番号が分かりませんでした。\n"
                "「覚えていることを見せて」で一覧を確認し、"
                "「(番号)の記憶を削除して」のように送ってください。"
            ),
        }

    if memory is None:
        return {
            "needs_confirmation": False,
            "memory_id": memory_id,
            "message": f"ID {memory_id} の記憶が見つかりませんでした。すでに削除されている可能性があります。",
        }

    content_preview = _shorten_text(_get_value(memory, "content"))

    return {
        "needs_confirmation": True,
        "memory_id": memory_id,
        "message": (
            f"この記憶を削除してもよいですか？\n"
            f"[{memory_id}] {content_preview}\n\n"
            "削除は無効化として扱い、物理的な削除は行いません（必要なら復元できます）。"
            "実行前に確認が必要です。"
        ),
    }


def resolve_memory_delete_confirmation_response(user_input, pending_confirmation, ask_llm_func=None):
    """Memory削除確認への返答を分類します。

    確認判定は、他のReader確認と同じハイブリッド方式（固定語彙優先＋不明時のみLLM）を再利用します。
    """
    if not pending_confirmation:
        return {"status": "no_pending", "memory_id": None, "message": ""}

    intent = resolve_confirmation_intent(user_input, context_type="memory_delete", ask_llm_func=ask_llm_func)
    memory_id = pending_confirmation.get("memory_id")

    if intent.get("status") == "confirmed":
        return {
            "status": "confirmed",
            "memory_id": memory_id,
            "message": "記憶の削除（無効化）を実行します。",
        }

    if intent.get("status") == "rejected":
        return {
            "status": "cancelled",
            "memory_id": memory_id,
            "message": "記憶は削除しませんでした。",
        }

    return {
        "status": "unclear",
        "memory_id": memory_id,
        "message": intent.get("message", ""),
    }


def build_memory_delete_result_response(deactivated_memory, memory_id):
    """削除（無効化）実行結果を、会話で分かりやすい返答にします。"""
    if deactivated_memory is None:
        return f"ID {memory_id} の記憶を削除できませんでした。すでに削除されている可能性があります。"

    content_preview = _shorten_text(_get_value(deactivated_memory, "content"))

    return f"記憶を削除しました（無効化）。\n[{memory_id}] {content_preview}"


def _get_value(obj, key, default=""):
    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(key, default)

    return getattr(obj, key, default)


def _shorten_text(value, max_chars=MEMORY_LIST_PREVIEW_MAX_CHARS):
    text = " ".join(str(value or "").split())

    if len(text) <= max_chars:
        return text

    return f"{text[:max_chars].rstrip()}..."
