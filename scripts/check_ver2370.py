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
    return check_true("check_ver2370 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2370.py").read_text(encoding="utf-8")
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
        print(f"[NG] check_ver2370 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2370 has no forbidden words")
    return 0


def check_imports():
    try:
        from core.excel_reader_adapter import ExcelReaderAdapter, extract_excel_path_from_text
        from core.excel_reader_confirmation import (
            build_excel_reader_confirmation,
            resolve_excel_reader_confirmation_response,
        )
        from core.confirmation_intent import resolve_confirmation_intent
        from core.personal_ai import PersonalAI
        from core.tool_adapter import ToolRequest, ToolResult
        from core.tool_runner import run_tool_request
    except Exception as error:
        print(f"[NG] imports failed -> {error}")
        return 1

    ExcelReaderAdapter
    extract_excel_path_from_text
    build_excel_reader_confirmation
    resolve_excel_reader_confirmation_response
    resolve_confirmation_intent
    PersonalAI
    ToolRequest
    ToolResult
    run_tool_request

    print("[OK] imports")
    return 0


def check_path_extraction():
    from core.excel_reader_adapter import extract_excel_path_from_text

    failures = 0
    failures += check_true(
        "bare xlsx path detected",
        extract_excel_path_from_text("このExcelファイルを読んで docs/report.xlsx")
        == "docs/report.xlsx",
    )
    failures += check_true(
        "space-containing windows path detected",
        extract_excel_path_from_text(r"C:\Users\me\Downloads\excel_report (1).xlsx")
        == r"C:\Users\me\Downloads\excel_report (1).xlsx",
    )
    failures += check_true(
        "no path returns None",
        extract_excel_path_from_text("このExcelファイルを読んで") is None,
    )
    failures += check_true(
        "non xlsx extension is ignored",
        extract_excel_path_from_text("note.txt を読んで") is None,
    )

    return failures


def _build_xlsx(tmp_path, cell_values, sheet_name="Sheet1"):
    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = sheet_name

    for row_index, row in enumerate(cell_values, start=1):
        for col_index, value in enumerate(row, start=1):
            sheet.cell(row=row_index, column=col_index, value=value)

    path = tmp_path / "note.xlsx"
    workbook.save(str(path))
    return path


def check_excel_reader_adapter(tmp_path):
    from core.excel_reader_adapter import ExcelReaderAdapter
    from core.tool_adapter import ToolRequest, ToolResult

    good_file = _build_xlsx(
        tmp_path,
        [
            ["Item", "Price"],
            ["Excel Readerの動作確認用テキストです。", 980],
        ],
    )

    adapter = ExcelReaderAdapter()
    failures = 0

    success_request = ToolRequest(
        tool_name="excel_reader",
        action="read_excel",
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
        success_result.data.get("file_name") == "note.xlsx",
    )
    failures += check_true(
        "success result has text preview",
        "動作確認" in success_result.data.get("text_preview", ""),
    )
    failures += check_true(
        "success result has sheet_count",
        success_result.data.get("sheet_count") == 1,
    )

    missing_request = ToolRequest(
        tool_name="excel_reader",
        action="read_excel",
        input_data={"path": str(tmp_path / "does_not_exist.xlsx")},
        requires_permission=True,
        risk_level="medium",
    )
    missing_result = adapter.execute(missing_request)
    failures += check_true("missing file fails", missing_result.success is False)
    failures += check_true("missing file not executed", missing_result.executed is False)

    wrong_extension_request = ToolRequest(
        tool_name="excel_reader",
        action="read_excel",
        input_data={"path": str(tmp_path / "note.txt")},
        requires_permission=True,
        risk_level="medium",
    )
    wrong_extension_result = adapter.execute(wrong_extension_request)
    failures += check_true("wrong extension fails", wrong_extension_result.success is False)
    failures += check_true("wrong extension not executed", wrong_extension_result.executed is False)

    corrupt_file = tmp_path / "corrupt.xlsx"
    corrupt_file.write_bytes(b"not a real xlsx file")
    corrupt_request = ToolRequest(
        tool_name="excel_reader",
        action="read_excel",
        input_data={"path": str(corrupt_file)},
        requires_permission=True,
        risk_level="medium",
    )
    corrupt_result = adapter.execute(corrupt_request)
    failures += check_true("corrupt xlsx fails honestly", corrupt_result.success is False)
    failures += check_true("corrupt xlsx executed True", corrupt_result.executed is True)

    return failures


def check_confirmation_flow(tmp_path):
    from core.excel_reader_confirmation import (
        build_excel_reader_confirmation,
        resolve_excel_reader_confirmation_response,
    )

    target_file = _build_xlsx(tmp_path, [["確認フローのテスト本文です。"]])

    confirmation = build_excel_reader_confirmation(f"このExcelファイルを読んで {target_file}")
    failures = 0
    failures += check_true("confirmation needs_confirmation", confirmation.needs_confirmation is True)
    failures += check_true("confirmation has path", confirmation.path == str(target_file))
    failures += check_true("confirmation tool_name", confirmation.tool_name == "excel_reader")

    pending = confirmation.to_dict()
    pending["original_input"] = f"このExcelファイルを読んで {target_file}"

    confirmed = resolve_excel_reader_confirmation_response("いいよ", pending)
    failures += check_true("confirmed status", confirmed.status == "confirmed")
    failures += check_true(
        "confirmed candidate tool_name",
        confirmed.tool_request_candidate["tool_name"] == "excel_reader",
    )

    cancelled = resolve_excel_reader_confirmation_response("キャンセル", pending)
    failures += check_true("cancelled status", cancelled.status == "cancelled")

    unclear = resolve_excel_reader_confirmation_response("よくわからない", pending)
    failures += check_true("unclear status", unclear.status == "unclear")

    no_pending = resolve_excel_reader_confirmation_response("いいよ", None)
    failures += check_true("no pending status", no_pending.status == "no_pending")

    return failures


def check_tool_runner_permission(tmp_path):
    from core.tool_adapter import ToolRequest
    from core.tool_execution_log import ToolExecutionLogger
    from core.tool_registry import ToolRegistry
    from core.tool_runner import run_tool_request
    from core.excel_reader_adapter import ExcelReaderAdapter

    target_file = _build_xlsx(tmp_path, [["Permission経由の実行確認です。"]])

    registry = ToolRegistry()
    registry.register(ExcelReaderAdapter())
    logger = ToolExecutionLogger()
    request = ToolRequest(
        tool_name="excel_reader",
        action="read_excel",
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
    document_in_context = any("EXCEL_FAKE_MARKER" in text for text in system_texts)
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
    ai.pending_word_reader_confirmation = None
    ai.pending_excel_reader_confirmation = None
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
    ai.last_word_reader_confirmation = None
    ai.last_word_reader_confirmation_result = None
    ai.last_word_reader_tool_request_candidate = None
    ai.last_word_reader_tool_run_result = None
    ai.last_word_reader_tool_result = None
    ai.last_excel_reader_confirmation = None
    ai.last_excel_reader_confirmation_result = None
    ai.last_excel_reader_tool_request_candidate = None
    ai.last_excel_reader_tool_run_result = None
    ai.last_excel_reader_tool_result = None
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
    # ファイル名に"excel"を含めて、文書作成判定との衝突がないことも合わせて確認します。
    target_file = _build_xlsx(tmp_path, [["EXCEL_FAKE_MARKERを含む本文です。結合テストです。"]])
    excel_named_file = target_file.rename(tmp_path / "excel_report (1).xlsx")

    failures = 0

    ai_confirm = build_lightweight_personal_ai()
    confirmation_response = ai_confirm.handle_user_input(f"このExcelファイルを読んで {excel_named_file}")
    read_response = ai_confirm.handle_user_input("いいよ")
    failures += check_true(
        "confirmation shown for space+excel-containing filename",
        str(excel_named_file) in confirmation_response,
    )
    failures += check_true("reads with Excel Reader", "Excel Readerで読み取りました" in read_response)
    failures += check_true("shows file content", "結合テスト" in read_response)
    failures += check_true("pending cleared", ai_confirm.pending_excel_reader_confirmation is None)
    failures += check_true(
        "last_read_document stored as excel_reader",
        ai_confirm.last_read_document is not None
        and ai_confirm.last_read_document.get("source_tool") == "excel_reader",
    )

    ai_summarize = build_lightweight_personal_ai()
    ai_summarize.handle_user_input(f"{excel_named_file} 内容を要約してください")
    summarize_response = ai_summarize.handle_user_input("はい")
    failures += check_true("combined flow calls fake LLM", "FAKE_LLM_ANSWER" in summarize_response)
    failures += check_true(
        "combined flow LLM sees document despite 'excel' in filename",
        "document_in_context=True" in summarize_response,
    )

    ai_cancel = build_lightweight_personal_ai()
    ai_cancel.handle_user_input(f"このExcelファイルを読んで {excel_named_file}")
    cancel_response = ai_cancel.handle_user_input("キャンセル")
    failures += check_true("cancel not executed", "Excel Readerは実行しませんでした" in cancel_response)
    failures += check_true("cancel pending cleared", ai_cancel.pending_excel_reader_confirmation is None)

    ai_missing = build_lightweight_personal_ai()
    missing_path = tmp_path / "missing.xlsx"
    ai_missing.handle_user_input(f"このExcelファイルを読んで {missing_path}")
    missing_response = ai_missing.handle_user_input("はい")
    failures += check_true(
        "missing file reports not executed",
        "Excel Readerは実行されませんでした" in missing_response,
    )

    return failures


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"
    core = PROJECT_ROOT / "core"

    files = [
        ("excel_reader_adapter.py", core / "excel_reader_adapter.py"),
        ("excel_reader_confirmation.py", core / "excel_reader_confirmation.py"),
        ("confirmation_intent.py", core / "confirmation_intent.py"),
        ("personal_ai.py", core / "personal_ai.py"),
        ("check_ver2370.py", scripts / "check_ver2370.py"),
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
        failures += check_excel_reader_adapter(tmp_path)
        failures += check_confirmation_flow(tmp_path)
        failures += check_tool_runner_permission(tmp_path)
        failures += check_personal_ai_flow(tmp_path)

    failures += check_words(
        "requirements.txt",
        PROJECT_ROOT / "requirements.txt",
        [
            "openpyxl",
        ],
    )

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
            "check_ver2370.py",
        ],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        [
            "## Version 2.37",
            "Excel Reader",
            "scripts/check_ver2370.py",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        [
            "現在バージョン:",
            "Ver2.37: Excel Reader最小実装",
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
