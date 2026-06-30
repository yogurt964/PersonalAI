DETAILED_MEMORY_KEYWORDS = [
    "私について覚えている",
    "私について覚えてる",
    "私について",
    "私の情報",
    "覚えていること",
    "覚えてること",
    "何を覚えて",
    "何覚えて",
    "記憶している内容",
    "記憶してる内容",
    "記憶内容",
    "記憶を確認",
    "Memoryを確認",
    "memoryを確認",
    "メモリーを確認",
    "好みを覚えて",
    "好きなものを覚えて",
]

MEMORY_REFERENCE_WORDS = [
    "記憶",
    "Memory",
    "memory",
    "メモリー",
]

REFERENCE_REQUEST_WORDS = [
    "教えて",
    "見せて",
    "確認",
    "何",
    "内容",
    "ありますか",
    "ある？",
    "ある?",
    "？",
    "?",
]

MINIMAL_MEMORY_KEYWORDS = [
    "こんにちは",
    "おはよう",
    "こんばんは",
    "ありがとう",
    "疲れました",
    "疲れた",
    "応援",
    "励まして",
    "雑談",
    "挨拶",
]

NORMAL_MEMORY_KEYWORDS = [
    "おすすめ",
    "オススメ",
    "候補",
    "提案",
    "合いそう",
    "方針",
    "踏まえて",
    "考えて",
    "次の作業",
    "開発",
]


def decide_memory_usage(user_input, input_analysis=None):
    """ユーザー入力に対して、Memoryをどの強さで使うかを決めます。

    まずは分かりやすいキーワードベースです。
    将来的にはInputAnalyzerやPlannerの結果をより細かく使えるようにします。
    """
    text = str(user_input or "").strip()

    if not text:
        return "minimal"

    if _contains_any(text, DETAILED_MEMORY_KEYWORDS):
        return "detailed"

    if _is_memory_reference_request(text):
        return "detailed"

    if _contains_any(text, NORMAL_MEMORY_KEYWORDS):
        return "normal"

    task_type = _get_context_value(input_analysis, "task_type")

    if task_type in ["recommend", "summarize", "create_document"]:
        return "normal"

    if task_type == "question" and not _contains_any(text, MINIMAL_MEMORY_KEYWORDS):
        return "normal"

    if _contains_any(text, MINIMAL_MEMORY_KEYWORDS):
        return "minimal"

    if task_type == "chat":
        return "minimal"

    return "normal"


def _is_memory_reference_request(text):
    """記憶そのものを見たい・確認したい入力かを判定します。"""
    return _contains_any(text, MEMORY_REFERENCE_WORDS) and _contains_any(
        text,
        REFERENCE_REQUEST_WORDS,
    )


def _contains_any(text, keywords):
    return any(keyword in text for keyword in keywords)


def _get_context_value(context, key, default=None):
    if context is None:
        return default

    if isinstance(context, dict):
        return context.get(key, default)

    return getattr(context, key, default)
