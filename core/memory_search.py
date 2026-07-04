MEMORY_SEARCH_PATTERNS = [
    "について覚えてる",
    "を覚えてる",
    "について記憶ある",
    "に関する記憶を探して",
    "のmemoryを探して",
    "のMemoryを探して",
    "前に保存した",
]

MEMORY_SEARCH_PREVIEW_MAX_CHARS = 240


def detect_memory_search_intent(user_input):
    """ユーザー入力が保存済みMemory検索かどうかを簡易判定します。

    Ver2.20ではLLMによるIntent判定は使わず、代表的な表現だけを扱います。
    """
    text = _clean_text(user_input)

    if not text:
        return {
            "is_memory_search": False,
            "query": "",
            "reason": "入力が空です。",
        }

    if "今保存した記憶" in text or "直近保存した記憶" in text:
        return {
            "is_memory_search": False,
            "query": "",
            "reason": "直近保存Memory確認は別フローで扱います。",
        }

    query = _extract_query(text)

    if not query:
        return {
            "is_memory_search": False,
            "query": "",
            "reason": "Memory検索表現ではありません。",
        }

    return {
        "is_memory_search": True,
        "query": query,
        "reason": "保存済みMemory検索として扱います。",
    }


def search_memories(query, search_func=None, limit=5):
    """保存済みMemoryをキーワードで検索します。

    search_funcを渡すと、自動チェックではDBを触らずfake検索に差し替えられます。
    search_funcがない場合も、既存のget_memoriesを使うread-only検索に留めます。
    """
    normalized_query = _clean_text(query)

    if not normalized_query:
        return _build_search_result(
            status="not_found",
            action="search_memory",
            query=normalized_query,
            results=[],
            message="検索したいMemoryのキーワードが空でした。",
        )

    try:
        raw_results = _run_search(normalized_query, search_func=search_func, limit=limit)
    except Exception as error:
        return _build_search_result(
            status="search_unavailable",
            action="search_memory_unavailable",
            query=normalized_query,
            results=[],
            message=(
                "現在のMemory構造では安全に検索できませんでした。\n"
                "DBスキーマ変更なしで対応できる方法を確認中です。"
            ),
            error=str(error),
        )

    results = [_normalize_memory_result(item) for item in raw_results[:limit]]
    results = [result for result in results if result.get("content")]

    if not results:
        return _build_search_result(
            status="not_found",
            action="search_memory",
            query=normalized_query,
            results=[],
            message=(
                f"保存済みMemoryから「{normalized_query}」に関する内容は見つかりませんでした。\n"
                "必要なら、関連するURLや情報を送ってください。"
            ),
        )

    return _build_search_result(
        status="found",
        action="search_memory",
        query=normalized_query,
        results=results,
        message="保存済みMemoryから関連しそうな内容を見つけました。",
    )


def format_memory_search_response(search_result):
    """Memory検索結果を、会話で読みやすい短い返答にします。"""
    status = search_result.get("status")

    if status != "found":
        return search_result.get("message", "Memory検索結果を確認できませんでした。")

    lines = [
        search_result.get("message", "保存済みMemoryから関連しそうな内容を見つけました。"),
        "",
    ]

    for index, result in enumerate(search_result.get("results", []), start=1):
        lines.append(f"{index}. {_shorten_text(result.get('content'))}")

        source_url = _clean_text(result.get("source_url"))
        source_tool = _clean_text(result.get("source_tool"))
        created_at = _clean_text(result.get("created_at"))

        if source_url:
            lines.append(f"   URL: {source_url}")

        if source_tool:
            lines.append(f"   保存元: {source_tool}")

        if created_at:
            lines.append(f"   保存日時: {created_at}")

        lines.append("")

    return "\n".join(lines).rstrip()


def _extract_query(text):
    for pattern in MEMORY_SEARCH_PATTERNS:
        if pattern in text:
            if pattern == "前に保存した":
                query = text.split(pattern, 1)[-1]
                return _clean_query_suffix(query)

            query = text.split(pattern, 1)[0]
            return _clean_query_suffix(query)

    return ""


def _run_search(query, search_func=None, limit=5):
    if search_func is not None:
        return list(search_func(query, limit=limit) or [])

    from database.memory_manager import get_memories

    memories = get_memories(limit=100, active_only=True)
    normalized_query = _normalize_for_search(query)
    matches = []

    for memory in memories:
        haystack = " ".join(
            [
                _get_value(memory, "content"),
                _get_value(memory, "source"),
                _get_value(memory, "tags"),
                _get_value(memory, "category"),
                _get_value(memory, "memory_key"),
                _get_value(memory, "subcategory"),
            ]
        )

        if normalized_query in _normalize_for_search(haystack):
            matches.append(memory)

        if len(matches) >= limit:
            break

    return matches


def _normalize_memory_result(memory):
    source = _get_value(memory, "source")

    return {
        "content": _clean_text(_get_value(memory, "content")),
        "source_url": _extract_source_url(memory),
        "source_tool": _clean_text(_get_value(memory, "source_tool") or source),
        "created_at": _clean_text(_get_value(memory, "created_at")),
    }


def _extract_source_url(memory):
    for key in ["source_url", "url", "final_url"]:
        value = _clean_text(_get_value(memory, key))

        if value:
            return value

    content = _clean_text(_get_value(memory, "content"))

    if "URL:" not in content:
        return ""

    after_url = content.split("URL:", 1)[-1].strip()
    return after_url.split()[0].strip() if after_url else ""


def _build_search_result(status, action, query, results, message, error=None):
    result = {
        "status": status,
        "action": action,
        "query": query,
        "results": list(results),
        "message": message,
    }

    if error:
        result["error"] = error

    return result


def _get_value(obj, key, default=""):
    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(key, default)

    return getattr(obj, key, default)


def _clean_query_suffix(text):
    query = _clean_text(text).strip("。．.、,！!？?「」『』（）()[] ")
    suffixes = [
        "を見せて",
        "見せて",
        "を探して",
        "探して",
        "について",
    ]

    for suffix in suffixes:
        if query.endswith(suffix):
            query = query[: -len(suffix)].strip()

    return query.strip("。．.、,！!？?「」『』（）()[] ")


def _clean_text(value):
    if value is None:
        return ""

    return " ".join(str(value).split())


def _shorten_text(value, max_chars=MEMORY_SEARCH_PREVIEW_MAX_CHARS):
    text = _clean_text(value)

    if len(text) <= max_chars:
        return text

    return f"{text[:max_chars].rstrip()}..."


def _normalize_for_search(value):
    return _clean_text(value).lower()
