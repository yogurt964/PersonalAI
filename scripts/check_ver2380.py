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
    return check_true("check_ver2380 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2380.py").read_text(encoding="utf-8")
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
        print(f"[NG] check_ver2380 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2380 has no forbidden words")
    return 0


def _build_xlsx(tmp_path, header, rows, sheet_name="Sheet1"):
    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = sheet_name
    sheet.append(header)

    for row in rows:
        sheet.append(row)

    path = tmp_path / "sales.xlsx"
    workbook.save(str(path))
    return path


def check_numeric_aggregation_accuracy(tmp_path):
    from core.excel_reader_adapter import ExcelReaderAdapter
    from core.tool_adapter import ToolRequest

    target_file = _build_xlsx(
        tmp_path,
        ["注文ID", "店舗", "商品名", "売上", "満足度"],
        [
            [1001, "池袋店", "抹茶ガトーショコラ", 760, 4],
            [1002, "新宿店", "抹茶ガトーショコラ", 760, 4],
            [1003, "渋谷店", "抹茶ガトーショコラ", 1080, 5],
            [1004, "池袋店", "厚切りベーコンサンド", 1080, 3],
            [1005, "新宿店", "黒糖ミルクラテ", 600, 5],
        ],
    )

    adapter = ExcelReaderAdapter()
    request = ToolRequest(
        tool_name="excel_reader",
        action="read_excel",
        input_data={"path": str(target_file)},
        requires_permission=True,
        risk_level="medium",
    )
    result = adapter.execute(request)
    text = result.data.get("text", "")

    failures = 0
    failures += check_true("read succeeded", result.success is True)
    failures += check_true("summary section present", "自動集計" in text)
    failures += check_true("correct total sales computed", "合計=4280" in text)
    failures += check_true("correct average satisfaction computed", "平均=4.20" in text)
    failures += check_true(
        "summary appears before raw row dump (survives truncation)",
        text.index("自動集計") < text.index("[Sheet1]\n注文ID"),
    )
    failures += check_true(
        "non-numeric column (store name) is not falsely summarized",
        "列「店舗」" not in text,
    )

    return failures


def check_no_summary_for_non_numeric_sheet(tmp_path):
    from core.excel_reader_adapter import ExcelReaderAdapter
    from core.tool_adapter import ToolRequest

    target_file = _build_xlsx(
        tmp_path,
        ["メモ"],
        [["これはテキストだけのシートです。"]],
        sheet_name="Notes",
    )

    adapter = ExcelReaderAdapter()
    request = ToolRequest(
        tool_name="excel_reader",
        action="read_excel",
        input_data={"path": str(target_file)},
        requires_permission=True,
        risk_level="medium",
    )
    result = adapter.execute(request)
    text = result.data.get("text", "")

    return check_true(
        "no summary section when there are no numeric columns",
        "自動集計" not in text,
    )


def fake_llm_responder(messages):
    system_texts = [message["content"] for message in messages if message["role"] == "system"]
    aggregate_visible = any("自動集計" in text and "合計=4280" in text for text in system_texts)
    return f"FAKE_LLM_ANSWER|aggregate_visible={aggregate_visible}"


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


def check_aggregate_survives_into_followup_turn(tmp_path):
    target_file = _build_xlsx(
        tmp_path,
        ["注文ID", "店舗", "商品名", "売上", "満足度"],
        [
            [1001, "池袋店", "抹茶ガトーショコラ", 760, 4],
            [1002, "新宿店", "抹茶ガトーショコラ", 760, 4],
            [1003, "渋谷店", "抹茶ガトーショコラ", 1080, 5],
            [1004, "池袋店", "厚切りベーコンサンド", 1080, 3],
            [1005, "新宿店", "黒糖ミルクラテ", 600, 5],
        ],
    )

    ai = build_lightweight_personal_ai()
    ai.handle_user_input(f"{target_file} を読んで")
    ai.handle_user_input("はい")

    messages = ai.build_messages()
    aggregate_in_context = any(
        "自動集計" in message["content"] and "合計=4280" in message["content"]
        for message in messages
        if message["role"] == "system"
    )

    return check_true(
        "correct aggregate values available for follow-up questions",
        aggregate_in_context,
    )


def check_combined_summarize_sees_aggregate(tmp_path):
    target_file = _build_xlsx(
        tmp_path,
        ["注文ID", "店舗", "商品名", "売上", "満足度"],
        [
            [1001, "池袋店", "抹茶ガトーショコラ", 760, 4],
            [1002, "新宿店", "抹茶ガトーショコラ", 760, 4],
            [1003, "渋谷店", "抹茶ガトーショコラ", 1080, 5],
            [1004, "池袋店", "厚切りベーコンサンド", 1080, 3],
            [1005, "新宿店", "黒糖ミルクラテ", 600, 5],
        ],
    )

    ai = build_lightweight_personal_ai()
    ai.handle_user_input(f"{target_file} 内容を要約して")
    response = ai.handle_user_input("はい")

    return check_true(
        "combined summarize call receives correct aggregate",
        "aggregate_visible=True" in response,
    )


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"
    core = PROJECT_ROOT / "core"

    files = [
        ("excel_reader_adapter.py", core / "excel_reader_adapter.py"),
        ("check_ver2380.py", scripts / "check_ver2380.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        failures += check_numeric_aggregation_accuracy(tmp_path)
        failures += check_no_summary_for_non_numeric_sheet(tmp_path)
        failures += check_aggregate_survives_into_followup_turn(tmp_path)
        failures += check_combined_summarize_sees_aggregate(tmp_path)

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
            "check_ver2380.py",
        ],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        [
            "## Version 2.38",
            "自動集計",
            "scripts/check_ver2380.py",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        [
            "現在バージョン:",
            "Ver2.38: Excel Readerに数値列の自動集計を追加",
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
