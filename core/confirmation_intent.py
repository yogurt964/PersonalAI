CONFIRMATION_INTENT_CONFIRMED = "confirmed"
CONFIRMATION_INTENT_REJECTED = "rejected"
CONFIRMATION_INTENT_UNCLEAR = "unclear"


WEB_READER_CONFIRMED_WORDS = [
    "はい",
    "うん",
    "いいよ",
    "いいです",
    "大丈夫",
    "ok",
    "okです",
    "お願いします",
    "お願い",
    "読んで",
    "読み取って",
    "実行して",
    "進めて",
    "許可",
    "許可します",
    "問題ない",
    "問題ありません",
    "yes",
]

WEB_READER_REJECTED_WORDS = [
    "いいえ",
    "だめ",
    "ダメ",
    "やめて",
    "やめる",
    "キャンセル",
    "今回はいい",
    "今はいい",
    "読まないで",
    "実行しないで",
    "拒否",
    "許可しない",
    "不要",
    "しないで",
    "no",
]


def resolve_confirmation_intent(user_input, context_type):
    """確認待ち状態の入力を、実行許可・拒否・不明に分類します。

    今はルールベースですが、将来LLM Intent Resolverに差し替えやすいように
    PersonalAI本体から分けています。
    """
    normalized_input = _normalize_confirmation_text(user_input)

    if context_type == "web_reader":
        return _resolve_web_reader_intent(normalized_input, context_type)

    return _build_intent_result(
        status=CONFIRMATION_INTENT_UNCLEAR,
        action="ask_clarification",
        context_type=context_type,
        confidence="low",
        message="確認応答として解釈できませんでした。",
    )


def _resolve_web_reader_intent(normalized_input, context_type):
    if _matches_any(normalized_input, WEB_READER_REJECTED_WORDS):
        return _build_intent_result(
            status=CONFIRMATION_INTENT_REJECTED,
            action="cancel_web_reader",
            context_type=context_type,
            confidence="high",
            message="Web Reader実行をキャンセルする意図として解釈しました。",
        )

    if _matches_any(normalized_input, WEB_READER_CONFIRMED_WORDS):
        return _build_intent_result(
            status=CONFIRMATION_INTENT_CONFIRMED,
            action="confirm_web_reader",
            context_type=context_type,
            confidence="high",
            message="Web Reader実行を許可する意図として解釈しました。",
        )

    return _build_intent_result(
        status=CONFIRMATION_INTENT_UNCLEAR,
        action="ask_web_reader_confirmation_again",
        context_type=context_type,
        confidence="low",
        message=(
            "Web Readerを実行するか確認中です。\n"
            "実行する場合は「はい」「いいよ」「お願いします」など、\n"
            "実行しない場合は「いいえ」「キャンセル」などで答えてください。"
        ),
    )


def _build_intent_result(status, action, context_type, confidence, message):
    return {
        "status": status,
        "action": action,
        "context_type": context_type,
        "confidence": confidence,
        "message": message,
    }


def _matches_any(normalized_input, words):
    if not normalized_input:
        return False

    normalized_words = [_normalize_confirmation_text(word) for word in words]

    return normalized_input in normalized_words


def _normalize_confirmation_text(value):
    """表記ゆれを小さくし、短い確認応答を比較しやすくします。"""
    text = " ".join(str(value or "").strip().lower().split())
    return text.strip("。．.、,！!？?　 ")
