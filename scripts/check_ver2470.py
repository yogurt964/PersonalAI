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
    return check_true("check_ver2470 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2470.py").read_text(encoding="utf-8")
    forbidden_words = [
        "req" + "uests.get",
        "req" + "uests.post",
        "ask_" + "llm(",
        "Base.metadata." + "create_all",
        "create_" + "database(",
        "reset --" + "hard",
        "force " + "push",
        "re" + "base",
    ]
    found_words = [word for word in forbidden_words if word in source]

    if found_words:
        print(f"[NG] check_ver2470 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2470 has no forbidden words")
    return 0


def check_imports():
    try:
        from core.image_reader_adapter import ImageReaderAdapter, extract_image_path_from_text
        from core.image_reader_confirmation import (
            build_image_reader_confirmation,
            resolve_image_reader_confirmation_response,
        )
        from core.vision_router import VISION_BACKEND_LOCAL, choose_vision_backend
        from core.confirmation_intent import resolve_confirmation_intent
        from core.personal_ai import PersonalAI
        from core.tool_adapter import ToolRequest, ToolResult
        from core.tool_runner import run_tool_request
    except Exception as error:
        print(f"[NG] imports failed -> {error}")
        return 1

    ImageReaderAdapter
    extract_image_path_from_text
    build_image_reader_confirmation
    resolve_image_reader_confirmation_response
    VISION_BACKEND_LOCAL
    choose_vision_backend
    resolve_confirmation_intent
    PersonalAI
    ToolRequest
    ToolResult
    run_tool_request

    print("[OK] imports")
    return 0


def check_path_extraction():
    from core.image_reader_adapter import extract_image_path_from_text

    failures = 0
    failures += check_true(
        "bare png path detected",
        extract_image_path_from_text("この画像を見て docs/photo.png") == "docs/photo.png",
    )
    failures += check_true(
        "space-containing windows path detected",
        extract_image_path_from_text(r"C:\Users\me\Downloads\photo (1).jpg")
        == r"C:\Users\me\Downloads\photo (1).jpg",
    )
    failures += check_true(
        "no path returns None",
        extract_image_path_from_text("この画像を見て") is None,
    )
    failures += check_true(
        "non image extension is ignored",
        extract_image_path_from_text("note.txt を読んで") is None,
    )

    return failures


def check_vision_router_defaults_to_local():
    from core.vision_router import VISION_BACKEND_LOCAL, choose_vision_backend

    backend = choose_vision_backend(image_path="photo.png", user_request_text="これは何ですか？")

    return check_true(
        "vision router currently always selects local (OpenAI not connected yet)",
        backend == VISION_BACKEND_LOCAL,
    )


def _build_fake_png(tmp_path):
    path = tmp_path / "note.png"
    # 最小のPNGヘッダーバイト列。実際のvisionモデルは呼ばず、fakeのvision_describerを使う。
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\nIDATx\x9cc\xf8\xcf\xc0"
        b"\x00\x00\x03\x01\x01\x00\x18\xdd\x8d\xb0\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    return path


def _fake_vision_describer(path, original_input, backend):
    return f"IMAGE_TEST_MARKER_ADAPTER これはテスト用の画像説明です。backend={backend}"


def check_image_reader_adapter(tmp_path):
    from core.image_reader_adapter import ImageReaderAdapter
    from core.tool_adapter import ToolRequest, ToolResult

    good_file = _build_fake_png(tmp_path)
    adapter = ImageReaderAdapter(vision_describer=_fake_vision_describer)
    failures = 0

    success_request = ToolRequest(
        tool_name="image_reader",
        action="read_image",
        input_data={"path": str(good_file)},
        requires_permission=True,
        risk_level="medium",
    )
    success_result = adapter.execute(success_request)
    failures += check_true("adapter is available", adapter.is_available() is True)
    failures += check_true("execute returns ToolResult", isinstance(success_result, ToolResult))
    failures += check_true("success result success", success_result.success is True)
    failures += check_true("success result executed", success_result.executed is True)
    failures += check_true(
        "success result has file_name",
        success_result.data.get("file_name") == "note.png",
    )
    failures += check_true(
        "success result has description text",
        "テスト用の画像説明" in success_result.data.get("text", ""),
    )
    failures += check_true(
        "success result records local backend",
        success_result.data.get("backend") == "local",
    )

    missing_request = ToolRequest(
        tool_name="image_reader",
        action="read_image",
        input_data={"path": str(tmp_path / "does_not_exist.png")},
        requires_permission=True,
        risk_level="medium",
    )
    missing_result = adapter.execute(missing_request)
    failures += check_true("missing file fails", missing_result.success is False)
    failures += check_true("missing file not executed", missing_result.executed is False)

    wrong_extension_request = ToolRequest(
        tool_name="image_reader",
        action="read_image",
        input_data={"path": str(tmp_path / "note.txt")},
        requires_permission=True,
        risk_level="medium",
    )
    wrong_extension_result = adapter.execute(wrong_extension_request)
    failures += check_true("wrong extension fails", wrong_extension_result.success is False)
    failures += check_true("wrong extension not executed", wrong_extension_result.executed is False)

    def failing_describer(path, original_input, backend):
        raise RuntimeError("vision model unavailable")

    failing_adapter = ImageReaderAdapter(vision_describer=failing_describer)
    failing_result = failing_adapter.execute(success_request)
    failures += check_true("vision failure is honest", failing_result.success is False)
    failures += check_true("vision failure executed True", failing_result.executed is True)
    failures += check_true(
        "vision failure does not pretend success",
        "読めたふりはしません" in failing_result.message,
    )

    return failures


def check_confirmation_flow(tmp_path):
    from core.image_reader_confirmation import (
        build_image_reader_confirmation,
        resolve_image_reader_confirmation_response,
    )

    target_file = _build_fake_png(tmp_path)

    confirmation = build_image_reader_confirmation(f"この画像を見て {target_file}")
    failures = 0
    failures += check_true("confirmation needs_confirmation", confirmation.needs_confirmation is True)
    failures += check_true("confirmation has path", confirmation.path == str(target_file))
    failures += check_true("confirmation tool_name", confirmation.tool_name == "image_reader")

    pending = confirmation.to_dict()
    pending["original_input"] = f"この画像を見て {target_file}"

    confirmed = resolve_image_reader_confirmation_response("いいよ", pending)
    failures += check_true("confirmed status", confirmed.status == "confirmed")
    failures += check_true(
        "confirmed candidate tool_name",
        confirmed.tool_request_candidate["tool_name"] == "image_reader",
    )

    cancelled = resolve_image_reader_confirmation_response("キャンセル", pending)
    failures += check_true("cancelled status", cancelled.status == "cancelled")

    unclear = resolve_image_reader_confirmation_response("よくわからない", pending)
    failures += check_true("unclear status", unclear.status == "unclear")

    no_pending = resolve_image_reader_confirmation_response("いいよ", None)
    failures += check_true("no pending status", no_pending.status == "no_pending")

    return failures


def check_tool_runner_permission(tmp_path):
    from core.tool_adapter import ToolRequest
    from core.tool_execution_log import ToolExecutionLogger
    from core.tool_registry import ToolRegistry
    from core.tool_runner import run_tool_request
    from core.image_reader_adapter import ImageReaderAdapter

    target_file = _build_fake_png(tmp_path)

    registry = ToolRegistry()
    registry.register(ImageReaderAdapter(vision_describer=_fake_vision_describer))
    logger = ToolExecutionLogger()
    request = ToolRequest(
        tool_name="image_reader",
        action="read_image",
        input_data={"path": str(target_file)},
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
    document_in_context = any("IMAGE_TEST_MARKER_ADAPTER" in text for text in system_texts)
    last_user_text = user_texts[-1] if user_texts else ""
    return f"FAKE_LLM_ANSWER|document_in_context={document_in_context}|user={last_user_text}"


def build_lightweight_personal_ai():
    from core.capability_manager import CapabilityManager
    from core.input_analyzer import InputAnalyzer
    from core.personal_ai import PersonalAI
    from core.tool_execution_log import ToolExecutionLogger
    from core.tool_registry import ToolRegistry
    from core.image_reader_adapter import ImageReaderAdapter

    ai = PersonalAI.__new__(PersonalAI)
    ai.input_analyzer = InputAnalyzer()
    ai.capability_manager = CapabilityManager()
    ai.web_reader_fetcher = None
    ai.ask_llm_func = fake_llm_responder
    registry = ToolRegistry()
    registry.register(ImageReaderAdapter(vision_describer=_fake_vision_describer))
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
    ai.pending_image_reader_confirmation = None
    for prefix in [
        "web_reader",
        "file_reader",
        "pdf_reader",
        "word_reader",
        "excel_reader",
        "pptx_reader",
        "youtube_reader",
        "image_reader",
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


def check_personal_ai_flow(tmp_path):
    target_file = _build_fake_png(tmp_path)

    ai_preview = build_lightweight_personal_ai()
    confirmation_response = ai_preview.handle_user_input(f"この画像 {target_file}")
    read_response = ai_preview.handle_user_input("いいよ")
    failures = 0
    failures += check_true(
        "confirmation shown",
        str(target_file) in confirmation_response,
    )
    failures += check_true("reads with Image Reader", "Image Readerで画像を解析しました" in read_response)
    failures += check_true("shows description preview", "テスト用の画像説明" in read_response)
    failures += check_true("pending cleared", ai_preview.pending_image_reader_confirmation is None)
    failures += check_true(
        "last_read_document stored as image_reader",
        ai_preview.last_read_document is not None
        and ai_preview.last_read_document.get("source_tool") == "image_reader",
    )

    ai_summarize = build_lightweight_personal_ai()
    ai_summarize.handle_user_input(f"{target_file} 内容を要約してください")
    summarize_response = ai_summarize.handle_user_input("はい")
    failures += check_true("combined flow calls fake LLM", "FAKE_LLM_ANSWER" in summarize_response)
    failures += check_true(
        "combined flow LLM sees description",
        "document_in_context=True" in summarize_response,
    )

    ai_cancel = build_lightweight_personal_ai()
    ai_cancel.handle_user_input(f"この画像 {target_file}")
    cancel_response = ai_cancel.handle_user_input("キャンセル")
    failures += check_true("cancel not executed", "Image Readerは実行しませんでした" in cancel_response)
    failures += check_true("cancel pending cleared", ai_cancel.pending_image_reader_confirmation is None)

    ai_missing = build_lightweight_personal_ai()
    missing_path = tmp_path / "missing.png"
    ai_missing.handle_user_input(f"この画像 {missing_path}")
    missing_response = ai_missing.handle_user_input("はい")
    failures += check_true(
        "missing file reports not executed",
        "Image Readerは実行されませんでした" in missing_response,
    )

    ai_no_path = build_lightweight_personal_ai()
    no_path_response = ai_no_path.handle_user_input("この画像を見て説明して")
    failures += check_true(
        "no path falls back to capability gate (still honest about being unimplemented for that case)",
        "未実装" in no_path_response,
    )

    return failures


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"
    core = PROJECT_ROOT / "core"

    files = [
        ("image_reader_adapter.py", core / "image_reader_adapter.py"),
        ("image_reader_confirmation.py", core / "image_reader_confirmation.py"),
        ("vision_router.py", core / "vision_router.py"),
        ("confirmation_intent.py", core / "confirmation_intent.py"),
        ("personal_ai.py", core / "personal_ai.py"),
        ("check_ver2470.py", scripts / "check_ver2470.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_imports()
    failures += check_path_extraction()
    failures += check_vision_router_defaults_to_local()

    import tempfile

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        failures += check_image_reader_adapter(tmp_path)
        failures += check_confirmation_flow(tmp_path)
        failures += check_tool_runner_permission(tmp_path)
        failures += check_personal_ai_flow(tmp_path)

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
            "check_ver2470.py",
        ],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        [
            "## Version 2.47",
            "Image Reader",
            "scripts/check_ver2470.py",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        [
            "現在バージョン:",
            "Ver2.47:",
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
