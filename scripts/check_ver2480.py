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
    return check_true("check_ver2480 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2480.py").read_text(encoding="utf-8")
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
        print(f"[NG] check_ver2480 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2480 has no forbidden words")
    return 0


def check_new_extensions_extracted():
    from core.file_reader_adapter import extract_file_path_from_text

    failures = 0
    cases = [
        ("このファイルを読んで data.csv", "data.csv"),
        ("このファイルを読んで config.json", "config.json"),
        ("このファイルを読んで app.log", "app.log"),
        ("このファイルを読んで settings.yaml", "settings.yaml"),
        ("このファイルを読んで settings.yml", "settings.yml"),
        ("このファイルを読んで data.xml", "data.xml"),
        ("このファイルを読んで config.ini", "config.ini"),
        ("このファイルを読んで pyproject.toml", "pyproject.toml"),
        ("このファイルを読んで data.tsv", "data.tsv"),
    ]

    for input_text, expected in cases:
        actual = extract_file_path_from_text(input_text)
        failures += check_true(f"extracts {expected}", actual == expected)

    failures += check_true(
        "still rejects unrelated binary extensions (.pdf handled by PDF Reader)",
        extract_file_path_from_text("report.pdf を読んで") is None,
    )

    return failures


def check_extraction_respects_instance_allowed_extensions():
    from core.file_reader_adapter import FileReaderAdapter

    # コンストラクタでextensionsを絞った場合、_get_path_from_requestもそれに従うことを確認する
    # （固定のモジュール定数を見てしまっていたVer2.47以前のバグの再発防止）。
    from core.tool_adapter import ToolRequest

    restricted_adapter = FileReaderAdapter(allowed_extensions=(".txt",))
    request = ToolRequest(
        tool_name="file_reader",
        action="read_file",
        input_data={"original_input": "このファイルを読んで data.csv"},
        requires_permission=True,
        risk_level="medium",
    )
    result = restricted_adapter.execute(request)

    return check_true(
        "instance-level allowed_extensions is honored during path extraction",
        result.error == "missing_path",
    )


def check_file_reader_reads_new_extensions(tmp_path):
    from core.file_reader_adapter import FileReaderAdapter
    from core.tool_adapter import ToolRequest

    csv_path = tmp_path / "data (1).csv"
    csv_path.write_text("name,age\nAlice,30\nBob,25\n", encoding="utf-8")

    json_path = tmp_path / "config.json"
    json_path.write_text('{"key": "value"}', encoding="utf-8")

    adapter = FileReaderAdapter()
    failures = 0

    csv_request = ToolRequest(
        tool_name="file_reader",
        action="read_file",
        input_data={"path": str(csv_path)},
        requires_permission=True,
        risk_level="medium",
    )
    csv_result = adapter.execute(csv_request)
    failures += check_true("csv read succeeds", csv_result.success is True)
    failures += check_true("csv content correct", "Alice,30" in csv_result.data.get("text", ""))

    json_request = ToolRequest(
        tool_name="file_reader",
        action="read_file",
        input_data={"path": str(json_path)},
        requires_permission=True,
        risk_level="medium",
    )
    json_result = adapter.execute(json_request)
    failures += check_true("json read succeeds", json_result.success is True)
    failures += check_true("json content correct", '"key": "value"' in json_result.data.get("text", ""))

    return failures


def check_personal_ai_flow_with_csv(tmp_path):
    from core.capability_manager import CapabilityManager
    from core.input_analyzer import InputAnalyzer
    from core.personal_ai import PersonalAI
    from core.tool_execution_log import ToolExecutionLogger

    csv_path = tmp_path / "sales (1).csv"
    csv_path.write_text("item,price\nPen,100\nNote,200\n", encoding="utf-8")

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

    confirmation_response = ai.handle_user_input(f"このファイルを読んで {csv_path}")
    read_response = ai.handle_user_input("はい")

    failures = 0
    failures += check_true("confirmation shown for csv", str(csv_path) in confirmation_response)
    failures += check_true("reads with File Reader", "File Readerで読み取りました" in read_response)
    failures += check_true("shows csv content", "Pen,100" in read_response)

    return failures


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"
    core = PROJECT_ROOT / "core"

    files = [
        ("file_reader_adapter.py", core / "file_reader_adapter.py"),
        ("check_ver2480.py", scripts / "check_ver2480.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_new_extensions_extracted()
    failures += check_extraction_respects_instance_allowed_extensions()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        failures += check_file_reader_reads_new_extensions(tmp_path)
        failures += check_personal_ai_flow_with_csv(tmp_path)

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
            "check_ver2480.py",
        ],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        [
            "## Version 2.48",
            "scripts/check_ver2480.py",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        [
            "現在バージョン:",
            "Ver2.48:",
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
