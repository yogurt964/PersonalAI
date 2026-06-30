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


def check_imports():
    try:
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

    print("[OK] imports")
    return 0


def check_dry_run():
    from core.tool_request_builder import build_tool_request_decision

    web = build_tool_request_decision("このURLを読んでください https://example.com")
    youtube = build_tool_request_decision("このYouTube動画を要約してください https://youtu.be/example")

    failures = 0
    failures += check_true("URL requires Tool", web.requires_tool is True)
    failures += check_true("URL -> web_reader", web.tool_request.tool_name == "web_reader")
    failures += check_true("URL should_execute False", web.should_execute is False)
    failures += check_true("YouTube -> youtube_reader", youtube.tool_request.tool_name == "youtube_reader")
    failures += check_true("YouTube should_execute False", youtube.should_execute is False)

    return failures


def main():
    failures = 0

    reader_plan = PROJECT_ROOT / "docs" / "reader_implementation_plan_v2.md"
    check_ver190 = PROJECT_ROOT / "scripts" / "check_ver190.py"
    run_ver1_checks = PROJECT_ROOT / "scripts" / "run_ver1_checks.py"
    changelog = PROJECT_ROOT / "docs" / "changelog.md"
    project_handoff = PROJECT_ROOT / "docs" / "project_handoff.md"

    failures += check_file_exists("reader_implementation_plan_v2.md", reader_plan)
    failures += check_file_exists("check_ver190.py", check_ver190)
    failures += check_file_exists("run_ver1_checks.py", run_ver1_checks)
    failures += check_file_exists("changelog.md", changelog)
    failures += check_file_exists("project_handoff.md", project_handoff)

    failures += check_imports()

    failures += check_words(
        "reader_implementation_plan_v2.md",
        reader_plan,
        [
            "Ver1.9",
            "Ver2.0",
            "Reader",
            "Web Reader",
            "PDF Reader",
            "Image Reader",
            "YouTube Reader",
            "File Reader",
            "ToolRequest",
            "ToolResult",
            "ToolExecutionLog",
            "Permission",
            "risk_level",
            "requires_permission",
            "実行したふりをしない",
            "未実装",
            "できること",
            "できないこと",
            "Ver1.10",
            "Ver2.x",
        ],
    )

    failures += check_words(
        "Ver2.0 conditions",
        reader_plan,
        [
            "少なくとも1つのReaderが実際に動く",
            "Permission確認を通る",
            "ToolResultを返す",
            "ToolExecutionLogに記録する",
            "未実装Readerは未実装と返す",
        ],
    )

    failures += check_words(
        "Reader implementation order",
        reader_plan,
        [
            "最初の候補は Web Reader",
            "PDF Reader は段階的に追加",
            "Image Reader は段階的に追加",
            "YouTube Reader は段階的に追加",
        ],
    )

    failures += check_dry_run()

    failures += check_words(
        "run_ver1_checks.py",
        run_ver1_checks,
        [
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

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
