import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


def check_file_exists(label, path):
    if path.exists():
        print(f"[OK] {label} exists")
        return 0

    print(f"[NG] {label} missing -> {path}")
    return 1


def check_true(label, condition):
    if condition:
        print(f"[OK] {label}")
        return 0

    print(f"[NG] {label}")
    return 1


def check_words(label, path, words):
    if not path.exists():
        print(f"[NG] {label} missing -> {path}")
        return 1

    text = path.read_text(encoding="utf-8")
    missing_words = [word for word in words if word not in text]

    if missing_words:
        print(f"[NG] {label} missing words -> {missing_words}")
        return 1

    print(f"[OK] {label} required words")
    return 0


def get_db_timestamp():
    db_path = PROJECT_ROOT / "data" / "personal_ai.db"
    return db_path.stat().st_mtime_ns if db_path.exists() else None


def check_db_unchanged(before):
    after = get_db_timestamp()
    return check_true("check_ver2430 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2430.py").read_text(encoding="utf-8")
    forbidden_words = [
        "req" + "uests.get",
        "req" + "uests.post",
        "url" + "lib.request",
        "url" + "open(",
        "ask_" + "llm(",
        "Base.metadata." + "create_all",
        "create_" + "database(",
        "reset --" + "hard",
        "force " + "push",
        "re" + "base",
    ]
    found_words = [word for word in forbidden_words if word in source]

    if found_words:
        print(f"[NG] check_ver2430 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2430 has no forbidden words")
    return 0


def check_imports():
    try:
        from core.youtube_reader_adapter import (
            YouTubeReaderAdapter,
            extract_youtube_url_from_text,
            extract_youtube_video_id_from_text,
        )
        from core.youtube_reader_confirmation import (
            build_youtube_reader_confirmation,
            resolve_youtube_reader_confirmation_response,
        )
        from core.confirmation_intent import resolve_confirmation_intent
        from core.personal_ai import PersonalAI
        from core.tool_adapter import ToolRequest, ToolResult
        from core.tool_runner import run_tool_request
    except Exception as error:
        print(f"[NG] imports failed -> {error}")
        return 1

    YouTubeReaderAdapter
    extract_youtube_url_from_text
    extract_youtube_video_id_from_text
    build_youtube_reader_confirmation
    resolve_youtube_reader_confirmation_response
    resolve_confirmation_intent
    PersonalAI
    ToolRequest
    ToolResult
    run_tool_request

    print("[OK] imports")
    return 0


def check_video_id_extraction():
    from core.youtube_reader_adapter import (
        extract_youtube_url_from_text,
        extract_youtube_video_id_from_text,
    )

    failures = 0
    watch_url_video_id = extract_youtube_video_id_from_text(
        "この動画を読んで https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )
    failures += check_true("watch url video id", watch_url_video_id == "dQw4w9WgXcQ")

    short_url_video_id = extract_youtube_video_id_from_text("https://youtu.be/dQw4w9WgXcQ を見て")
    failures += check_true("short url video id", short_url_video_id == "dQw4w9WgXcQ")

    embed_url_video_id = extract_youtube_video_id_from_text(
        "https://www.youtube.com/embed/dQw4w9WgXcQ"
    )
    failures += check_true("embed url video id", embed_url_video_id == "dQw4w9WgXcQ")

    shorts_url_video_id = extract_youtube_video_id_from_text(
        "https://www.youtube.com/shorts/dQw4w9WgXcQ"
    )
    failures += check_true("shorts url video id", shorts_url_video_id == "dQw4w9WgXcQ")

    with_timestamp_video_id = extract_youtube_video_id_from_text(
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=30s"
    )
    failures += check_true("url with query param still parses", with_timestamp_video_id == "dQw4w9WgXcQ")

    no_url_video_id = extract_youtube_video_id_from_text("普通の会話です")
    failures += check_true("no url returns None", no_url_video_id is None)

    url_text = extract_youtube_url_from_text(
        "この動画を読んで https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )
    failures += check_true(
        "url text extraction",
        url_text == "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    )

    return failures


def _fake_transcript_fetcher(video_id):
    return [
        "YOUTUBE_TEST_MARKER_12345 ",
        "これはテスト用の字幕本文です。",
        f"動画IDは {video_id} です。",
    ]


def _empty_transcript_fetcher(video_id):
    return []


def _failing_transcript_fetcher(video_id):
    raise RuntimeError("Transcript is disabled for this video")


def check_youtube_reader_adapter():
    from core.youtube_reader_adapter import YouTubeReaderAdapter
    from core.tool_adapter import ToolRequest, ToolResult

    failures = 0

    adapter = YouTubeReaderAdapter(transcript_fetcher=_fake_transcript_fetcher)
    request = ToolRequest(
        tool_name="youtube_reader",
        action="read_youtube",
        input_data={"video_id": "dQw4w9WgXcQ"},
        requires_permission=True,
        risk_level="medium",
    )
    result = adapter.execute(request)
    failures += check_true("adapter is available", adapter.is_available() is True)
    failures += check_true("execute returns ToolResult", isinstance(result, ToolResult))
    failures += check_true("success result success", result.success is True)
    failures += check_true("success result executed", result.executed is True)
    failures += check_true(
        "success result has video_id",
        result.data.get("video_id") == "dQw4w9WgXcQ",
    )
    failures += check_true(
        "success result has transcript text",
        "テスト用の字幕本文" in result.data.get("text", ""),
    )
    failures += check_true(
        "success result has url",
        result.data.get("url") == "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    )

    missing_request = ToolRequest(
        tool_name="youtube_reader",
        action="read_youtube",
        input_data={"original_input": "特にURLを含まない普通の文章です"},
        requires_permission=True,
        risk_level="medium",
    )
    missing_adapter = YouTubeReaderAdapter(transcript_fetcher=_fake_transcript_fetcher)
    missing_result = missing_adapter.execute(missing_request)
    failures += check_true("missing video id fails", missing_result.success is False)
    failures += check_true("missing video id not executed", missing_result.executed is False)

    empty_adapter = YouTubeReaderAdapter(transcript_fetcher=_empty_transcript_fetcher)
    empty_request = ToolRequest(
        tool_name="youtube_reader",
        action="read_youtube",
        input_data={"video_id": "dQw4w9WgXcQ"},
        requires_permission=True,
        risk_level="medium",
    )
    empty_result = empty_adapter.execute(empty_request)
    failures += check_true("empty transcript fails honestly", empty_result.success is False)
    failures += check_true("empty transcript executed True", empty_result.executed is True)

    failing_adapter = YouTubeReaderAdapter(transcript_fetcher=_failing_transcript_fetcher)
    failing_result = failing_adapter.execute(empty_request)
    failures += check_true("disabled transcript fails honestly", failing_result.success is False)
    failures += check_true("disabled transcript executed True", failing_result.executed is True)
    failures += check_true(
        "disabled transcript does not pretend success",
        "読めたふりはしません" in failing_result.message,
    )

    return failures


def check_confirmation_flow():
    from core.youtube_reader_confirmation import (
        build_youtube_reader_confirmation,
        resolve_youtube_reader_confirmation_response,
    )

    confirmation = build_youtube_reader_confirmation(
        "この動画を読んで https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )
    failures = 0
    failures += check_true("confirmation needs_confirmation", confirmation.needs_confirmation is True)
    failures += check_true("confirmation has video_id", confirmation.video_id == "dQw4w9WgXcQ")
    failures += check_true("confirmation tool_name", confirmation.tool_name == "youtube_reader")

    no_url_confirmation = build_youtube_reader_confirmation("普通の会話です")
    failures += check_true(
        "no url means no confirmation needed",
        no_url_confirmation.needs_confirmation is False,
    )

    pending = confirmation.to_dict()
    pending["original_input"] = "この動画を読んで https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    confirmed = resolve_youtube_reader_confirmation_response("いいよ", pending)
    failures += check_true("confirmed status", confirmed.status == "confirmed")
    failures += check_true(
        "confirmed candidate tool_name",
        confirmed.tool_request_candidate["tool_name"] == "youtube_reader",
    )

    cancelled = resolve_youtube_reader_confirmation_response("キャンセル", pending)
    failures += check_true("cancelled status", cancelled.status == "cancelled")

    unclear = resolve_youtube_reader_confirmation_response("よくわからない", pending)
    failures += check_true("unclear status", unclear.status == "unclear")

    no_pending = resolve_youtube_reader_confirmation_response("いいよ", None)
    failures += check_true("no pending status", no_pending.status == "no_pending")

    return failures


def check_tool_runner_permission():
    from core.tool_adapter import ToolRequest
    from core.tool_execution_log import ToolExecutionLogger
    from core.tool_registry import ToolRegistry
    from core.tool_runner import run_tool_request
    from core.youtube_reader_adapter import YouTubeReaderAdapter

    registry = ToolRegistry()
    registry.register(YouTubeReaderAdapter(transcript_fetcher=_fake_transcript_fetcher))
    logger = ToolExecutionLogger()
    request = ToolRequest(
        tool_name="youtube_reader",
        action="read_youtube",
        input_data={"video_id": "dQw4w9WgXcQ"},
        requires_permission=True,
        risk_level="medium",
    )

    blocked = run_tool_request(
        request,
        registry=registry,
        user_confirmed=False,
        logger=logger,
    )
    executed = run_tool_request(
        request,
        registry=registry,
        user_confirmed=True,
        logger=logger,
    )

    failures = 0
    failures += check_true("permission needed", blocked.permission_decision.needs_user_confirmation is True)
    failures += check_true("no permission not executed", blocked.result.executed is False)
    failures += check_true("confirmed executed", executed.result.executed is True)
    failures += check_true("confirmed success", executed.result.success is True)
    failures += check_true("logger recorded both results", logger.count() == 2)

    return failures


def fake_llm_responder(messages):
    system_texts = [message["content"] for message in messages if message["role"] == "system"]
    user_texts = [message["content"] for message in messages if message["role"] == "user"]
    document_in_context = any("YOUTUBE_TEST_MARKER_12345" in text for text in system_texts)
    last_user_text = user_texts[-1] if user_texts else ""
    return f"FAKE_LLM_ANSWER|document_in_context={document_in_context}|user={last_user_text}"


def build_lightweight_personal_ai():
    from core.capability_manager import CapabilityManager
    from core.input_analyzer import InputAnalyzer
    from core.personal_ai import PersonalAI
    from core.tool_execution_log import ToolExecutionLogger
    from core.tool_registry import ToolRegistry
    from core.youtube_reader_adapter import YouTubeReaderAdapter

    ai = PersonalAI.__new__(PersonalAI)
    ai.input_analyzer = InputAnalyzer()
    ai.capability_manager = CapabilityManager()
    ai.web_reader_fetcher = None
    ai.ask_llm_func = fake_llm_responder
    registry = ToolRegistry()
    registry.register(YouTubeReaderAdapter(transcript_fetcher=_fake_transcript_fetcher))
    ai.tool_registry = registry
    ai.tool_execution_logger = ToolExecutionLogger()
    ai.pending_preference_confirmation = None
    ai.pending_memory_candidate_confirmation = None
    ai.pending_memory_candidate_edit = None
    ai.pending_web_reader_confirmation = None
    ai.pending_file_reader_confirmation = None
    ai.pending_pdf_reader_confirmation = None
    ai.pending_word_reader_confirmation = None
    ai.pending_excel_reader_confirmation = None
    ai.pending_pptx_reader_confirmation = None
    ai.pending_youtube_reader_confirmation = None
    for prefix in [
        "web_reader",
        "file_reader",
        "pdf_reader",
        "word_reader",
        "excel_reader",
        "pptx_reader",
        "youtube_reader",
    ]:
        setattr(ai, f"last_{prefix}_confirmation", None)
        setattr(ai, f"last_{prefix}_confirmation_result", None)
        setattr(ai, f"last_{prefix}_tool_request_candidate", None)
        setattr(ai, f"last_{prefix}_tool_run_result", None)
        setattr(ai, f"last_{prefix}_tool_result", None)
    ai.last_read_document = None
    ai.last_tool_execution_record = None
    ai.last_memory_candidate = None
    ai.last_memory_candidate_confirmation_result = None
    ai.last_memory_candidate_save_result = None
    ai.last_saved_memory_candidate_result = None
    ai.last_memory_usage = "normal"
    ai.last_conversation_mode = "chat"
    ai.last_conversation_quality_guidance = None
    ai.last_input_analysis = None
    ai.last_response = None
    ai.save_user_message = lambda _message: None
    ai.save_assistant_message = lambda _message: None
    return ai


def check_personal_ai_flow():
    failures = 0

    # youtu.be形式（クエリ文字列の"?"を含まない）で、素の読み取り→プレビュー表示を確認する。
    ai_preview = build_lightweight_personal_ai()
    confirmation_response = ai_preview.handle_user_input("この動画 https://youtu.be/dQw4w9WgXcQ")
    read_response = ai_preview.handle_user_input("いいよ")
    failures += check_true(
        "confirmation shown",
        "https://youtu.be/dQw4w9WgXcQ" in confirmation_response,
    )
    failures += check_true("reads with YouTube Reader", "YouTube Readerで字幕を取得しました" in read_response)
    failures += check_true("shows transcript preview", "テスト用の字幕本文" in read_response)
    failures += check_true("pending cleared", ai_preview.pending_youtube_reader_confirmation is None)
    failures += check_true(
        "last_read_document stored as youtube_reader",
        ai_preview.last_read_document is not None
        and ai_preview.last_read_document.get("source_tool") == "youtube_reader",
    )

    ai_summarize = build_lightweight_personal_ai()
    ai_summarize.handle_user_input(
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ 内容を要約してください"
    )
    summarize_response = ai_summarize.handle_user_input("はい")
    failures += check_true("combined flow calls fake LLM", "FAKE_LLM_ANSWER" in summarize_response)
    failures += check_true(
        "combined flow LLM sees transcript",
        "document_in_context=True" in summarize_response,
    )

    ai_cancel = build_lightweight_personal_ai()
    ai_cancel.handle_user_input("この動画 https://youtu.be/dQw4w9WgXcQ")
    cancel_response = ai_cancel.handle_user_input("キャンセル")
    failures += check_true("cancel not executed", "YouTube Readerは実行しませんでした" in cancel_response)
    failures += check_true("cancel pending cleared", ai_cancel.pending_youtube_reader_confirmation is None)

    ai_no_url = build_lightweight_personal_ai()
    no_url_response = ai_no_url.handle_user_input("このYouTube動画を見て要約して")
    failures += check_true(
        "no url falls back to capability gate (still honest about being unimplemented for that case)",
        "未実装" in no_url_response,
    )

    return failures


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"
    core = PROJECT_ROOT / "core"

    files = [
        ("youtube_reader_adapter.py", core / "youtube_reader_adapter.py"),
        ("youtube_reader_confirmation.py", core / "youtube_reader_confirmation.py"),
        ("confirmation_intent.py", core / "confirmation_intent.py"),
        ("personal_ai.py", core / "personal_ai.py"),
        ("check_ver2430.py", scripts / "check_ver2430.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("requirements.txt", PROJECT_ROOT / "requirements.txt"),
        ("changelog.md", docs / "changelog.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_imports()
    failures += check_video_id_extraction()
    failures += check_youtube_reader_adapter()
    failures += check_confirmation_flow()
    failures += check_tool_runner_permission()
    failures += check_personal_ai_flow()

    failures += check_words(
        "requirements.txt",
        PROJECT_ROOT / "requirements.txt",
        [
            "youtube-transcript-api",
        ],
    )

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
            "check_ver2430.py",
        ],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        [
            "## Version 2.43",
            "YouTube Reader",
            "scripts/check_ver2430.py",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        [
            "現在バージョン:",
            "Ver2.43: YouTube Reader最小実装",
        ],
    )

    failures += check_check_script_has_no_forbidden_words()
    failures += check_db_unchanged(db_timestamp_before)

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
