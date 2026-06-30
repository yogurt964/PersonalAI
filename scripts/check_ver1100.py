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


def check_words_in_text(label, text, words):
    missing_words = [word for word in words if word not in text]

    if missing_words:
        print(f"[NG] {label} missing words -> {missing_words}")
        return 1

    print(f"[OK] {label} required words")
    return 0


def check_imports():
    try:
        from ai.conversation_quality_policy import build_conversation_quality_guidance
        from ai.memory_usage_policy import decide_memory_usage
        from core.capability_manager import CapabilityManager
        from core.personal_ai import PersonalAI
        from core.tool_execution_log import build_tool_execution_record
        from core.tool_permission import evaluate_tool_permission
        from core.tool_registry import ToolRegistry
        from core.tool_request_builder import build_tool_request_decision
    except Exception as error:
        print(f"[NG] imports failed -> {error}")
        return 1

    PersonalAI
    CapabilityManager
    ToolRegistry
    build_tool_request_decision
    evaluate_tool_permission
    build_tool_execution_record
    decide_memory_usage
    build_conversation_quality_guidance

    print("[OK] imports")
    return 0


def check_dry_run():
    from core.tool_request_builder import build_tool_request_decision

    normal = build_tool_request_decision("こんにちは")
    web = build_tool_request_decision("このURLを読んでください https://example.com")
    pc = build_tool_request_decision("ファイルを削除してください")

    failures = 0
    failures += check_true("normal requires no Tool", normal.requires_tool is False)
    failures += check_true("normal should_execute False", normal.should_execute is False)
    failures += check_true("URL requires Tool", web.requires_tool is True)
    failures += check_true("URL -> web_reader", web.tool_request.tool_name == "web_reader")
    failures += check_true("URL should_execute False", web.should_execute is False)
    failures += check_true("delete file -> pc_operator", pc.tool_request.tool_name == "pc_operator")
    failures += check_true("delete risk high or critical", pc.tool_request.risk_level in ["high", "critical"])
    failures += check_true("delete should_execute False", pc.should_execute is False)

    return failures


def main():
    failures = 0

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"

    final_review = docs / "ver1_x_final_review.md"
    reader_plan = docs / "reader_implementation_plan_v2.md"
    reader_tests = docs / "reader_pre_implementation_test_cases.md"
    tool_input = docs / "tool_input_integration.md"
    tool_log = docs / "tool_execution_log_design.md"
    tool_permission = docs / "tool_permission_design.md"
    tool_adapter = docs / "tool_adapter_design.md"
    conversation_quality = docs / "conversation_quality.md"
    check_workflow = docs / "check_workflow.md"
    check_ver1100 = scripts / "check_ver1100.py"
    run_ver1_checks = scripts / "run_ver1_checks.py"
    changelog = docs / "changelog.md"
    project_handoff = docs / "project_handoff.md"

    files = [
        ("ver1_x_final_review.md", final_review),
        ("reader_implementation_plan_v2.md", reader_plan),
        ("reader_pre_implementation_test_cases.md", reader_tests),
        ("tool_input_integration.md", tool_input),
        ("tool_execution_log_design.md", tool_log),
        ("tool_permission_design.md", tool_permission),
        ("tool_adapter_design.md", tool_adapter),
        ("conversation_quality.md", conversation_quality),
        ("check_workflow.md", check_workflow),
        ("check_ver1100.py", check_ver1100),
        ("run_ver1_checks.py", run_ver1_checks),
        ("changelog.md", changelog),
        ("project_handoff.md", project_handoff),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_imports()

    failures += check_words(
        "ver1_x_final_review.md",
        final_review,
        [
            "Ver1.10",
            "Ver1.x",
            "Ver2.0",
            "総仕上げ",
            "Memory利用バランス",
            "会話品質",
            "Tool / Adapter",
            "Permission",
            "ToolRequest",
            "ToolExecutionLog",
            "Reader",
            "Web Reader",
            "実行したふりをしない",
            "未実装",
            "できること",
            "できないこと",
            "data/personal_ai.db",
            "Ver2.0準備",
        ],
    )

    failures += check_words(
        "Ver1.x list",
        final_review,
        [
            "Ver1.1",
            "Ver1.2",
            "Ver1.3",
            "Ver1.4",
            "Ver1.5",
            "Ver1.6",
            "Ver1.7",
            "Ver1.8",
            "Ver1.9",
        ],
    )

    combined_reader_text = ""
    for path in [final_review, reader_plan]:
        if path.exists():
            combined_reader_text += path.read_text(encoding="utf-8")

    failures += check_words_in_text(
        "Ver2.0 readiness",
        combined_reader_text,
        [
            "Web Readerを最初の実装候補",
            "少なくとも1つのReaderが実際に動く",
            "Permission確認を通す",
            "ToolResultを返す",
            "ToolExecutionLogに記録する",
            "未実装Readerは未実装と返す",
        ],
    )

    failures += check_words(
        "run_ver1_checks.py",
        run_ver1_checks,
        [
            "check_ver1100.py",
            "check_ver190.py",
            "check_ver180.py",
            "check_ver170.py",
            "check_ver160.py",
            "check_ver150.py",
            "check_ver140.py",
            "check_ver130.py",
            "check_ver120.py",
            "check_ver110.py",
            "All Ver1 checks passed",
        ],
    )

    failures += check_dry_run()

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
