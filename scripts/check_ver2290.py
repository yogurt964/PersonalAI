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
    return check_true("check_ver2290 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2290.py").read_text(encoding="utf-8")
    forbidden_words = [
        "req" + "uests",
        "url" + "lib",
        "ask_" + "llm(",
        "Base.metadata." + "create_all",
        "create_" + "database(",
        "reset --" + "hard",
        "force " + "push",
        "re" + "base",
        "shutil.rm" + "tree(str(PROJECT_ROOT",
    ]
    found_words = [word for word in forbidden_words if word in source]

    if found_words:
        print(f"[NG] check_ver2290 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2290 has no forbidden words")
    return 0


def check_imports():
    try:
        from core.file_reader_adapter import FileReaderAdapter, extract_file_path_from_text
        from core.file_reader_confirmation import (
            build_file_reader_confirmation,
            resolve_file_reader_confirmation_response,
        )
        from core.confirmation_intent import resolve_confirmation_intent
        from core.personal_ai import PersonalAI
        from core.tool_adapter import ToolRequest, ToolResult
        from core.tool_runner import run_tool_request
    except Exception as error:
        print(f"[NG] imports failed -> {error}")
        return 1

    FileReaderAdapter
    extract_file_path_from_text
    build_file_reader_confirmation
    resolve_file_reader_confirmation_response
    resolve_confirmation_intent
    PersonalAI
    ToolRequest
    ToolResult
    run_tool_request

    print("[OK] imports")
    return 0


def check_path_extraction():
    from core.file_reader_adapter import extract_file_path_from_text

    failures = 0
    failures += check_true(
        "bare txt path detected",
        extract_file_path_from_text("このファイルを読んで notes/memo.txt") == "notes/memo.txt",
    )
    failures += check_true(
        "bare md path detected",
        extract_file_path_from_text("README.md を読んで") == "README.md",
    )
    failures += check_true(
        "quoted path with spaces detected",
        extract_file_path_from_text('"My Notes/memo file.txt" を読んで')
        == "My Notes/memo file.txt",
    )
    failures += check_true(
        "no path returns None",
        extract_file_path_from_text("このファイルを読んで") is None,
    )
    failures += check_true(
        "unsupported extension is ignored",
        extract_file_path_from_text("report.pdf を読んで") is None,
    )

    return failures


def check_file_reader_adapter(tmp_path):
    from core.file_reader_adapter import FileReaderAdapter
    from core.tool_adapter import ToolRequest, ToolResult

    good_file = tmp_path / "note.txt"
    good_file.write_text("File Readerの動作確認用テキストです。", encoding="utf-8")

    adapter = FileReaderAdapter(max_file_bytes=1024)
    failures = 0

    success_request = ToolRequest(
        tool_name="file_reader",
        action="read_file",
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
        success_result.data.get("file_name") == "note.txt",
    )
    failures += check_true(
        "success result has text preview",
        "動作確認" in success_result.data.get("text_preview", ""),
    )

    missing_request = ToolRequest(
        tool_name="file_reader",
        action="read_file",
        input_data={"path": str(tmp_path / "does_not_exist.txt")},
        requires_permission=True,
        risk_level="medium",
    )
    missing_result = adapter.execute(missing_request)
    failures += check_true("missing file fails", missing_result.success is False)
    failures += check_true("missing file not executed", missing_result.executed is False)
    failures += check_true("missing file message honest", "実行していません" in missing_result.message)

    wrong_extension_request = ToolRequest(
        tool_name="file_reader",
        action="read_file",
        input_data={"path": str(tmp_path / "report.pdf")},
        requires_permission=True,
        risk_level="medium",
    )
    wrong_extension_result = adapter.execute(wrong_extension_request)
    failures += check_true("wrong extension fails", wrong_extension_result.success is False)
    failures += check_true("wrong extension not executed", wrong_extension_result.executed is False)

    directory_request = ToolRequest(
        tool_name="file_reader",
        action="read_file",
        input_data={"path": str(tmp_path)},
        requires_permission=True,
        risk_level="medium",
    )
    directory_result = adapter.execute(directory_request)
    failures += check_true("directory path fails", directory_result.success is False)
    failures += check_true("directory path not executed", directory_result.executed is False)

    large_file = tmp_path / "large.txt"
    large_file.write_text("a" * 2000, encoding="utf-8")
    large_request = ToolRequest(
        tool_name="file_reader",
        action="read_file",
        input_data={"path": str(large_file)},
        requires_permission=True,
        risk_level="medium",
    )
    large_result = adapter.execute(large_request)
    failures += check_true("too large file fails", large_result.success is False)
    failures += check_true("too large file not executed", large_result.executed is False)

    return failures


def check_confirmation_flow(tmp_path):
    from core.file_reader_confirmation import (
        build_file_reader_confirmation,
        resolve_file_reader_confirmation_response,
    )

    target_file = tmp_path / "memo.txt"
    target_file.write_text("確認フローのテスト本文です。", encoding="utf-8")

    confirmation = build_file_reader_confirmation(f"このファイルを読んで {target_file}")
    failures = 0
    failures += check_true("confirmation needs_confirmation", confirmation.needs_confirmation is True)
    failures += check_true("confirmation has path", confirmation.path == str(target_file))
    failures += check_true("confirmation tool_name", confirmation.tool_name == "file_reader")

    pending = confirmation.to_dict()
    pending["original_input"] = f"このファイルを読んで {target_file}"

    confirmed = resolve_file_reader_confirmation_response("いいよ", pending)
    failures += check_true("confirmed status", confirmed.status == "confirmed")
    failures += check_true("confirmed candidate tool_name", confirmed.tool_request_candidate["tool_name"] == "file_reader")
    failures += check_true("confirmed candidate requires_permission", confirmed.tool_request_candidate["requires_permission"] is True)

    cancelled = resolve_file_reader_confirmation_response("キャンセル", pending)
    failures += check_true("cancelled status", cancelled.status == "cancelled")
    failures += check_true("cancelled no candidate", cancelled.tool_request_candidate is None)

    unclear = resolve_file_reader_confirmation_response("よくわからない", pending)
    failures += check_true("unclear status", unclear.status == "unclear")

    no_pending = resolve_file_reader_confirmation_response("いいよ", None)
    failures += check_true("no pending status", no_pending.status == "no_pending")

    return failures


def check_tool_runner_permission(tmp_path):
    from core.tool_adapter import ToolRequest
    from core.tool_execution_log import ToolExecutionLogger
    from core.tool_registry import ToolRegistry
    from core.tool_runner import run_tool_request
    from core.file_reader_adapter import FileReaderAdapter

    target_file = tmp_path / "permission.txt"
    target_file.write_text("Permission経由の実行確認です。", encoding="utf-8")

    registry = ToolRegistry()
    registry.register(FileReaderAdapter())
    logger = ToolExecutionLogger()
    request = ToolRequest(
        tool_name="file_reader",
        action="read_file",
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


def build_lightweight_personal_ai():
    from core.capability_manager import CapabilityManager
    from core.input_analyzer import InputAnalyzer
    from core.personal_ai import PersonalAI
    from core.tool_execution_log import ToolExecutionLogger

    ai = PersonalAI.__new__(PersonalAI)
    ai.input_analyzer = InputAnalyzer()
    ai.capability_manager = CapabilityManager()
    ai.web_reader_fetcher = None
    ai.tool_registry = ai.build_tool_registry(None)
    ai.tool_execution_logger = ToolExecutionLogger()
    ai.pending_preference_confirmation = None
    ai.pending_memory_candidate_confirmation = None
    ai.pending_memory_candidate_edit = None
    ai.pending_web_reader_confirmation = None
    ai.pending_file_reader_confirmation = None
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
    ai.last_tool_execution_record = None
    ai.last_memory_candidate = None
    ai.last_memory_candidate_confirmation_result = None
    ai.last_memory_candidate_save_result = None
    ai.last_saved_memory_candidate_result = None
    ai.last_input_analysis = None
    ai.last_response = None
    ai.save_user_message = lambda _message: None
    ai.save_assistant_message = lambda _message: None
    return ai


def check_personal_ai_flow(tmp_path):
    target_file = tmp_path / "chat.txt"
    target_file.write_text("PersonalAI経由のFile Reader結合テストです。", encoding="utf-8")

    failures = 0

    ai_confirm = build_lightweight_personal_ai()
    confirmation_response = ai_confirm.handle_user_input(f"このファイルを読んで {target_file}")
    read_response = ai_confirm.handle_user_input("いいよ")
    failures += check_true(
        "confirmation shown",
        "File Readerで読み取ってもよいですか" in confirmation_response,
    )
    failures += check_true("reads with File Reader", "File Readerで読み取りました" in read_response)
    failures += check_true("shows file content", "結合テスト" in read_response)
    failures += check_true("pending cleared", ai_confirm.pending_file_reader_confirmation is None)

    ai_cancel = build_lightweight_personal_ai()
    ai_cancel.handle_user_input(f"このファイルを読んで {target_file}")
    cancel_response = ai_cancel.handle_user_input("キャンセル")
    failures += check_true("cancel not executed", "File Readerは実行しませんでした" in cancel_response)
    failures += check_true("cancel pending cleared", ai_cancel.pending_file_reader_confirmation is None)

    ai_missing = build_lightweight_personal_ai()
    missing_path = tmp_path / "missing.txt"
    ai_missing.handle_user_input(f"このファイルを読んで {missing_path}")
    missing_response = ai_missing.handle_user_input("はい")
    failures += check_true(
        "missing file reports not executed",
        "File Readerは実行されませんでした" in missing_response,
    )

    ai_unsupported = build_lightweight_personal_ai()
    unsupported_response = ai_unsupported.handle_user_input("このファイルを読んで video.mp4")
    failures += check_true(
        "unsupported extension falls back to capability gate",
        "未実装" in unsupported_response,
    )
    failures += check_true(
        "unsupported extension creates no pending",
        ai_unsupported.pending_file_reader_confirmation is None,
    )

    return failures


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"
    core = PROJECT_ROOT / "core"

    files = [
        ("file_reader_adapter.py", core / "file_reader_adapter.py"),
        ("file_reader_confirmation.py", core / "file_reader_confirmation.py"),
        ("confirmation_intent.py", core / "confirmation_intent.py"),
        ("personal_ai.py", core / "personal_ai.py"),
        ("check_ver2290.py", scripts / "check_ver2290.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_imports()
    failures += check_path_extraction()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        failures += check_file_reader_adapter(tmp_path)
        failures += check_confirmation_flow(tmp_path)
        failures += check_tool_runner_permission(tmp_path)
        failures += check_personal_ai_flow(tmp_path)

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
            "check_ver2290.py",
        ],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        [
            "## Version 2.29",
            "File Reader",
            "scripts/check_ver2290.py",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        [
            "現在バージョン:",
            "Ver2.29: File Reader最小実装",
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
