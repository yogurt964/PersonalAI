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
        from core.tool_request_builder import build_tool_request_decision
    except Exception as error:
        print(f"[NG] imports failed -> {error}")
        return 1

    PersonalAI
    CapabilityManager
    build_tool_request_decision
    evaluate_tool_permission
    build_tool_execution_record

    print("[OK] imports")
    return 0


def check_tool_request_dry_run():
    from core.tool_request_builder import build_tool_request_decision

    failures = 0

    normal = build_tool_request_decision("こんにちは")
    failures += check_true("normal requires no Tool", normal.requires_tool is False)
    failures += check_true("normal tool_request None", normal.tool_request is None)
    failures += check_true("normal should_execute False", normal.should_execute is False)

    web = build_tool_request_decision("このURLを読んでください https://example.com")
    failures += check_true("URL -> web_reader", web.tool_request.tool_name == "web_reader")
    failures += check_true("URL should_execute False", web.should_execute is False)

    youtube = build_tool_request_decision("このYouTube動画を要約してください https://youtu.be/example")
    failures += check_true("YouTube -> youtube_reader", youtube.tool_request.tool_name == "youtube_reader")
    failures += check_true("YouTube should_execute False", youtube.should_execute is False)

    pdf = build_tool_request_decision("sample.pdf を読んでください")
    failures += check_true("PDF filename -> pdf_reader", pdf.tool_request.tool_name == "pdf_reader")
    failures += check_true("PDF should_execute False", pdf.should_execute is False)

    image = build_tool_request_decision("image.png を解析してください")
    failures += check_true("image filename -> image_reader", image.tool_request.tool_name == "image_reader")
    failures += check_true("image should_execute False", image.should_execute is False)

    document = build_tool_request_decision("Word文書を作ってください")
    failures += check_true("Word -> document_creator", document.tool_request.tool_name == "document_creator")
    failures += check_true("document should_execute False", document.should_execute is False)

    pc = build_tool_request_decision("ファイルを削除してください")
    failures += check_true("delete file -> pc_operator", pc.tool_request.tool_name == "pc_operator")
    failures += check_true("delete risk high or critical", pc.tool_request.risk_level in {"high", "critical"})
    failures += check_true("delete should_execute False", pc.should_execute is False)

    return failures


def check_permission_and_log():
    from core.tool_execution_log import build_tool_execution_record
    from core.tool_permission import evaluate_tool_permission
    from core.tool_request_builder import build_tool_request_decision

    url_decision = build_tool_request_decision("このURLを読んでください https://example.com")
    url_permission = evaluate_tool_permission(url_decision.tool_request)

    pc_decision = build_tool_request_decision("ファイルを削除してください")
    pc_permission = evaluate_tool_permission(pc_decision.tool_request)

    url_record = build_tool_execution_record(
        url_decision.tool_request,
        permission_decision=url_permission,
    )
    pc_record = build_tool_execution_record(
        pc_decision.tool_request,
        permission_decision=pc_permission,
    )

    failures = 0
    failures += check_true("medium needs confirmation", url_permission.needs_user_confirmation is True)
    failures += check_true("medium permission executed False", url_permission.executed is False)
    failures += check_true("pc needs confirmation", pc_permission.needs_user_confirmation is True)
    failures += check_true("pc permission executed False", pc_permission.executed is False)

    failures += check_true("log executed False", url_record.executed is False)
    failures += check_true("log success False", url_record.success is False)
    failures += check_true("log keeps tool_name", url_record.tool_name == "web_reader")
    failures += check_true("log keeps risk_level", url_record.risk_level == "medium")
    failures += check_true("pc log executed False", pc_record.executed is False)
    failures += check_true("pc log risk kept", pc_record.risk_level in {"high", "critical"})

    return failures


def main():
    failures = 0

    reader_tests = PROJECT_ROOT / "docs" / "reader_pre_implementation_test_cases.md"
    check_ver180 = PROJECT_ROOT / "scripts" / "check_ver180.py"
    run_ver1_checks = PROJECT_ROOT / "scripts" / "run_ver1_checks.py"
    changelog = PROJECT_ROOT / "docs" / "changelog.md"
    project_handoff = PROJECT_ROOT / "docs" / "project_handoff.md"

    failures += check_file_exists("reader_pre_implementation_test_cases.md", reader_tests)
    failures += check_file_exists("check_ver180.py", check_ver180)
    failures += check_file_exists("run_ver1_checks.py", run_ver1_checks)
    failures += check_file_exists("changelog.md", changelog)
    failures += check_file_exists("project_handoff.md", project_handoff)

    failures += check_imports()

    failures += check_words(
        "reader_pre_implementation_test_cases.md",
        reader_tests,
        [
            "Ver1.8",
            "Reader実装前",
            "手動テスト",
            "Web",
            "YouTube",
            "PDF",
            "Image",
            "File",
            "Document",
            "PC",
            "ToolRequest",
            "ToolPermission",
            "ToolExecutionLog",
            "should_execute",
            "executed=False",
            "実行しない",
            "実行したふりをしない",
            "未実装",
            "Ver2.0",
        ],
    )

    failures += check_tool_request_dry_run()
    failures += check_permission_and_log()

    failures += check_words(
        "run_ver1_checks.py",
        run_ver1_checks,
        [
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
