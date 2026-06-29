MAX_TOTAL_MEMORIES = 20
MAX_MEMORIES_PER_SECTION = 5

SECTION_ORDER = [
    "ユーザー情報",
    "好み・方針",
    "プロジェクト",
    "現在の作業",
    "知識",
    "その他",
]

CATEGORY_TO_SECTION = {
    "name": "ユーザー情報",
    "favorite_food": "ユーザー情報",
    "preference": "好み・方針",
    "personality": "好み・方針",
    "goal": "好み・方針",
    "project": "プロジェクト",
    "current_activity": "現在の作業",
    "knowledge": "知識",
    "other": "その他",
}

SCOPE_TO_SECTION = {
    "user": "ユーザー情報",
    "project": "プロジェクト",
    "knowledge": "知識",
}


def build_memory_context(memories):
    """長期記憶を、LLMに渡しやすい分類済みテキストへ変換します。"""
    active_memories = filter_active_memories(memories)
    sorted_memories = sort_memories(active_memories)
    limited_memories = sorted_memories[:MAX_TOTAL_MEMORIES]
    grouped_memories = group_memories_by_section(limited_memories)

    lines = [
        "【長期記憶】",
        "以下はユーザーやプロジェクトに関する記憶です。",
        "確定情報を優先してください。",
        "記憶にないことは推測で断定しないでください。",
        "",
    ]

    if not limited_memories:
        return "【長期記憶】\n現在、利用できる長期記憶はありません。"

    for section_name in SECTION_ORDER:
        section_memories = grouped_memories.get(section_name, [])

        if not section_memories:
            continue

        lines.append(f"【{section_name}】")

        for memory in section_memories[:MAX_MEMORIES_PER_SECTION]:
            lines.append(format_memory_line(memory))

        lines.append("")

    return "\n".join(lines).rstrip()


def filter_active_memories(memories):
    """is_activeがFalseの記憶だけを除外します。"""
    active_memories = []

    for memory in memories:
        is_active = getattr(memory, "is_active", None)

        if is_active is False or is_active == 0:
            continue

        if not getattr(memory, "content", None):
            continue

        active_memories.append(memory)

    return active_memories


def sort_memories(memories):
    """重要度、確信度、更新日時の順で、重要そうな記憶を先にします。"""
    return sorted(
        memories,
        key=lambda memory: (
            to_int(getattr(memory, "importance", 0)),
            to_int(getattr(memory, "confidence", 80)),
            safe_text(getattr(memory, "updated_at", "")),
            safe_text(getattr(memory, "created_at", "")),
        ),
        reverse=True,
    )


def group_memories_by_section(memories):
    """categoryやscopeを使って、記憶を見出しごとに分けます。"""
    grouped_memories = {section_name: [] for section_name in SECTION_ORDER}

    for memory in memories:
        section_name = detect_section(memory)
        grouped_memories[section_name].append(memory)

    return grouped_memories


def detect_section(memory):
    """1つの記憶を、LLMに渡すときの分類名へ変換します。"""
    category = safe_text(getattr(memory, "category", "")).lower()
    scope = safe_text(getattr(memory, "scope", "")).lower()

    if scope in SCOPE_TO_SECTION:
        return SCOPE_TO_SECTION[scope]

    return CATEGORY_TO_SECTION.get(category, "その他")


def format_memory_line(memory):
    """1件の記憶を、重要度や確信度つきの1行にします。"""
    content = safe_text(getattr(memory, "content", ""))
    importance = to_int(getattr(memory, "importance", 0))
    confidence = to_int(getattr(memory, "confidence", 80))
    scope = safe_text(getattr(memory, "scope", "global"))
    memory_key = safe_text(getattr(memory, "memory_key", ""))

    details = [
        f"重要度:{importance}",
        f"確信度:{confidence}",
    ]

    if scope and scope != "global":
        details.append(f"範囲:{scope}")

    if memory_key:
        details.append(f"key:{memory_key}")

    if confidence < 50:
        details.append("低確信")

    if not content.endswith(("。", "！", "？", "!", "?")):
        content = f"{content}。"

    return f"- {content}{' / '.join(details)}"


def to_int(value, default=0):
    """Noneや文字列が来ても、安全に整数へ変換します。"""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_text(value):
    """Noneを空文字として扱い、文字列として安全に使います。"""
    if value is None:
        return ""

    return str(value)
