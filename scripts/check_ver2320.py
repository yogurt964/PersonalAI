import sys
import tempfile
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
    return check_true("check_ver2320 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2320.py").read_text(encoding="utf-8")
    forbidden_words = [
        "req" + "uests",
        "url" + "lib",
        "url" + "open",
        "ask_" + "llm(",
        "Base.metadata." + "create_all",
        "create_" + "database(",
        "reset --" + "hard",
        "force " + "push",
        "re" + "base",
    ]
    found_words = [word for word in forbidden_words if word in source]

    if found_words:
        print(f"[NG] check_ver2320 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2320 has no forbidden words")
    return 0


def check_imports():
    try:
        from core.pdf_reader_adapter import PDFReaderAdapter, extract_pdf_path_from_text
        from core.pdf_reader_confirmation import (
            build_pdf_reader_confirmation,
            resolve_pdf_reader_confirmation_response,
        )
        from core.confirmation_intent import resolve_confirmation_intent
        from core.personal_ai import PersonalAI
        from core.tool_adapter import ToolRequest, ToolResult
        from core.tool_runner import run_tool_request
    except Exception as error:
        print(f"[NG] imports failed -> {error}")
        return 1

    PDFReaderAdapter
    extract_pdf_path_from_text
    build_pdf_reader_confirmation
    resolve_pdf_reader_confirmation_response
    resolve_confirmation_intent
    PersonalAI
    ToolRequest
    ToolResult
    run_tool_request

    print("[OK] imports")
    return 0


def check_path_extraction():
    from core.pdf_reader_adapter import extract_pdf_path_from_text

    failures = 0
    failures += check_true(
        "bare pdf path detected",
        extract_pdf_path_from_text("このPDFを読んで docs/report.pdf") == "docs/report.pdf",
    )
    failures += check_true(
        "quoted path with spaces detected",
        extract_pdf_path_from_text('"My Reports/annual report.pdf" を読んで')
        == "My Reports/annual report.pdf",
    )
    failures += check_true(
        "no path returns None",
        extract_pdf_path_from_text("このPDFを読んで") is None,
    )
    failures += check_true(
        "non pdf extension is ignored",
        extract_pdf_path_from_text("note.txt を読んで") is None,
    )

    return failures


class _FakePage:
    def __init__(self, text):
        self._text = text

    def extract_text(self):
        return self._text


class _FakePdfReader:
    def __init__(self, pages_text):
        self.pages = [_FakePage(text) for text in pages_text]


def _fake_reader_factory(pages_text):
    def factory(_path):
        return _FakePdfReader(pages_text)

    return factory


def check_pdf_reader_adapter(tmp_path):
    from core.pdf_reader_adapter import PDFReaderAdapter
    from core.tool_adapter import ToolRequest, ToolResult

    good_file = tmp_path / "note.pdf"
    good_file.write_bytes(b"%PDF-1.4 fake bytes for size checks only")

    adapter = PDFReaderAdapter(
        max_file_bytes=1024,
        pdf_reader_factory=_fake_reader_factory(["PDF Readerの動作確認用テキストです。"]),
    )
    failures = 0

    success_request = ToolRequest(
        tool_name="pdf_reader",
        action="read_pdf",
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
        success_result.data.get("file_name") == "note.pdf",
    )
    failures += check_true(
        "success result has text preview",
        "動作確認" in success_result.data.get("text_preview", ""),
    )
    failures += check_true(
        "success result has page_count",
        success_result.data.get("page_count") == 1,
    )

    missing_request = ToolRequest(
        tool_name="pdf_reader",
        action="read_pdf",
        input_data={"path": str(tmp_path / "does_not_exist.pdf")},
        requires_permission=True,
        risk_level="medium",
    )
    missing_result = adapter.execute(missing_request)
    failures += check_true("missing file fails", missing_result.success is False)
    failures += check_true("missing file not executed", missing_result.executed is False)

    wrong_extension_request = ToolRequest(
        tool_name="pdf_reader",
        action="read_pdf",
        input_data={"path": str(tmp_path / "note.txt")},
        requires_permission=True,
        risk_level="medium",
    )
    wrong_extension_result = adapter.execute(wrong_extension_request)
    failures += check_true("wrong extension fails", wrong_extension_result.success is False)
    failures += check_true("wrong extension not executed", wrong_extension_result.executed is False)

    empty_text_adapter = PDFReaderAdapter(
        pdf_reader_factory=_fake_reader_factory(["", ""]),
    )
    empty_result = empty_text_adapter.execute(success_request)
    failures += check_true("scanned/empty pdf fails honestly", empty_result.success is False)
    failures += check_true("scanned/empty pdf executed True", empty_result.executed is True)
    failures += check_true("scanned/empty pdf error is empty_text", empty_result.error == "empty_text")

    large_file = tmp_path / "large.pdf"
    large_file.write_bytes(b"%PDF-1.4 " + b"a" * 2000)
    large_request = ToolRequest(
        tool_name="pdf_reader",
        action="read_pdf",
        input_data={"path": str(large_file)},
        requires_permission=True,
        risk_level="medium",
    )
    large_result = adapter.execute(large_request)
    failures += check_true("too large file fails", large_result.success is False)
    failures += check_true("too large file not executed", large_result.executed is False)

    return failures


def check_confirmation_flow(tmp_path):
    from core.pdf_reader_confirmation import (
        build_pdf_reader_confirmation,
        resolve_pdf_reader_confirmation_response,
    )

    target_file = tmp_path / "memo.pdf"
    target_file.write_bytes(b"%PDF-1.4 fake")

    confirmation = build_pdf_reader_confirmation(f"このPDFを読んで {target_file}")
    failures = 0
    failures += check_true("confirmation needs_confirmation", confirmation.needs_confirmation is True)
    failures += check_true("confirmation has path", confirmation.path == str(target_file))
    failures += check_true("confirmation tool_name", confirmation.tool_name == "pdf_reader")

    pending = confirmation.to_dict()
    pending["original_input"] = f"このPDFを読んで {target_file}"

    confirmed = resolve_pdf_reader_confirmation_response("いいよ", pending)
    failures += check_true("confirmed status", confirmed.status == "confirmed")
    failures += check_true(
        "confirmed candidate tool_name",
        confirmed.tool_request_candidate["tool_name"] == "pdf_reader",
    )

    cancelled = resolve_pdf_reader_confirmation_response("キャンセル", pending)
    failures += check_true("cancelled status", cancelled.status == "cancelled")

    unclear = resolve_pdf_reader_confirmation_response("よくわからない", pending)
    failures += check_true("unclear status", unclear.status == "unclear")

    no_pending = resolve_pdf_reader_confirmation_response("いいよ", None)
    failures += check_true("no pending status", no_pending.status == "no_pending")

    return failures


def check_tool_runner_permission(tmp_path):
    from core.tool_adapter import ToolRequest
    from core.tool_execution_log import ToolExecutionLogger
    from core.tool_registry import ToolRegistry
    from core.tool_runner import run_tool_request
    from core.pdf_reader_adapter import PDFReaderAdapter

    target_file = tmp_path / "permission.pdf"
    target_file.write_bytes(b"%PDF-1.4 fake")

    registry = ToolRegistry()
    registry.register(
        PDFReaderAdapter(pdf_reader_factory=_fake_reader_factory(["Permission経由の実行確認です。"]))
    )
    logger = ToolExecutionLogger()
    request = ToolRequest(
        tool_name="pdf_reader",
        action="read_pdf",
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
    document_in_context = any("PDF_FAKE_MARKER" in text for text in system_texts)
    last_user_text = user_texts[-1] if user_texts else ""
    return f"FAKE_LLM_ANSWER|document_in_context={document_in_context}|user={last_user_text}"


def build_lightweight_personal_ai():
    from core.capability_manager import CapabilityManager
    from core.input_analyzer import InputAnalyzer
    from core.personal_ai import PersonalAI
    from core.tool_execution_log import ToolExecutionLogger

    ai = PersonalAI.__new__(PersonalAI)
    ai.input_analyzer = InputAnalyzer()
    ai.capability_manager = CapabilityManager()
    ai.web_reader_fetcher = None
    ai.ask_llm_func = fake_llm_responder
    ai.tool_registry = ai.build_tool_registry(None)
    ai.tool_execution_logger = ToolExecutionLogger()
    ai.pending_preference_confirmation = None
    ai.pending_memory_candidate_confirmation = None
    ai.pending_memory_candidate_edit = None
    ai.pending_web_reader_confirmation = None
    ai.pending_file_reader_confirmation = None
    ai.pending_pdf_reader_confirmation = None
    ai.last_web_reader_confirmation = None
    ai.last_web_reader_confirmation_result = None
    ai.last_web_reader_tool_request_candidate = None
    ai.last_web_reader_tool_run_result = None
    ai.last_web_reader_tool_result = None
    ai.last_file_reader_confirmation = None
    ai.last_file_reader_confirmation_result = None
    ai.last_file_reader_tool_request_candidate = None
    ai.last_file_reader_tool_run_result = None
    ai.last_file_reader_tool_result = None
    ai.last_pdf_reader_confirmation = None
    ai.last_pdf_reader_confirmation_result = None
    ai.last_pdf_reader_tool_request_candidate = None
    ai.last_pdf_reader_tool_run_result = None
    ai.last_pdf_reader_tool_result = None
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


def check_personal_ai_flow(tmp_path, monkeypatch_pdf_reader):
    target_file = tmp_path / "chat.pdf"
    target_file.write_bytes(b"%PDF-1.4 fake")

    failures = 0

    ai_confirm = build_lightweight_personal_ai()
    monkeypatch_pdf_reader(ai_confirm, ["PDF_FAKE_MARKERを含む本文です。結合テストです。"])
    ai_confirm.handle_user_input(f"このPDFを読んで {target_file}")
    read_response = ai_confirm.handle_user_input("はい")
    failures += check_true("reads with PDF Reader", "PDF Readerで読み取りました" in read_response)
    failures += check_true("shows file content", "結合テスト" in read_response)
    failures += check_true("pending cleared", ai_confirm.pending_pdf_reader_confirmation is None)
    failures += check_true(
        "last_read_document stored as pdf_reader",
        ai_confirm.last_read_document is not None
        and ai_confirm.last_read_document.get("source_tool") == "pdf_reader",
    )

    ai_summarize = build_lightweight_personal_ai()
    monkeypatch_pdf_reader(ai_summarize, ["PDF_FAKE_MARKERを含む本文です。"])
    ai_summarize.handle_user_input(f"このPDFを読んで要約してください {target_file}")
    summarize_response = ai_summarize.handle_user_input("はい")
    failures += check_true("combined flow calls fake LLM", "FAKE_LLM_ANSWER" in summarize_response)
    failures += check_true(
        "combined flow LLM sees document",
        "document_in_context=True" in summarize_response,
    )

    ai_cancel = build_lightweight_personal_ai()
    monkeypatch_pdf_reader(ai_cancel, ["PDF_FAKE_MARKERを含む本文です。"])
    ai_cancel.handle_user_input(f"このPDFを読んで {target_file}")
    cancel_response = ai_cancel.handle_user_input("キャンセル")
    failures += check_true("cancel not executed", "PDF Readerは実行しませんでした" in cancel_response)
    failures += check_true("cancel pending cleared", ai_cancel.pending_pdf_reader_confirmation is None)

    ai_missing = build_lightweight_personal_ai()
    missing_path = tmp_path / "missing.pdf"
    ai_missing.handle_user_input(f"このPDFを読んで {missing_path}")
    missing_response = ai_missing.handle_user_input("はい")
    failures += check_true(
        "missing file reports not executed",
        "PDF Readerは実行されませんでした" in missing_response,
    )

    return failures


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"
    core = PROJECT_ROOT / "core"

    files = [
        ("pdf_reader_adapter.py", core / "pdf_reader_adapter.py"),
        ("pdf_reader_confirmation.py", core / "pdf_reader_confirmation.py"),
        ("confirmation_intent.py", core / "confirmation_intent.py"),
        ("personal_ai.py", core / "personal_ai.py"),
        ("check_ver2320.py", scripts / "check_ver2320.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("requirements.txt", PROJECT_ROOT / "requirements.txt"),
        ("changelog.md", docs / "changelog.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_imports()
    failures += check_path_extraction()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        failures += check_pdf_reader_adapter(tmp_path)
        failures += check_confirmation_flow(tmp_path)
        failures += check_tool_runner_permission(tmp_path)

        def monkeypatch_pdf_reader(ai_instance, pages_text):
            from core.pdf_reader_adapter import PDFReaderAdapter

            registry = ai_instance.tool_registry
            registry.register(
                PDFReaderAdapter(pdf_reader_factory=_fake_reader_factory(pages_text))
            )

        failures += check_personal_ai_flow(tmp_path, monkeypatch_pdf_reader)

    failures += check_words(
        "requirements.txt",
        PROJECT_ROOT / "requirements.txt",
        [
            "pypdf",
        ],
    )

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
            "check_ver2320.py",
        ],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        [
            "## Version 2.32",
            "PDF Reader",
            "scripts/check_ver2320.py",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        [
            "現在バージョン:",
            "Ver2.32: PDF Reader最小実装",
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
