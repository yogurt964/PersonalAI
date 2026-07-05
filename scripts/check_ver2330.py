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
    return check_true("check_ver2330 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2330.py").read_text(encoding="utf-8")
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
        print(f"[NG] check_ver2330 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2330 has no forbidden words")
    return 0


def check_imports():
    try:
        from core.file_path_extraction import extract_single_file_path_from_text
        from core.file_reader_adapter import extract_file_path_from_text
        from core.pdf_reader_adapter import extract_pdf_path_from_text
        from core.confirmation_intent import resolve_confirmation_intent
    except Exception as error:
        print(f"[NG] imports failed -> {error}")
        return 1

    extract_single_file_path_from_text
    extract_file_path_from_text
    extract_pdf_path_from_text
    resolve_confirmation_intent

    print("[OK] imports")
    return 0


def check_space_containing_windows_paths():
    from core.file_reader_adapter import extract_file_path_from_text
    from core.pdf_reader_adapter import extract_pdf_path_from_text

    failures = 0

    txt_case = r"これです。C:\Users\KEYza\Downloads\curry_shop_reading_test (1).txt"
    failures += check_true(
        "space-containing windows txt path extracted in full",
        extract_file_path_from_text(txt_case)
        == r"C:\Users\KEYza\Downloads\curry_shop_reading_test (1).txt",
    )

    pdf_case = r"C:\Users\KEYza\Downloads\pdf_reading_test_curry_shop (2).pdf 内容を要約して"
    failures += check_true(
        "space-containing windows pdf path extracted in full",
        extract_pdf_path_from_text(pdf_case)
        == r"C:\Users\KEYza\Downloads\pdf_reading_test_curry_shop (2).pdf",
    )

    failures += check_true(
        "txt extractor does not pick up pdf-suffixed windows path",
        extract_file_path_from_text(pdf_case) is None,
    )
    failures += check_true(
        "pdf extractor does not pick up txt-suffixed windows path",
        extract_pdf_path_from_text(txt_case) is None,
    )

    return failures


def check_existing_path_styles_unaffected():
    from core.file_reader_adapter import extract_file_path_from_text
    from core.pdf_reader_adapter import extract_pdf_path_from_text

    failures = 0
    failures += check_true(
        "quoted path with spaces still works",
        extract_file_path_from_text('"My Notes/memo file.txt" を読んで')
        == "My Notes/memo file.txt",
    )
    failures += check_true(
        "simple no-space relative path still works",
        extract_file_path_from_text("notes/memo.txt を読んで") == "notes/memo.txt",
    )
    failures += check_true(
        "simple no-space pdf path still works",
        extract_pdf_path_from_text("report.pdf を読んで") == "report.pdf",
    )
    failures += check_true(
        "no path returns None",
        extract_file_path_from_text("このファイルを読んで") is None,
    )

    return failures


def check_yes_word_added():
    from core.confirmation_intent import resolve_confirmation_intent

    result = resolve_confirmation_intent("イエス", context_type="web_reader")

    return check_true(
        "イエス recognized as confirmed",
        result["status"] == "confirmed",
    )


def build_lightweight_personal_ai():
    from core.capability_manager import CapabilityManager
    from core.input_analyzer import InputAnalyzer
    from core.personal_ai import PersonalAI
    from core.tool_execution_log import ToolExecutionLogger

    ai = PersonalAI.__new__(PersonalAI)
    ai.input_analyzer = InputAnalyzer()
    ai.capability_manager = CapabilityManager()
    ai.web_reader_fetcher = None
    ai.ask_llm_func = None
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


def check_personal_ai_bug_reproduction(tmp_path):
    target_file = tmp_path / "curry_shop_reading_test (1).txt"
    target_file.write_text("スペースを含むファイル名のテストです。", encoding="utf-8")

    ai = build_lightweight_personal_ai()
    confirmation_response = ai.handle_user_input(f"これです。{target_file}")
    read_response = ai.handle_user_input("はい")

    failures = 0
    failures += check_true(
        "confirmation message shows the full path",
        str(target_file) in confirmation_response,
    )
    failures += check_true(
        "read succeeds with full path",
        "File Readerで読み取りました" in read_response,
    )
    failures += check_true(
        "read shows real file content",
        "スペースを含む" in read_response,
    )

    return failures


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"
    core = PROJECT_ROOT / "core"

    files = [
        ("file_path_extraction.py", core / "file_path_extraction.py"),
        ("file_reader_adapter.py", core / "file_reader_adapter.py"),
        ("pdf_reader_adapter.py", core / "pdf_reader_adapter.py"),
        ("confirmation_intent.py", core / "confirmation_intent.py"),
        ("check_ver2330.py", scripts / "check_ver2330.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_imports()
    failures += check_space_containing_windows_paths()
    failures += check_existing_path_styles_unaffected()
    failures += check_yes_word_added()

    with tempfile.TemporaryDirectory() as tmp_dir:
        failures += check_personal_ai_bug_reproduction(Path(tmp_dir))

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
            "check_ver2330.py",
        ],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        [
            "## Version 2.33",
            "file_path_extraction",
            "scripts/check_ver2330.py",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        [
            "現在バージョン:",
            "Ver2.33: ファイルパス抽出のスペース対応バグ修正",
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
