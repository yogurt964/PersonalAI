from datetime import datetime

from database.memory_manager import get_memories


def analyze_forgetting_candidates(
    memories: list,
    max_candidates: int = 20,
    min_score: int = 50,
) -> list[dict]:
    """Memory一覧から忘却候補をdry-runで判定します。

    この関数は候補を提案するだけです。
    DB削除、物理削除、is_active変更は一切行いません。
    """
    candidates = []

    for memory in memories or []:
        if is_inactive_memory(memory):
            continue

        score, reasons = calculate_forgetting_score(memory)

        if score < min_score:
            continue

        candidates.append(
            {
                "memory_id": get_memory_value(memory, "id"),
                "memory_key": get_memory_value(memory, "memory_key"),
                "content": get_memory_value(memory, "content", ""),
                "score": score,
                "reasons": reasons,
                "recommended_action": "review_for_deactivation",
                "dry_run": True,
            }
        )

    candidates.sort(key=lambda candidate: candidate["score"], reverse=True)
    return candidates[:max_candidates]


def get_forgetting_candidates(
    limit: int = 100,
    max_candidates: int = 20,
    min_score: int = 50,
) -> list[dict]:
    """DBから有効なMemoryを読み取り、忘却候補をdry-runで返します。

    get_memories() は読み取り専用で使います。
    この関数もMemoryの削除や無効化は行いません。
    """
    memories = get_memories(limit=limit, active_only=True)
    return analyze_forgetting_candidates(
        memories,
        max_candidates=max_candidates,
        min_score=min_score,
    )


def calculate_forgetting_score(memory):
    """1件のMemoryに対して、忘却候補らしさのスコアと理由を返します。"""
    score = 0
    reasons = []

    importance = to_int(get_memory_value(memory, "importance", 5), 5)
    confidence = to_int(get_memory_value(memory, "confidence", 80), 80)
    content = str(get_memory_value(memory, "content", "") or "").strip()
    memory_type = normalize_text(get_memory_value(memory, "memory_type", ""))
    category = normalize_text(get_memory_value(memory, "category", ""))
    scope = normalize_text(get_memory_value(memory, "scope", ""))
    tags = normalize_text(get_memory_value(memory, "tags", ""))
    memory_key = normalize_text(get_memory_value(memory, "memory_key", ""))

    if importance <= 3:
        score += 30
        reasons.append("low_importance")

    if confidence < 50:
        score += 25
        reasons.append("low_confidence")

    if has_any_marker(scope, ["temporary", "session", "debug", "test"]):
        score += 30
        reasons.append("temporary_scope")

    if has_any_marker(category, ["temporary", "debug", "test"]):
        score += 30
        reasons.append("temporary_category")

    if has_any_marker(tags, ["temporary", "debug", "test"]):
        score += 30
        reasons.append("test_or_debug_tag")

    if is_expired(get_memory_value(memory, "expires_at")):
        score += 50
        reasons.append("expired")

    if is_very_short_content(content):
        score += 10
        reasons.append("very_short_content")

    # 重要な記憶は候補にしにくくします。自動処理はしないため、ここではスコアを下げるだけです。
    if importance >= 8:
        score -= 40

    if confidence >= 90:
        score -= 20

    if scope == "user":
        score -= 20

    if memory_type == "user_profile":
        score -= 40

    if category in ["preference", "user_profile", "core", "project"]:
        score -= 30

    if has_any_marker(memory_key, ["core", "preference", "user", "project"]):
        score -= 40

    return max(score, 0), reasons


def is_inactive_memory(memory):
    """すでに無効なMemoryは、忘却候補から除外します。"""
    is_active = get_memory_value(memory, "is_active", True)
    return is_active is False or is_active == 0


def is_expired(expires_at):
    """expires_atが過去ならTrueを返します。"""
    if not expires_at:
        return False

    try:
        expires_at_text = str(expires_at).replace("Z", "+00:00")
        expires_at_datetime = datetime.fromisoformat(expires_at_text)
    except (TypeError, ValueError):
        return False

    if expires_at_datetime.tzinfo is not None:
        return expires_at_datetime < datetime.now(expires_at_datetime.tzinfo)

    return expires_at_datetime < datetime.now()


def is_very_short_content(content):
    """短すぎて意味が薄そうなcontentを判定します。"""
    return len(content.strip()) <= 5


def get_memory_value(memory, key, default=None):
    """dictとMemoryオブジェクトの両方から値を取り出します。"""
    if memory is None:
        return default

    if isinstance(memory, dict):
        return memory.get(key, default)

    return getattr(memory, key, default)


def normalize_text(value):
    return str(value or "").strip().lower()


def has_any_marker(text, markers):
    return any(marker in text for marker in markers)


def to_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
