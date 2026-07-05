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
    return check_true("check_ver2420 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2420.py").read_text(encoding="utf-8")
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
        print(f"[NG] check_ver2420 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2420 has no forbidden words")
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


MULTI_STORE_ROWS = [
    [1001, "池袋店", "抹茶ガトーショコラ", 760, 4],
    [1002, "新宿店", "抹茶ガトーショコラ", 760, 4],
    [1003, "渋谷店", "抹茶ガトーショコラ", 1080, 5],
    [1004, "池袋店", "厚切りベーコンサンド", 1080, 3],
    [1005, "新宿店", "黒糖ミルクラテ", 600, 5],
    [1006, "渋谷店", "抹茶ガトーショコラ", 760, 4],
    [1007, "渋谷店", "厚切りベーコンサンド", 1080, 4],
]


def check_group_by_accuracy(tmp_path):
    from core.excel_reader_adapter import ExcelReaderAdapter
    from core.tool_adapter import ToolRequest

    target_file = _build_xlsx(
        tmp_path,
        ["注文ID", "店舗", "商品名", "売上", "満足度"],
        MULTI_STORE_ROWS,
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
    failures += check_true("group-by section present", "グループ集計" in text)
    failures += check_true(
        "correct max store by sales (渋谷店=2920)",
        "最大は「渋谷店」で2920" in text,
    )
    failures += check_true(
        "correct min store by sales (新宿店=1360)",
        "最小は「新宿店」で1360" in text,
    )
    failures += check_true(
        "id-like unique column excluded from group-by (no 注文ID aggregation)",
        "ごとの「注文ID」合計" not in text,
    )
    failures += check_true(
        "group-by section appears before raw row dump",
        text.index("グループ集計") < text.index("[Sheet1]\n注文ID"),
    )

    return failures


def check_no_group_by_when_no_category_column(tmp_path):
    from core.excel_reader_adapter import ExcelReaderAdapter
    from core.tool_adapter import ToolRequest

    # 各行の店舗名がすべて異なる（=繰り返しがない）ため、意味のあるグループ化ができない。
    target_file = _build_xlsx(
        tmp_path,
        ["注文ID", "店舗", "売上"],
        [
            [1, "店A", 100],
            [2, "店B", 200],
            [3, "店C", 300],
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

    return check_true(
        "no group-by section when every category value is unique",
        "グループ集計" not in text,
    )


def fake_llm_responder(messages):
    system_texts = [message["content"] for message in messages if message["role"] == "system"]
    group_by_visible = any(
        "グループ集計" in text and "最大は「渋谷店」で2920" in text for text in system_texts
    )
    return f"FAKE_LLM_ANSWER|group_by_visible={group_by_visible}"


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
    ai.last_pptx_reader_confirmation = None
    ai.last_pptx_reader_confirmation_result = None
    ai.last_pptx_reader_tool_request_candidate = None
    ai.last_pptx_reader_tool_run_result = None
    ai.last_pptx_reader_tool_result = None
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


def check_group_by_survives_into_followup_turn(tmp_path):
    target_file = _build_xlsx(
        tmp_path,
        ["注文ID", "店舗", "商品名", "売上", "満足度"],
        MULTI_STORE_ROWS,
    )

    ai = build_lightweight_personal_ai()
    ai.handle_user_input(f"{target_file} を読んで")
    ai.handle_user_input("はい")

    messages = ai.build_messages()
    group_by_in_context = any(
        "グループ集計" in message["content"] and "最大は「渋谷店」で2920" in message["content"]
        for message in messages
        if message["role"] == "system"
    )

    return check_true(
        "correct group-by values available for follow-up questions",
        group_by_in_context,
    )


def check_combined_summarize_sees_group_by(tmp_path):
    target_file = _build_xlsx(
        tmp_path,
        ["注文ID", "店舗", "商品名", "売上", "満足度"],
        MULTI_STORE_ROWS,
    )

    ai = build_lightweight_personal_ai()
    ai.handle_user_input(f"{target_file} 内容を要約して")
    response = ai.handle_user_input("はい")

    return check_true(
        "combined summarize call receives correct group-by aggregate",
        "group_by_visible=True" in response,
    )


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"
    core = PROJECT_ROOT / "core"

    files = [
        ("excel_reader_adapter.py", core / "excel_reader_adapter.py"),
        ("check_ver2420.py", scripts / "check_ver2420.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        failures += check_group_by_accuracy(tmp_path)
        failures += check_no_group_by_when_no_category_column(tmp_path)
        failures += check_group_by_survives_into_followup_turn(tmp_path)
        failures += check_combined_summarize_sees_group_by(tmp_path)

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
            "check_ver2420.py",
        ],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        [
            "## Version 2.42",
            "グループ集計",
            "scripts/check_ver2420.py",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        [
            "現在バージョン:",
            "Ver2.42: Excel Readerにグループ集計を追加",
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
