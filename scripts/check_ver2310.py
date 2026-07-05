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
    return check_true("check_ver2310 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2310.py").read_text(encoding="utf-8")
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
        print(f"[NG] check_ver2310 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2310 has no forbidden words")
    return 0


def fake_llm_responder(messages):
    system_texts = [message["content"] for message in messages if message["role"] == "system"]
    user_texts = [message["content"] for message in messages if message["role"] == "user"]
    document_in_context = any("FAKE_MARKER" in text for text in system_texts)
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


def check_combined_read_and_summarize(tmp_path):
    target_file = tmp_path / "note.txt"
    target_file.write_text("FAKE_MARKERを含む本文です。" * 5, encoding="utf-8")

    ai = build_lightweight_personal_ai()
    ai.handle_user_input(f"{target_file} を読んで要約してください")
    response = ai.handle_user_input("はい")

    failures = 0
    failures += check_true("combined flow reads first", "File Readerで読み取りました" in response)
    failures += check_true("combined flow calls fake LLM", "FAKE_LLM_ANSWER" in response)
    failures += check_true("combined flow LLM sees document", "document_in_context=True" in response)
    failures += check_true(
        "combined flow does not show generic preview label",
        "本文プレビュー:" not in response,
    )
    failures += check_true(
        "last_read_document stored",
        ai.last_read_document is not None and ai.last_read_document.get("source_tool") == "file_reader",
    )

    return failures


def check_plain_read_keeps_preview(tmp_path):
    target_file = tmp_path / "plain.txt"
    target_file.write_text("FAKE_MARKERを含む本文です。", encoding="utf-8")

    ai = build_lightweight_personal_ai()
    ai.handle_user_input(f"{target_file} を読んで")
    response = ai.handle_user_input("はい")

    failures = 0
    failures += check_true("plain read shows preview label", "本文プレビュー:" in response)
    failures += check_true("plain read does not call fake LLM", "FAKE_LLM_ANSWER" not in response)
    failures += check_true(
        "last_read_document still stored for plain read",
        ai.last_read_document is not None,
    )

    return failures


def check_follow_up_question_uses_document_context(tmp_path):
    target_file = tmp_path / "followup.txt"
    target_file.write_text("FAKE_MARKERを含む本文です。", encoding="utf-8")

    ai = build_lightweight_personal_ai()
    ai.handle_user_input(f"{target_file} を読んで")
    ai.handle_user_input("はい")

    messages = ai.build_messages()

    failures = 0
    failures += check_true(
        "build_messages includes last read document context",
        any(
            "FAKE_MARKER" in message["content"]
            for message in messages
            if message["role"] == "system"
        ),
    )

    return failures


def check_no_document_context_when_nothing_read():
    ai = build_lightweight_personal_ai()
    messages = ai.build_messages()

    return check_true(
        "no document context before any read",
        ai.build_last_read_document_context() is None
        and all("直近" not in message["content"] or "読み取った資料" not in message["content"] for message in messages if message["role"] == "system"),
    )


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"
    core = PROJECT_ROOT / "core"

    files = [
        ("personal_ai.py", core / "personal_ai.py"),
        ("check_ver2310.py", scripts / "check_ver2310.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        failures += check_combined_read_and_summarize(tmp_path)
        failures += check_plain_read_keeps_preview(tmp_path)
        failures += check_follow_up_question_uses_document_context(tmp_path)

    failures += check_no_document_context_when_nothing_read()

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
            "check_ver2310.py",
        ],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        [
            "## Version 2.31",
            "last_read_document",
            "scripts/check_ver2310.py",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        [
            "現在バージョン:",
            "Ver2.31: Reader結果をQwenでの応答に接続",
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
