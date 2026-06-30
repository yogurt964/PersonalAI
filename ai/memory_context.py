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

VALID_MEMORY_USAGES = ["minimal", "normal", "detailed"]


def build_memory_context(memories, memory_usage="normal"):
    """長期記憶を、LLMに渡しやすい分類済みテキストへ変換します。"""
    memory_usage = normalize_memory_usage(memory_usage)
    active_memories = filter_active_memories(memories)
    usage_memories = filter_memories_by_usage(active_memories, memory_usage)
    sorted_memories = sort_memories(usage_memories)
    limited_memories = sorted_memories[:MAX_TOTAL_MEMORIES]
    grouped_memories = group_memories_by_section(limited_memories)

    lines = [
        "【長期記憶】",
        "以下はユーザーやプロジェクトに関する記憶です。",
        "確定情報を優先してください。",
        "記憶にないことは推測で断定しないでください。",
        "",
        "【Memory利用方針】",
        build_memory_usage_guidance(memory_usage),
        "",
    ]

    if not limited_memories:
        lines.append("現在、利用できる長期記憶はありません。")
        return "\n".join(lines).rstrip()

    for section_name in SECTION_ORDER:
        section_memories = grouped_memories.get(section_name, [])

        if not section_memories:
            continue

        lines.append(f"【{section_name}】")

        for memory in section_memories[:MAX_MEMORIES_PER_SECTION]:
            lines.append(format_memory_line(memory))

        lines.append("")

    return "\n".join(lines).rstrip()


def normalize_memory_usage(memory_usage):
    """想定外の値が来た場合も、既定のnormalとして安全に扱います。"""
    if memory_usage in VALID_MEMORY_USAGES:
        return memory_usage

    return "normal"


def build_memory_usage_guidance(memory_usage):
    """memory_usageごとに、LLMへ渡すMemoryの使い方を変えます。"""
    if memory_usage == "minimal":
        return (
            "memory_usage: minimal。通常会話ではMemoryを控えめに使う。"
            "Preference情報を毎回話題に出さない。"
            "単なる挨拶、応援、雑談では好きな食べ物などを無理に出さない。"
        )

    if memory_usage == "detailed":
        return (
            "memory_usage: detailed。ユーザーが明示的に記憶参照を求めた場合は詳しく使う。"
            "保存済みMemoryを分かる範囲で整理して答える。"
            "分からないことは作らない。"
        )

    return (
        "memory_usage: normal。関連が強いMemoryだけ使う。"
        "関係の薄いMemoryは使わない。"
        "Preference情報は、好み・おすすめ・食事・選択など会話と直接関係がある場合だけ自然に使う。"
    )


def filter_memories_by_usage(memories, memory_usage):
    """通常会話では長期記憶の詳細を渡さず、記憶参照では詳しく渡します。"""
    if memory_usage == "minimal":
        return []

    return memories


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
