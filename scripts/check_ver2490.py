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
    return check_true("check_ver2490 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2490.py").read_text(encoding="utf-8")
    forbidden_words = [
        "req" + "uests.get",
        "req" + "uests.post",
        "ask_" + "llm(",
        "reset --" + "hard",
        "force " + "push",
        "re" + "base",
    ]
    found_words = [word for word in forbidden_words if word in source]

    if found_words:
        print(f"[NG] check_ver2490 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2490 has no forbidden words")
    return 0


def check_multi_path_extraction():
    from core.file_path_extraction import extract_multiple_file_paths_from_text

    exts = (".txt", ".csv")
    failures = 0

    failures += check_true(
        "bare multi-path extraction in order",
        extract_multiple_file_paths_from_text("a.txt b.csv c.txt を読んで", exts)
        == ["a.txt", "b.csv", "c.txt"],
    )
    failures += check_true(
        "single path still returns single-item list",
        extract_multiple_file_paths_from_text("a.txt を読んで", exts) == ["a.txt"],
    )
    failures += check_true(
        "duplicate path collapses to one entry",
        extract_multiple_file_paths_from_text("a.txt a.txt を読んで", exts) == ["a.txt"],
    )
    failures += check_true(
        "no path returns empty list",
        extract_multiple_file_paths_from_text("普通の会話です", exts) == [],
    )
    failures += check_true(
        "max_files caps the result",
        extract_multiple_file_paths_from_text("a.txt b.txt c.txt d.txt", exts, max_files=2)
        == ["a.txt", "b.txt"],
    )
    failures += check_true(
        "quoted path with spaces extracted alongside a bare path",
        extract_multiple_file_paths_from_text('"my notes (1).txt" と other.csv を読んで', exts)
        == ["my notes (1).txt", "other.csv"],
    )

    return failures


def check_single_file_confirmation_unchanged():
    from core.file_reader_confirmation import build_file_reader_confirmation

    confirmation = build_file_reader_confirmation("このファイルを読んで note.txt")

    failures = 0
    failures += check_true("single file action is read_file", confirmation.action == "read_file")
    failures += check_true("single file path set", confirmation.path == "note.txt")
    failures += check_true("single file paths list has one entry", confirmation.paths == ["note.txt"])
    failures += check_true(
        "single file message matches the pre-Ver2.49 wording exactly",
        confirmation.message
        == (
            "このファイルをFile Readerで読み取ってもよいですか？\n"
            "note.txt\n\n"
            "ローカルファイルへアクセスするため、実行前に確認が必要です。"
        ),
    )

    return failures


def check_multi_file_confirmation():
    from core.file_reader_confirmation import (
        build_file_reader_confirmation,
        resolve_file_reader_confirmation_response,
    )

    confirmation = build_file_reader_confirmation("note1.txt note2.txt note3.csv を読んで")

    failures = 0
    failures += check_true("multi file needs_confirmation", confirmation.needs_confirmation is True)
    failures += check_true("multi file action is read_files", confirmation.action == "read_files")
    failures += check_true(
        "multi file paths captured in order",
        confirmation.paths == ["note1.txt", "note2.txt", "note3.csv"],
    )
    failures += check_true("multi file message lists all files", all(
        path in confirmation.message for path in confirmation.paths
    ))

    pending = confirmation.to_dict()
    pending["original_input"] = "note1.txt note2.txt note3.csv を読んで"

    confirmed = resolve_file_reader_confirmation_response("いいよ", pending)
    failures += check_true("confirmed status", confirmed.status == "confirmed")
    failures += check_true(
        "confirmed candidate carries all paths",
        confirmed.tool_request_candidate["input_data"]["paths"] == ["note1.txt", "note2.txt", "note3.csv"],
    )
    failures += check_true(
        "confirmed candidate action is read_files",
        confirmed.tool_request_candidate["action"] == "read_files",
    )

    return failures


def fake_llm_responder(messages):
    system_texts = [message["content"] for message in messages if message["role"] == "system"]
    both_markers = any("MARKER_ONE" in text and "MARKER_TWO" in text for text in system_texts)
    return f"FAKE_LLM_ANSWER|both_markers_seen={both_markers}"


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


def check_personal_ai_multi_file_flow(tmp_path):
    path1 = tmp_path / "note1.txt"
    path2 = tmp_path / "note2.txt"
    missing_path = tmp_path / "missing.txt"
    path1.write_text("MARKER_ONEを含む本文です。", encoding="utf-8")
    path2.write_text("MARKER_TWOを含む本文です。", encoding="utf-8")

    failures = 0

    ai_read = build_lightweight_personal_ai()
    confirmation_response = ai_read.handle_user_input(f"{path1} {path2} を読んで")
    read_response = ai_read.handle_user_input("はい")
    failures += check_true(
        "multi-file confirmation lists both files",
        str(path1) in confirmation_response and str(path2) in confirmation_response,
    )
    failures += check_true("multi-file read reports 2 files", "2件のファイルを読み取りました" in read_response)
    failures += check_true(
        "combined preview includes both markers",
        "MARKER_ONE" in read_response and "MARKER_TWO" in read_response,
    )
    failures += check_true("pending cleared", ai_read.pending_file_reader_confirmation is None)
    failures += check_true(
        "last_read_document combines both file names",
        ai_read.last_read_document is not None
        and "note1.txt" in ai_read.last_read_document.get("title", "")
        and "note2.txt" in ai_read.last_read_document.get("title", ""),
    )

    ai_summarize = build_lightweight_personal_ai()
    ai_summarize.handle_user_input(f"{path1} {path2} 内容を要約してください")
    summarize_response = ai_summarize.handle_user_input("はい")
    failures += check_true("combined summarize calls fake LLM", "FAKE_LLM_ANSWER" in summarize_response)
    failures += check_true(
        "combined summarize LLM sees both files' content",
        "both_markers_seen=True" in summarize_response,
    )

    ai_partial = build_lightweight_personal_ai()
    ai_partial.handle_user_input(f"{path1} {missing_path} を読んで")
    partial_response = ai_partial.handle_user_input("はい")
    failures += check_true(
        "partial failure reports 1 succeeded",
        "1件のファイルを読み取りました" in partial_response,
    )
    failures += check_true(
        "partial failure lists the missing file",
        "読み取れなかったファイル" in partial_response and str(missing_path) in partial_response,
    )

    ai_single = build_lightweight_personal_ai()
    single_confirmation = ai_single.handle_user_input(f"{path1} を読んで")
    failures += check_true(
        "single-file confirmation message unchanged",
        single_confirmation
        == (
            "このファイルをFile Readerで読み取ってもよいですか？\n"
            f"{path1}\n\n"
            "ローカルファイルへアクセスするため、実行前に確認が必要です。"
        ),
    )
    single_read_response = ai_single.handle_user_input("はい")
    failures += check_true(
        "single-file read response still uses the pre-Ver2.49 wording",
        "File Readerで読み取りました。" in single_read_response
        and "件のファイルを読み取りました" not in single_read_response,
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
        ("file_reader_confirmation.py", core / "file_reader_confirmation.py"),
        ("personal_ai.py", core / "personal_ai.py"),
        ("check_ver2490.py", scripts / "check_ver2490.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_multi_path_extraction()
    failures += check_single_file_confirmation_unchanged()
    failures += check_multi_file_confirmation()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        failures += check_personal_ai_multi_file_flow(tmp_path)

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
            "check_ver2490.py",
        ],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        [
            "## Version 2.49",
            "scripts/check_ver2490.py",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        [
            "現在バージョン:",
            "Ver2.49:",
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
