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
    "pptx_reader": {
        "confirm_action": "confirm_pptx_reader",
        "cancel_action": "cancel_pptx_reader",
        "unclear_action": "ask_pptx_reader_confirmation_again",
        "confirm_message": "PowerPoint Reader実行を許可する意図として解釈しました。",
        "cancel_message": "PowerPoint Reader実行をキャンセルする意図として解釈しました。",
        "unclear_message": (
            "PowerPointファイルを読み取るか確認中です。\n"
            "実行する場合は「はい」「いいよ」「お願いします」など、\n"
            "実行しない場合は「いいえ」「キャンセル」などで答えてください。"
        ),
    },
    "youtube_reader": {
        "confirm_action": "confirm_youtube_reader",
        "cancel_action": "cancel_youtube_reader",
        "unclear_action": "ask_youtube_reader_confirmation_again",
        "confirm_message": "YouTube Reader実行を許可する意図として解釈しました。",
        "cancel_message": "YouTube Reader実行をキャンセルする意図として解釈しました。",
        "unclear_message": (
            "YouTube動画の字幕を取得するか確認中です。\n"
            "実行する場合は「はい」「いいよ」「お願いします」など、\n"
            "実行しない場合は「いいえ」「キャンセル」などで答えてください。"
        ),
    },
}


def resolve_confirmation_intent(user_input, context_type, ask_llm_func=None):
    """確認待ち状態の入力を、実行許可・拒否・不明に分類します。

    まず固定語彙リストで判定し、一致しない場合だけLLMに解釈させるハイブリッド方式です。
    固定語彙で判定できる範囲は今まで通り決定的に動作するため、既存の挙動は変わりません。
    """
    normalized_input = _normalize_confirmation_text(user_input)
    context_config = GENERIC_CONFIRMATION_CONTEXTS.get(context_type)

    if context_config is not None:
        return _resolve_generic_confirmation_intent(
            normalized_input,
            context_type,
            context_config,
            ask_llm_func=ask_llm_func,
        )

    return _build_intent_result(
        status=CONFIRMATION_INTENT_UNCLEAR,
        action="ask_clarification",
        context_type=context_type,
        confidence="low",
        message="確認応答として解釈できませんでした。",
    )


def _resolve_generic_confirmation_intent(normalized_input, context_type, context_config, ask_llm_func=None):
    """はい/いいえ系の一般的な確認応答を、共通の語彙リストで判定します。

    Web ReaderとFile Readerは、どちらも「実行してよいか」を問う確認であり、
    使われる言い回し自体は共通です。文言だけをcontext_configで切り替えます。

    固定語彙に一致しない場合のみ、LLMに解釈させます（Ver2.44）。
    LLMには正規化済みのユーザー返信テキストだけを渡し、Readerが読み込んだ外部本文は
    一切含めません。これはWeb/PDF/YouTubeなどの外部contentに紛れた指示文で
    実行許可を誤認識させる（prompt injection）リスクを避けるためです。
    LLMの応答が3つの単語のどれにも一致しない場合や、呼び出しに失敗した場合は、
    安全側に倒してunclear（不明）として扱います。
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

    llm_status = _resolve_confirmation_intent_via_llm(normalized_input, ask_llm_func)

    if llm_status == CONFIRMATION_INTENT_CONFIRMED:
        return _build_intent_result(
            status=CONFIRMATION_INTENT_CONFIRMED,
            action=context_config["confirm_action"],
            context_type=context_type,
            confidence="medium",
            message=context_config["confirm_message"],
        )

    if llm_status == CONFIRMATION_INTENT_REJECTED:
        return _build_intent_result(
            status=CONFIRMATION_INTENT_REJECTED,
            action=context_config["cancel_action"],
            context_type=context_type,
            confidence="medium",
            message=context_config["cancel_message"],
        )

    return _build_intent_result(
        status=CONFIRMATION_INTENT_UNCLEAR,
        action=context_config["unclear_action"],
        context_type=context_type,
        confidence="low",
        message=context_config["unclear_message"],
    )


def _resolve_confirmation_intent_via_llm(normalized_input, ask_llm_func):
    """固定語彙で判定できない返信だけを、LLMにconfirmed/rejected/unclearの1語で答えさせます。

    渡すのはユーザー自身の返信テキストのみです。判断できない・失敗した場合は
    必ずunclearを返し、silent確認（黙って実行許可扱いにすること）は絶対にしません。
    """
    if not normalized_input:
        return CONFIRMATION_INTENT_UNCLEAR

    # ask_llm_funcを渡さない呼び出し元（LLMフォールバックを意図していない場合）では、
    # 暗黙にQwenを呼び出さずunclearのままにします。実行時のPersonalAIは
    # __init__でself.ask_llm_funcを設定しているため、実際の会話では通常どおりLLMが使われます。
    if ask_llm_func is None:
        return CONFIRMATION_INTENT_UNCLEAR

    llm_func = ask_llm_func

    prompt = (
        "次のテキストは、ツール実行の確認（はい/いいえ）に対するユーザーの返信です。\n"
        "実行してよいという意味なら confirmed、実行しないでほしいという意味なら rejected、\n"
        "どちらとも判断できない場合は unclear と、必ずこの3つの単語のうち1つだけで答えてください。\n"
        "説明や他の文章、記号は付けないでください。\n\n"
        f"返信テキスト: {normalized_input}"
    )

    try:
        response = llm_func([{"role": "user", "content": prompt}])
    except Exception:
        return CONFIRMATION_INTENT_UNCLEAR

    normalized_response = str(response or "").strip().lower()
    has_confirmed = "confirmed" in normalized_response
    has_rejected = "rejected" in normalized_response
    has_unclear = "unclear" in normalized_response

    if has_confirmed and not has_rejected and not has_unclear:
        return CONFIRMATION_INTENT_CONFIRMED

    if has_rejected and not has_confirmed and not has_unclear:
        return CONFIRMATION_INTENT_REJECTED

    return CONFIRMATION_INTENT_UNCLEAR


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
