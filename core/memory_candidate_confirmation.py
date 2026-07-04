SAVE_WORDS = ["保存する", "はい", "yes", "ok", "1"]
REJECT_WORDS = ["保存しない", "いいえ", "no", "3"]
POSTPONE_WORDS = ["後で確認", "後で", "あとで", "4"]
EDIT_WORDS = ["編集して保存", "編集", "2"]


def resolve_memory_candidate_confirmation_response(user_input, pending_candidate):
    """Memory Candidateへの確認応答をdry-runで解釈します。

    Ver2.13では保存処理を呼ばず、ユーザーの意図だけを判定します。
    """
    normalized_input = _normalize_user_input(user_input)
    candidate = _normalize_candidate(pending_candidate)

    if _matches_any(normalized_input, REJECT_WORDS):
        return _build_result(
            status="rejected",
            action="discard_candidate",
            message="Memory Candidateは保存しません。",
            candidate=candidate,
        )

    if _matches_any(normalized_input, POSTPONE_WORDS):
        return _build_result(
            status="postponed",
            action="postpone_candidate",
            message="Memory Candidateを後で確認する候補として扱います。ただしDB保存はまだしません。",
            candidate=candidate,
        )

    if _matches_any(normalized_input, EDIT_WORDS):
        return _build_result(
            status="edit_requested",
            action="edit_candidate_dry_run",
            requires_followup=True,
            message=(
                "編集して保存する意図を確認しました。"
                "ただしVer2.13ではまだ保存しません。"
            ),
            candidate=candidate,
        )

    if _matches_any(normalized_input, SAVE_WORDS):
        return _build_result(
            status="confirmed",
            action="save_requested_dry_run",
            message="保存要求は受け取りましたが、Ver2.13ではまだMemory保存しません。",
            candidate=candidate,
        )

    return _build_result(
        status="unclear",
        action="ask_clarification",
        requires_followup=True,
        message="保存する、保存しない、編集して保存、後で確認 のどれかで答えてください。",
        candidate=candidate,
    )


def _build_result(
    status,
    action,
    message,
    candidate,
    requires_followup=False,
):
    return {
        "status": status,
        "action": action,
        "should_save": False,
        "should_execute": False,
        "requires_followup": requires_followup,
        "message": message,
        "candidate": candidate,
    }


def _normalize_user_input(user_input):
    return " ".join(str(user_input or "").strip().lower().split())


def _normalize_candidate(pending_candidate):
    if pending_candidate is None:
        return {}

    if isinstance(pending_candidate, dict):
        return dict(pending_candidate)

    return {"value": pending_candidate}


def _matches_any(normalized_input, words):
    if not normalized_input:
        return False

    return any(_normalize_user_input(word) == normalized_input for word in words)
