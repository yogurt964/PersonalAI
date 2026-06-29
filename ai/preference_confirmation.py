import re

from ai.preference_memory import extract_preference_memories


def analyze_preference_confirmation(
    text,
    existing_memories=None,
    confirmation_frequency="normal",
):
    """Preferenceを保存する前に、確認質問が必要かを簡易判定します。"""
    if not text:
        return build_decision(
            False,
            "no_preference",
            "",
            "save_without_question",
        )

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
        return build_decision(
            False,
            "explicit_negative_preference",
            "",
            "save_without_question",
        )

    if preferences:
        return build_decision(
            False,
            "simple_addition",
            "",
            "save_without_question",
        )

    if confirmation_frequency == "high" and may_be_preference_update(normalized_text):
        return build_decision(
            True,
            "possible_preference_update",
            "この好みを新しい記憶として追加しますか？それとも既存の好みを更新しますか？",
            "ask_before_save",
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


def build_decision(should_ask, reason, question, default_action):
    return {
        "should_ask": should_ask,
        "reason": reason,
        "question": question,
        "default_action": default_action,
    }
