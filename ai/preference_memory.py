import re

from database.memory_manager import save_memory


TARGET_PATTERN = r"(?P<target>[一-龥ぁ-んァ-ンーA-Za-z0-9・]+)"

PREFERENCE_PATTERNS = [
    (
        "not_like",
        re.compile(
            rf"{TARGET_PATTERN}(?:は|が)(?:あまり)?好き(?:じゃない|ではない|じゃありません|ではありません|じゃないです|ではないです)"
        ),
    ),
    (
        "dislike",
        re.compile(rf"{TARGET_PATTERN}(?:は|が)(?:とても|すごく|かなり)?嫌い"),
    ),
    (
        "like",
        re.compile(
            rf"{TARGET_PATTERN}(?:は|が)(?:とても|すごく|かなり)?好き(?!じゃない|ではない|じゃありません|ではありません|じゃないです|ではないです)"
        ),
    ),
]

POLARITY_SUBCATEGORY = {
    "like": "food_like",
    "not_like": "food_not_like",
    "dislike": "food_dislike",
}


def extract_preference_memories(text):
    """明確な好き嫌い表現から、Preference記憶候補を抽出します。"""
    if not text:
        return []

    preferences = []
    matched_keys = set()

    for polarity, pattern in PREFERENCE_PATTERNS:
        for match in pattern.finditer(text):
            target = normalize_target(match.group("target"))

            if not target:
                continue

            memory_key = build_memory_key(target)

            # 同じ入力内で同じ対象が複数回取れた場合は、最初の明確な判定を優先します。
            if memory_key in matched_keys:
                continue

            matched_keys.add(memory_key)
            preferences.append(build_preference_memory(target, polarity))

    return preferences


def save_preference_memories(text, source="user", tags="preference"):
    """抽出したPreference記憶を、既存のsave_memoryで保存します。"""
    preferences = extract_preference_memories(text)
    results = []

    for preference in preferences:
        saved = save_memory(
            content=preference["content"],
            memory_type="user_profile",
            category=preference["category"],
            importance=preference["importance"],
            source=source,
            tags=tags,
            memory_key=preference["memory_key"],
            subcategory=preference["subcategory"],
            scope=preference["scope"],
            confidence=preference["confidence"],
        )
        results.append(
            {
                "preference": preference,
                "saved": saved,
            }
        )

    return results


def build_preference_memory(target, polarity):
    domain = "food"

    return {
        "target": target,
        "domain": domain,
        "polarity": polarity,
        "confidence": 90,
        "content": build_content(target, polarity),
        "memory_key": build_memory_key(target),
        "category": "preference",
        "subcategory": POLARITY_SUBCATEGORY[polarity],
        "scope": "user",
        "importance": 9,
    }


def build_content(target, polarity):
    if polarity == "like":
        return f"ユーザーは{target}が好きです。"

    if polarity == "not_like":
        return f"ユーザーは{target}が好きではありません。"

    return f"ユーザーは{target}が嫌いです。"


def build_memory_key(target):
    return f"preference:food:{target}"


def normalize_target(target):
    target = str(target).strip()

    for prefix in ("私は", "僕は", "俺は", "わたしは", "ぼくは"):
        if target.startswith(prefix):
            target = target[len(prefix):]

    return target.strip()
