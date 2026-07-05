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
    return check_true("check_ver2340 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2340.py").read_text(encoding="utf-8")
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
        print(f"[NG] check_ver2340 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2340 has no forbidden words")
    return 0


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


def check_context_warns_about_earlier_files():
    ai = build_lightweight_personal_ai()

    ai.remember_last_read_document(
        source_tool="file_reader",
        title="curry_shop_reading_test (1).txt",
        location="C:/x/curry.txt",
        text="テストキーワード: yogurt-test-2026",
    )
    ai.remember_last_read_document(
        source_tool="pdf_reader",
        title="pdf_reading_test_curry_shop.pdf",
        location="C:/x/curry.pdf",
        text="確認キーワード: pdf-curry-test-2026",
    )

    context = ai.build_last_read_document_context()

    failures = 0
    failures += check_true("context is not empty", bool(context))
    failures += check_true(
        "context shows the latest document only",
        "pdf-curry-test-2026" in context and "yogurt-test-2026" not in context,
    )
    failures += check_true(
        "context warns earlier file content is not held",
        "もう保持していません" in context,
    )
    failures += check_true(
        "context instructs not to assert absence in other files",
        "断定しないでください" in context,
    )

    return failures


def check_single_document_context_unaffected():
    ai = build_lightweight_personal_ai()

    ai.remember_last_read_document(
        source_tool="web_reader",
        title="Example Domain",
        location="https://example.com",
        text="Example Domain の本文です。",
    )

    context = ai.build_last_read_document_context()

    failures = 0
    failures += check_true("single document context still works", "Example Domain" in context)
    failures += check_true(
        "single document context still instructs honesty about this document",
        "推測せず" in context,
    )

    return failures


def check_no_context_before_any_read():
    ai = build_lightweight_personal_ai()

    return check_true(
        "no context when nothing has been read",
        ai.build_last_read_document_context() is None,
    )


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"
    core = PROJECT_ROOT / "core"

    files = [
        ("personal_ai.py", core / "personal_ai.py"),
        ("check_ver2340.py", scripts / "check_ver2340.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_context_warns_about_earlier_files()
    failures += check_single_document_context_unaffected()
    failures += check_no_context_before_any_read()

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
            "check_ver2340.py",
        ],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        [
            "## Version 2.34",
            "last_read_document",
            "scripts/check_ver2340.py",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        [
            "現在バージョン:",
            "Ver2.34: last_read_documentの誤解答防止",
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
