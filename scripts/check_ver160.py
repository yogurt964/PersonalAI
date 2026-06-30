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
        from core.input_analyzer import InputAnalyzer
        from core.personal_ai import PersonalAI
        from core.tool_adapter import ToolRequest, ToolResult
        from core.tool_flow import build_tool_flow_preview
        from core.tool_permission import evaluate_tool_permission
        from core.tool_registry import ToolRegistry
        from core.tool_request_builder import (
            ToolRequestDecision,
            build_tool_request_decision,
        )
    except Exception as error:
        print(f"[NG] imports failed -> {error}")
        return 1

    PersonalAI
    CapabilityManager
    InputAnalyzer
    ToolRequest
    ToolResult
    ToolRegistry
    evaluate_tool_permission
    ToolRequestDecision
    build_tool_request_decision
    build_tool_flow_preview

    print("[OK] imports")
    return 0


def analyze_and_build(user_input):
    from core.capability_manager import CapabilityManager
    from core.input_analyzer import InputAnalyzer
    from core.tool_request_builder import build_tool_request_decision

    input_analysis = InputAnalyzer().analyze(user_input)
    capability_result = CapabilityManager().analyze(user_input, input_analysis)

    return build_tool_request_decision(
        user_input,
        input_analysis=input_analysis,
        capability_result=capability_result,
    )


def check_tool_request_decision():
    from core.tool_request_builder import ToolRequestDecision

    decision = ToolRequestDecision(
        requires_tool=False,
        tool_request=None,
        reason="normal conversation",
        should_execute=False,
    )

    failures = 0
    failures += check_true("ToolRequestDecision can be created", decision.reason == "normal conversation")
    failures += check_true("requires_tool False works", decision.requires_tool is False)
    failures += check_true("tool_request None works", decision.tool_request is None)
    failures += check_true("should_execute False works", decision.should_execute is False)

    return failures


def check_build_tool_request_decision():
    failures = 0

    normal = analyze_and_build("こんにちは")
    failures += check_true("normal conversation requires no Tool", normal.requires_tool is False)
    failures += check_true("normal conversation has no ToolRequest", normal.tool_request is None)
    failures += check_true("normal conversation should not execute", normal.should_execute is False)

    web = analyze_and_build("このURLを読んでください https://example.com")
    failures += check_true("URL requires Tool", web.requires_tool is True)
    failures += check_true("URL -> web_reader", web.tool_request.tool_name == "web_reader")
    failures += check_true("URL action read_url", web.tool_request.action == "read_url")
    failures += check_true("URL requires permission", web.tool_request.requires_permission is True)
    failures += check_true("URL risk medium", web.tool_request.risk_level == "medium")
    failures += check_true("URL should not execute", web.should_execute is False)

    youtube = analyze_and_build("このYouTube動画を要約してください https://youtu.be/example")
    failures += check_true("YouTube -> youtube_reader", youtube.tool_request.tool_name == "youtube_reader")
    failures += check_true("YouTube should not execute", youtube.should_execute is False)

    pdf = analyze_and_build("このPDFを読んでください")
    failures += check_true("PDF -> pdf_reader", pdf.tool_request.tool_name == "pdf_reader")
    failures += check_true("PDF should not execute", pdf.should_execute is False)

    image = analyze_and_build("この画像を見てください")
    failures += check_true("image -> image_reader", image.tool_request.tool_name == "image_reader")
    failures += check_true("image should not execute", image.should_execute is False)

    document = analyze_and_build("Word文書を作ってください")
    failures += check_true("document -> document_creator", document.tool_request.tool_name == "document_creator")
    failures += check_true("document should not execute", document.should_execute is False)

    pc = analyze_and_build("PCを操作してファイルを削除してください")
    failures += check_true("PC -> pc_operator", pc.tool_request.tool_name == "pc_operator")
    failures += check_true("PC risk high or critical", pc.tool_request.risk_level in {"high", "critical"})
    failures += check_true("PC requires permission", pc.tool_request.requires_permission is True)
    failures += check_true("PC should not execute", pc.should_execute is False)

    return failures


def check_tool_permission_integration():
    from core.tool_permission import evaluate_tool_permission

    medium_decision = analyze_and_build("このURLを読んでください https://example.com")
    medium_permission = evaluate_tool_permission(medium_decision.tool_request)

    pc_decision = analyze_and_build("PCを操作してファイルを削除してください")
    pc_permission = evaluate_tool_permission(pc_decision.tool_request)

    failures = 0
    failures += check_true("medium permission confirmation", medium_permission.needs_user_confirmation is True)
    failures += check_true("medium permission executed False", medium_permission.executed is False)
    failures += check_true("PC permission confirmation", pc_permission.needs_user_confirmation is True)
    failures += check_true("PC permission executed False", pc_permission.executed is False)

    return failures


def check_tool_registry_integration():
    from core.tool_registry import ToolRegistry

    registry = ToolRegistry()
    decision = analyze_and_build("このURLを読んでください https://example.com")
    adapter = registry.get(decision.tool_request.tool_name)

    failures = 0
    failures += check_true("ToolRegistry returns adapter", adapter is not None)
    failures += check_true("web_reader adapter unavailable", adapter.is_available() is False)
    failures += check_true("ToolRegistry dry-run does not execute", decision.should_execute is False)

    return failures


def check_tool_flow_preview():
    from core.tool_flow import build_tool_flow_preview

    normal_preview = build_tool_flow_preview("こんにちは")
    web_preview = build_tool_flow_preview("このURLを読んでください https://example.com")

    failures = 0
    failures += check_true("flow normal requires no Tool", normal_preview.requires_tool is False)
    failures += check_true("flow normal executed False", normal_preview.executed is False)
    failures += check_true("flow web requires Tool", web_preview.requires_tool is True)
    failures += check_true("flow web tool_name", web_preview.tool_name == "web_reader")
    failures += check_true("flow web permission needed", web_preview.permission_needed is True)
    failures += check_true("flow web adapter unavailable", web_preview.adapter_available is False)
    failures += check_true("flow web should not execute", web_preview.should_execute is False)
    failures += check_true("flow web executed False", web_preview.executed is False)

    return failures


def main():
    failures = 0

    tool_request_builder = PROJECT_ROOT / "core" / "tool_request_builder.py"
    tool_flow = PROJECT_ROOT / "core" / "tool_flow.py"
    check_ver160 = PROJECT_ROOT / "scripts" / "check_ver160.py"
    run_ver1_checks = PROJECT_ROOT / "scripts" / "run_ver1_checks.py"
    tool_input_integration = PROJECT_ROOT / "docs" / "tool_input_integration.md"
    changelog = PROJECT_ROOT / "docs" / "changelog.md"
    project_handoff = PROJECT_ROOT / "docs" / "project_handoff.md"

    failures += check_file_exists("tool_request_builder.py", tool_request_builder)
    failures += check_file_exists("tool_flow.py", tool_flow)
    failures += check_file_exists("check_ver160.py", check_ver160)
    failures += check_file_exists("run_ver1_checks.py", run_ver1_checks)
    failures += check_file_exists("tool_input_integration.md", tool_input_integration)
    failures += check_file_exists("changelog.md", changelog)
    failures += check_file_exists("project_handoff.md", project_handoff)

    failures += check_imports()
    failures += check_tool_request_decision()
    failures += check_build_tool_request_decision()
    failures += check_tool_permission_integration()
    failures += check_tool_registry_integration()
    failures += check_tool_flow_preview()

    failures += check_words(
        "run_ver1_checks.py",
        run_ver1_checks,
        [
            "check_ver160.py",
            "check_ver150.py",
            "check_ver140.py",
            "check_ver130.py",
            "check_ver120.py",
            "check_ver110.py",
            "All Ver1 checks passed",
        ],
    )

    failures += check_words(
        "tool_input_integration.md",
        tool_input_integration,
        [
            "InputAnalyzer",
            "CapabilityManager",
            "ToolRequest",
            "ToolRegistry",
            "ToolPermission",
            "dry-run",
            "実行しない",
            "Reader",
            "Adapter",
            "未実装",
            "実行したふりしない",
        ],
    )

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
