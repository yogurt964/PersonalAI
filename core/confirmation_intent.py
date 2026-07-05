CONFIRMATION_INTENT_CONFIRMED = "confirmed"
CONFIRMATION_INTENT_REJECTED = "rejected"
CONFIRMATION_INTENT_UNCLEAR = "unclear"


WEB_READER_CONFIRMED_WORDS = [
    "はい",
    "うん",
    "イエス",
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


GENERIC_CONFIRMATION_CONTEXTS = {
    "web_reader": {
        "confirm_action": "confirm_web_reader",
        "cancel_action": "cancel_web_reader",
        "unclear_action": "ask_web_reader_confirmation_again",
        "confirm_message": "Web Reader実行を許可する意図として解釈しました。",
        "cancel_message": "Web Reader実行をキャンセルする意図として解釈しました。",
        "unclear_message": (
            "Web Readerを実行するか確認中です。\n"
            "実行する場合は「はい」「いいよ」「お願いします」など、\n"
            "実行しない場合は「いいえ」「キャンセル」などで答えてください。"
        ),
    },
    "file_reader": {
        "confirm_action": "confirm_file_reader",
        "cancel_action": "cancel_file_reader",
        "unclear_action": "ask_file_reader_confirmation_again",
        "confirm_message": "File Reader実行を許可する意図として解釈しました。",
        "cancel_message": "File Reader実行をキャンセルする意図として解釈しました。",
        "unclear_message": (
            "ファイルを読み取るか確認中です。\n"
            "実行する場合は「はい」「いいよ」「お願いします」など、\n"
            "実行しない場合は「いいえ」「キャンセル」などで答えてください。"
        ),
    },
    "pdf_reader": {
        "confirm_action": "confirm_pdf_reader",
        "cancel_action": "cancel_pdf_reader",
        "unclear_action": "ask_pdf_reader_confirmation_again",
        "confirm_message": "PDF Reader実行を許可する意図として解釈しました。",
        "cancel_message": "PDF Reader実行をキャンセルする意図として解釈しました。",
        "unclear_message": (
            "PDFを読み取るか確認中です。\n"
            "実行する場合は「はい」「いいよ」「お願いします」など、\n"
            "実行しない場合は「いいえ」「キャンセル」などで答えてください。"
        ),
    },
    "word_reader": {
        "confirm_action": "confirm_word_reader",
        "cancel_action": "cancel_word_reader",
        "unclear_action": "ask_word_reader_confirmation_again",
        "confirm_message": "Word Reader実行を許可する意図として解釈しました。",
        "cancel_message": "Word Reader実行をキャンセルする意図として解釈しました。",
        "unclear_message": (
            "Wordファイルを読み取るか確認中です。\n"
            "実行する場合は「はい」「いいよ」「お願いします」など、\n"
            "実行しない場合は「いいえ」「キャンセル」などで答えてください。"
        ),
    },
    "excel_reader": {
        "confirm_action": "confirm_excel_reader",
        "cancel_action": "cancel_excel_reader",
        "unclear_action": "ask_excel_reader_confirmation_again",
        "confirm_message": "Excel Reader実行を許可する意図として解釈しました。",
        "cancel_message": "Excel Reader実行をキャンセルする意図として解釈しました。",
        "unclear_message": (
            "Excelファイルを読み取るか確認中です。\n"
            "実行する場合は「はい」「いいよ」「お願いします」など、\n"
            "実行しない場合は「いいえ」「キャンセル」などで答えてください。"
        ),
    },
}


def resolve_confirmation_intent(user_input, context_type):
    """確認待ち状態の入力を、実行許可・拒否・不明に分類します。

    今はルールベースですが、将来LLM Intent Resolverに差し替えやすいように
    PersonalAI本体から分けています。
    """
    normalized_input = _normalize_confirmation_text(user_input)
    context_config = GENERIC_CONFIRMATION_CONTEXTS.get(context_type)

    if context_config is not None:
        return _resolve_generic_confirmation_intent(
            normalized_input,
            context_type,
            context_config,
        )

    return _build_intent_result(
        status=CONFIRMATION_INTENT_UNCLEAR,
        action="ask_clarification",
        context_type=context_type,
        confidence="low",
        message="確認応答として解釈できませんでした。",
    )


def _resolve_generic_confirmation_intent(normalized_input, context_type, context_config):
    """はい/いいえ系の一般的な確認応答を、共通の語彙リストで判定します。

    Web ReaderとFile Readerは、どちらも「実行してよいか」を問う確認であり、
    使われる言い回し自体は共通です。文言だけをcontext_configで切り替えます。
    """
    if _matches_any(normalized_input, WEB_READER_REJECTED_WORDS):
        return _build_intent_result(
            status=CONFIRMATION_INTENT_REJECTED,
            action=context_config["cancel_action"],
            context_type=context_type,
            confidence="high",
            message=context_config["cancel_message"],
        )

    if _matches_any(normalized_input, WEB_READER_CONFIRMED_WORDS):
        return _build_intent_result(
            status=CONFIRMATION_INTENT_CONFIRMED,
            action=context_config["confirm_action"],
            context_type=context_type,
            confidence="high",
            message=context_config["confirm_message"],
        )

    return _build_intent_result(
        status=CONFIRMATION_INTENT_UNCLEAR,
        action=context_config["unclear_action"],
        context_type=context_type,
        confidence="low",
        message=context_config["unclear_message"],
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
