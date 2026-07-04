SAVE_WORDS = [
    "保存する",
    "保存して",
    "覚えて",
    "記憶して",
    "これ覚えて",
    "それ覚えて",
    "保存お願いします",
    "はい",
    "yes",
    "ok",
    "1",
]
REJECT_WORDS = [
    "保存しない",
    "保存しないで",
    "覚えないで",
    "いらない",
    "不要",
    "捨てて",
    "いいえ",
    "no",
    "3",
]
POSTPONE_WORDS = ["後で確認", "後で", "あとで", "あとで見る", "後回し", "保留", "4"]
EDIT_WORDS = ["編集して保存", "修正して保存", "内容を変えたい", "編集したい", "編集", "2"]
CANCEL_EDIT_WORDS = ["キャンセル", "やめる", "保存しない"]


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
                "編集内容を送ってください。"
                "ただしVer2.16ではまだMemory保存しません。"
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


def resolve_memory_candidate_edit_response(user_input, pending_candidate):
    """Memory Candidateの編集内容をdry-runで受け取ります。

    Ver2.16では編集済み候補を作るだけで、Memory保存やDB保存は行いません。
    """
    original_input = str(user_input or "").strip()
    normalized_input = _normalize_user_input(original_input)
    candidate = _normalize_candidate(pending_candidate)

    if not original_input:
        return _build_edit_result(
            status="edit_empty",
            action="ask_edit_content",
            message=(
                "編集内容が空でした。"
                "Memory Candidateに反映したい内容を送ってください。"
                "Ver2.16ではまだMemory保存しません。"
            ),
            candidate=candidate,
            edited_candidate=dict(candidate),
            edited_summary="",
            requires_followup=True,
        )

    if _matches_any(normalized_input, CANCEL_EDIT_WORDS):
        return _build_edit_result(
            status="edit_cancelled",
            action="cancel_edit_candidate",
            message="Memory Candidateの編集をキャンセルしました。保存はしていません。",
            candidate=candidate,
            edited_candidate=dict(candidate),
            edited_summary="",
        )

    edited_candidate = dict(candidate)
    edited_candidate["summary"] = original_input
    edited_candidate["edited"] = True
    edited_candidate["edit_source"] = "user_input"
    edited_candidate["should_save"] = False

    return _build_edit_result(
        status="edited_dry_run",
        action="edit_candidate_content_dry_run",
        message=(
            "編集内容を受け取りました。"
            "Ver2.16ではまだMemory保存せず、編集済み候補としてdry-run保持します。"
        ),
        candidate=candidate,
        edited_candidate=edited_candidate,
        edited_summary=original_input,
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


def _build_edit_result(
    status,
    action,
    message,
    candidate,
    edited_candidate,
    edited_summary,
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
        "edited_candidate": edited_candidate,
        "edited_summary": edited_summary,
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
