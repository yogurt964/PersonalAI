import re

from ai.preference_memory import extract_preference_memories, build_memory_key
from database.memory_manager import save_memory


def analyze_preference_confirmation(
    text,
    existing_memories=None,
    confirmation_frequency="normal",
):
    """Preferenceを保存する前に、確認質問が必要かを簡易判定します。"""
    if not text:
        return build_decision(False, "no_preference", "", "save_without_question")

    normalized_text = str(text).strip()
    confirmation_frequency = normalize_confirmation_frequency(confirmation_frequency)

    change_decision = detect_change_request(normalized_text)

    if change_decision:
        return change_decision

    temporal_decision = detect_temporal_change(normalized_text)

    if temporal_decision:
        return temporal_decision

    primary_decision = detect_primary_preference(normalized_text)

    if primary_decision:
        return primary_decision

    preferences = extract_preference_memories(normalized_text)

    if has_explicit_negative_preference(preferences):
        preference = preferences[0]
        return build_decision(
            False,
            "explicit_negative_preference",
            "",
            "save_without_question",
            target=preference.get("target", ""),
            domain=preference.get("domain", "food"),
        )

    if preferences:
        preference = preferences[0]
        return build_decision(
            False,
            "simple_addition",
            "",
            "save_without_question",
            target=preference.get("target", ""),
            domain=preference.get("domain", "food"),
        )

    if confirmation_frequency == "high" and may_be_preference_update(normalized_text):
        return build_decision(
            True,
            "possible_preference_update",
            "この好みを新しい記憶として追加しますか？それとも既存の好みを更新しますか？",
            "ask_before_save",
            domain="food",
        )

    return build_decision(
        False,
        "no_preference",
        "",
        "save_without_question",
    )


def detect_change_request(text):
    if "好き" not in text:
        return None

    if "変更" not in text and "変えて" not in text and "変える" not in text:
        return None

    old_target, new_target = extract_from_to_targets(text)

    if old_target and new_target:
        question = (
            f"好きな食べ物を{old_target}から{new_target}に変更し、"
            f"{old_target}の好き記憶を使わないようにしますか？"
        )
    else:
        question = "好きな食べ物の記憶を変更しますか？それとも、好きなものの1つとして追加しますか？"

    return build_decision(
        True,
        "preference_change_request",
        question,
        "ask_before_save",
        old_target=old_target,
        new_target=new_target,
        domain="food",
    )


def detect_temporal_change(text):
    has_past = any(marker in text for marker in ("前は", "昔は", "以前は"))
    has_now = any(marker in text for marker in ("今は", "現在は"))

    if not has_past or not has_now or "好き" not in text:
        return None

    old_target, new_target = extract_temporal_targets(text)

    if old_target and new_target:
        question = f"{old_target}は古い好みとして扱い、今は{new_target}が好きとして更新しますか？"
    else:
        question = "過去の好みと現在の好みを分けて記憶しますか？"

    return build_decision(
        True,
        "temporal_preference_change",
        question,
        "ask_before_save",
        old_target=old_target,
        new_target=new_target,
        domain="food",
    )


def detect_primary_preference(text):
    if "一番" not in text or "好き" not in text:
        return None

    target = extract_primary_target(text)

    if target:
        question = (
            f"{target}を一番好きな食べ物として記憶しますか？"
            "それとも、好きな食べ物の1つとして追加しますか？"
        )
    else:
        question = "一番好きな食べ物として記憶しますか？それとも、好きな食べ物の1つとして追加しますか？"

    return build_decision(
        True,
        "primary_preference_update",
        question,
        "ask_before_save",
        target=target,
        domain="food",
    )


def has_explicit_negative_preference(preferences):
    return any(
        preference.get("polarity") in ("not_like", "dislike")
        for preference in preferences
    )


def may_be_preference_update(text):
    return "好き" in text and "覚えて" in text


def extract_from_to_targets(text):
    match = re.search(r"好きな食べ物を(?P<old>.+?)から(?P<new>.+?)(?:に|へ)?(?:変更|変えて|変える)", text)

    if not match:
        return "", ""

    return clean_target(match.group("old")), clean_target(match.group("new"))


def extract_temporal_targets(text):
    old_match = re.search(r"(?:前は|昔は|以前は)(?P<old>.+?)(?:が|は)好き", text)
    new_match = re.search(r"(?:今は|現在は)(?P<new>.+?)(?:が|は)好き", text)

    old_target = clean_target(old_match.group("old")) if old_match else ""
    new_target = clean_target(new_match.group("new")) if new_match else ""

    return old_target, new_target


def extract_primary_target(text):
    patterns = [
        r"一番好きな食べ物は(?P<target>.+?)(?:です|。|、|,|$)",
        r"(?P<target>.+?)(?:が|は)一番好き",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            return clean_target(match.group("target"))

    return ""


def clean_target(target):
    target = str(target).strip()
    target = re.sub(r"(です|だ|でした|だった|。|、|,|\.|！|!|？|\?)$", "", target)
    return target.strip()


def normalize_confirmation_frequency(value):
    if value in ("low", "normal", "high"):
        return value

    return "normal"


def resolve_preference_confirmation_answer(answer_text, pending):
    """保留中のPreference確認に対するユーザー回答を解釈します。"""
    answer_text = str(answer_text or "").strip()

    if is_cancel_answer(answer_text):
        return build_resolution(
            "cancel",
            "このPreference記憶は保存しませんでした。",
            True,
        )

    if is_ask_again_answer(answer_text):
        return build_resolution(
            "ask_again",
            build_ask_again_message(pending),
            False,
        )

    if is_primary_answer(answer_text):
        target = get_pending_target(pending)
        return build_resolution(
            "save_primary",
            f"{target}を一番好きな食べ物として記憶しました。",
            True,
        )

    if is_addition_answer(answer_text):
        target = get_pending_target(pending)
        return build_resolution(
            "save_addition",
            f"{target}を好きな食べ物の1つとして記憶しました。",
            True,
        )

    if is_change_answer(answer_text, pending):
        old_target = pending.get("old_target", "")
        new_target = get_pending_target(pending)

        if old_target:
            message = f"好きな食べ物を{old_target}から{new_target}に更新しました。"
        else:
            message = f"現在の好きな食べ物を{new_target}として記憶しました。"

        return build_resolution("save_change", message, True)

    return build_resolution(
        "ask_again",
        build_ask_again_message(pending),
        False,
    )


def save_resolved_preference_confirmation(
    pending,
    resolution,
    source="user",
    tags="preference",
):
    """確認回答の結果に応じてPreference記憶を保存します。"""
    action = resolution.get("action")

    if action in ("cancel", "ask_again"):
        return []

    if action == "save_primary":
        target = get_pending_target(pending)
        return [
            save_primary_preference(target, source, tags),
        ]

    if action == "save_addition":
        target = get_pending_target(pending)
        return [
            save_like_preference(target, source, tags),
        ]

    if action == "save_change":
        old_target = pending.get("old_target", "")
        new_target = get_pending_target(pending)
        results = [
            save_current_like_preference(new_target, source, tags),
        ]

        if old_target:
            results.append(save_past_like_preference(old_target, new_target, source, tags))

        return results

    return []


def save_primary_preference(target, source, tags):
    return save_memory(
        content=f"ユーザーは{target}が一番好きな食べ物です。",
        memory_type="user_profile",
        category="preference",
        importance=10,
        source=source,
        tags=tags,
        memory_key="preference:food:primary",
        subcategory="food_primary_like",
        scope="user",
        confidence=90,
    )


def save_like_preference(target, source, tags):
    return save_memory(
        content=f"ユーザーは{target}が好きです。",
        memory_type="user_profile",
        category="preference",
        importance=9,
        source=source,
        tags=tags,
        memory_key=build_memory_key(target),
        subcategory="food_like",
        scope="user",
        confidence=90,
    )


def save_current_like_preference(target, source, tags):
    return save_memory(
        content=f"ユーザーは現在、{target}が好きです。",
        memory_type="user_profile",
        category="preference",
        importance=9,
        source=source,
        tags=tags,
        memory_key=build_memory_key(target),
        subcategory="food_like",
        scope="user",
        confidence=90,
    )


def save_past_like_preference(old_target, new_target, source, tags):
    return save_memory(
        content=f"ユーザーは以前{old_target}が好きでしたが、現在の好みとしては優先しません。",
        memory_type="user_profile",
        category="preference",
        importance=8,
        source=source,
        tags=tags,
        memory_key=build_memory_key(old_target),
        subcategory="food_past_like",
        scope="user",
        confidence=85,
    )


def is_primary_answer(answer_text):
    return any(
        pattern in answer_text
        for pattern in ("一番好きとして", "一番でいい", "一番好き", "最優先で記憶")
    )


def is_addition_answer(answer_text):
    return any(
        pattern in answer_text
        for pattern in ("好きなものの1つとして", "好きなものの一つとして", "追加で", "追加して", "両方好き", "それも好き")
    )


def is_change_answer(answer_text, pending):
    if any(pattern in answer_text for pattern in ("変更して", "更新して", "今はそれで")):
        return True

    new_target = pending.get("new_target", "")
    old_target = pending.get("old_target", "")

    if new_target and f"今は{new_target}" in answer_text:
        return True

    if old_target and new_target and f"{old_target}から{new_target}" in answer_text:
        return True

    return False


def is_cancel_answer(answer_text):
    return any(
        pattern in answer_text
        for pattern in ("記憶しないで", "キャンセル", "やっぱりいい", "保存しないで", "取り消して")
    )


def is_ask_again_answer(answer_text):
    return any(
        pattern in answer_text
        for pattern in ("わからない", "分からない", "どっちでも", "任せる")
    )


def get_pending_target(pending):
    return pending.get("target") or pending.get("new_target") or ""


def build_ask_again_message(pending):
    reason = pending.get("reason")

    if reason == "primary_preference_update":
        return "一番好きとして記憶するか、好きなものの1つとして追加するか教えてください。"

    if reason in ("temporal_preference_change", "preference_change_request"):
        return "好みを変更として保存するか、好きなものの1つとして追加するか教えてください。"

    return "どのようにPreference記憶として保存するか、もう少し具体的に教えてください。"


def build_resolution(action, message, should_clear_pending):
    return {
        "action": action,
        "message": message,
        "should_clear_pending": should_clear_pending,
    }


def build_decision(should_ask, reason, question, default_action, **extra):
    decision = {
        "should_ask": should_ask,
        "reason": reason,
        "question": question,
        "default_action": default_action,
    }
    decision.update(extra)
    return decision
