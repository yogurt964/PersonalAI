from core.confirmation_intent import resolve_confirmation_intent


MEMORY_LIST_PREVIEW_MAX_CHARS = 120
MEMORY_LIST_LIMIT = 20

MEMORY_EDIT_CANCEL_WORDS = ["キャンセル", "やめる", "やめて", "編集しない"]


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
    lines.append("編集する場合は「(番号)の記憶を編集して」のように送ってください。")

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


def build_memory_edit_prompt(memory_id, memory):
    """指定されたIDのMemoryについて、新しい内容の入力を促すメッセージを作ります（Ver2.61）。

    この関数はDBへ一切アクセスせず、メッセージだけを作ります。
    """
    if memory_id is None:
        return {
            "needs_new_content": False,
            "memory_id": None,
            "message": (
                "どの記憶を編集するか、番号が分かりませんでした。\n"
                "「覚えていることを見せて」で一覧を確認し、"
                "「(番号)の記憶を編集して」のように送ってください。"
            ),
        }

    if memory is None:
        return {
            "needs_new_content": False,
            "memory_id": memory_id,
            "message": f"ID {memory_id} の記憶が見つかりませんでした。すでに削除されている可能性があります。",
        }

    content_preview = _shorten_text(_get_value(memory, "content"))

    return {
        "needs_new_content": True,
        "memory_id": memory_id,
        "original_content": _get_value(memory, "content"),
        "message": (
            f"この記憶を編集します。\n"
            f"[{memory_id}] {content_preview}\n\n"
            "新しい内容を送ってください（キャンセルする場合は「キャンセル」と送ってください）。"
        ),
    }


def build_memory_edit_confirmation(memory_id, original_content, new_content):
    """受け取った新しい内容で書き換えてよいか確認するメッセージを作ります（Ver2.61）。

    この関数はDBへ一切アクセスせず、メッセージだけを作ります。
    書き換えは元の内容に自動で戻せない（履歴を残さない）ため、実行前に確認が必要です。
    """
    normalized_new_content = str(new_content or "").strip()

    if not normalized_new_content:
        return {
            "needs_confirmation": False,
            "memory_id": memory_id,
            "message": "新しい内容が空でした。記憶に反映したい内容をもう一度送ってください。",
        }

    if _matches_any(normalized_new_content, MEMORY_EDIT_CANCEL_WORDS):
        return {
            "needs_confirmation": False,
            "memory_id": memory_id,
            "message": "記憶の編集をキャンセルしました。内容は変更していません。",
        }

    return {
        "needs_confirmation": True,
        "memory_id": memory_id,
        "new_content": normalized_new_content,
        "original_content": original_content,
        "message": (
            "この記憶をこの内容に書き換えてもよいですか？\n\n"
            f"変更前: {_shorten_text(original_content)}\n"
            f"変更後: {_shorten_text(normalized_new_content)}\n\n"
            "書き換えると元の内容には自動で戻せません。実行前に確認が必要です。"
        ),
    }


def resolve_memory_edit_confirmation_response(user_input, pending_confirmation, ask_llm_func=None):
    """Memory編集確認への返答を分類します。

    確認判定は、他のReader確認・Memory削除確認と同じハイブリッド方式
    （固定語彙優先＋不明時のみLLM）を再利用します。
    """
    if not pending_confirmation:
        return {"status": "no_pending", "memory_id": None, "message": ""}

    intent = resolve_confirmation_intent(user_input, context_type="memory_edit", ask_llm_func=ask_llm_func)
    memory_id = pending_confirmation.get("memory_id")

    if intent.get("status") == "confirmed":
        return {
            "status": "confirmed",
            "memory_id": memory_id,
            "message": "記憶の編集（内容の書き換え）を実行します。",
        }

    if intent.get("status") == "rejected":
        return {
            "status": "cancelled",
            "memory_id": memory_id,
            "message": "記憶の編集をキャンセルしました。内容は変更していません。",
        }

    return {
        "status": "unclear",
        "memory_id": memory_id,
        "message": intent.get("message", ""),
    }


def build_memory_edit_result_response(updated_memory, memory_id, original_content):
    """編集（内容書き換え）実行結果を、会話で分かりやすい返答にします。"""
    if updated_memory is None:
        return f"ID {memory_id} の記憶を編集できませんでした。すでに削除されている可能性があります。"

    content_preview = _shorten_text(_get_value(updated_memory, "content"))

    return f"記憶を編集しました。\n[{memory_id}] {content_preview}"


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


def _matches_any(normalized_text, words):
    return any(word in normalized_text for word in words)
