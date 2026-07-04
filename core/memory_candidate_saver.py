RISK_LEVEL_BLOCKED = {"high"}


def build_memory_text_from_candidate(candidate):
    """Memory Candidateを、既存Memoryに保存できる1つのテキストへ整形します。"""
    candidate = _normalize_candidate(candidate)
    summary = _select_summary(candidate)
    title = _clean_text(candidate.get("title")) or "(タイトルなし)"
    source_url = _clean_text(candidate.get("source_url")) or "(URLなし)"
    source_tool = _clean_text(candidate.get("source_tool")) or "unknown"

    return (
        "[Reader Summary]\n"
        f"Title: {title}\n"
        f"URL: {source_url}\n"
        f"Summary: {summary}\n"
        f"Source: {source_tool}"
    )


def save_memory_candidate(candidate, save_memory_func):
    """ユーザー確認済みのMemory Candidateを既存Memory保存関数へ渡します。

    DBスキーマ変更や専用テーブル作成は行わず、既存のsave_memory互換関数だけを使います。
    """
    candidate = _normalize_candidate(candidate)

    if not candidate:
        return _build_result(
            status="save_unavailable",
            action="save_memory_candidate_unavailable",
            should_save=False,
            should_execute=False,
            message="現在の保存機構ではMemory Candidateを安全に保存できません。",
            candidate=candidate,
        )

    if _clean_text(candidate.get("risk_level")).lower() in RISK_LEVEL_BLOCKED:
        return _build_result(
            status="save_blocked_high_risk",
            action="save_memory_candidate_blocked_high_risk",
            should_save=False,
            should_execute=False,
            message=(
                "この候補はリスクが高いため、Ver2.17では自動保存しません。"
                "保存する場合は、保存内容を短く編集してから再確認してください。"
            ),
            candidate=candidate,
        )

    if save_memory_func is None:
        return _build_result(
            status="save_unavailable",
            action="save_memory_candidate_unavailable",
            should_save=False,
            should_execute=False,
            message="現在の保存機構ではMemory Candidateを安全に保存できません。",
            candidate=candidate,
        )

    memory_text = build_memory_text_from_candidate(candidate)

    try:
        saved = save_memory_func(
            memory_text,
            "knowledge",
            "knowledge",
            _importance_to_number(candidate.get("importance")),
            _clean_text(candidate.get("source_tool")) or "memory_candidate",
            _build_tags(candidate),
            None,
            _clean_text(candidate.get("candidate_type")) or "reader_summary",
            "global",
            80,
            None,
        )
    except Exception as error:
        return _build_result(
            status="save_failed",
            action="save_memory_candidate_failed",
            should_save=False,
            should_execute=False,
            message="Memory Candidateの保存に失敗しました。",
            candidate=candidate,
            memory_text=memory_text,
            error=str(error),
        )

    if not saved:
        return _build_result(
            status="save_failed",
            action="save_memory_candidate_failed",
            should_save=False,
            should_execute=False,
            message="Memory Candidateの保存に失敗しました。",
            candidate=candidate,
            memory_text=memory_text,
            error="save_memory_func returned False",
        )

    saved_candidate = dict(candidate)
    saved_candidate["should_save"] = True

    return _build_result(
        status="saved",
        action="save_memory_candidate",
        should_save=True,
        should_execute=True,
        message="Memory Candidateを長期記憶に保存しました。",
        candidate=saved_candidate,
        memory_text=memory_text,
    )


def _select_summary(candidate):
    edited_candidate = candidate.get("edited_candidate")

    if isinstance(edited_candidate, dict):
        edited_summary = _clean_text(edited_candidate.get("summary"))

        if edited_summary:
            return edited_summary

    summary = _clean_text(candidate.get("summary"))

    if summary:
        return summary

    title = _clean_text(candidate.get("title"))
    source_url = _clean_text(candidate.get("source_url"))

    if title and source_url:
        return f"{title} ({source_url})"

    return title or source_url or "(要約なし)"


def _build_tags(candidate):
    tags = [
        "memory_candidate",
        _clean_text(candidate.get("candidate_type")),
        _clean_text(candidate.get("source_tool")),
    ]

    return ",".join(tag for tag in tags if tag)


def _importance_to_number(importance):
    text = _clean_text(importance).lower()
    mapping = {
        "low": 3,
        "medium": 6,
        "high": 8,
        "review": 5,
    }

    if text in mapping:
        return mapping[text]

    try:
        return int(importance)
    except (TypeError, ValueError):
        return 5


def _build_result(
    status,
    action,
    should_save,
    should_execute,
    message,
    candidate,
    memory_text="",
    error=None,
):
    result = {
        "status": status,
        "action": action,
        "should_save": should_save,
        "should_execute": should_execute,
        "message": message,
        "candidate": candidate,
        "memory_text": memory_text,
    }

    if error:
        result["error"] = error

    return result


def _normalize_candidate(candidate):
    if candidate is None:
        return {}

    if isinstance(candidate, dict):
        return dict(candidate)

    return {"value": candidate}


def _clean_text(value):
    if value is None:
        return ""

    return " ".join(str(value).split())
