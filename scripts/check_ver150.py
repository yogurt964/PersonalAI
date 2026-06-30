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
        from core.tool_adapter import (
            ToolAdapter,
            ToolRequest,
            ToolResult,
            UnimplementedToolAdapter,
        )
        from core.tool_permission import (
            ToolPermissionDecision,
            build_permission_message,
            evaluate_tool_permission,
        )
        from core.tool_registry import ToolRegistry
    except Exception as error:
        print(f"[NG] imports failed -> {error}")
        return 1

    PersonalAI
    CapabilityManager
    ToolRequest
    ToolResult
    ToolAdapter
    UnimplementedToolAdapter
    ToolRegistry
    ToolPermissionDecision
    evaluate_tool_permission
    build_permission_message

    try:
        from core.permission_manager import PermissionManager

        PermissionManager
        print("[OK] optional PermissionManager import")
    except Exception:
        print("[OK] optional PermissionManager import skipped")

    print("[OK] imports")
    return 0


def check_permission_decision():
    from core.tool_permission import ToolPermissionDecision

    decision = ToolPermissionDecision(
        allowed=False,
        needs_user_confirmation=True,
        risk_level="high",
        reason="test decision",
        executed=False,
    )

    failures = 0
    failures += check_true("ToolPermissionDecision can be created", decision.reason == "test decision")
    failures += check_true("allowed can be False", decision.allowed is False)
    failures += check_true("needs_user_confirmation can be True", decision.needs_user_confirmation is True)
    failures += check_true("executed remains False", decision.executed is False)

    return failures


def check_evaluate_tool_permission():
    from core.tool_adapter import ToolRequest
    from core.tool_permission import evaluate_tool_permission

    medium_request = ToolRequest(
        tool_name="web_reader",
        action="read",
        input_data={},
        requires_permission=True,
        risk_level="medium",
    )
    medium_decision = evaluate_tool_permission(medium_request)

    low_request = ToolRequest(
        tool_name="internal_check",
        action="check",
        input_data={},
        requires_permission=False,
        risk_level="low",
    )
    low_decision = evaluate_tool_permission(low_request)

    critical_request = ToolRequest(
        tool_name="pc_operator",
        action="delete_file",
        input_data={},
        requires_permission=True,
        risk_level="critical",
    )
    critical_decision = evaluate_tool_permission(critical_request)

    unknown_request = ToolRequest(
        tool_name="unknown",
        action="unknown",
        input_data={},
        requires_permission=False,
        risk_level="unknown",
    )
    unknown_decision = evaluate_tool_permission(unknown_request)

    failures = 0
    failures += check_true("medium needs confirmation", medium_decision.needs_user_confirmation is True)
    failures += check_true("medium executed False", medium_decision.executed is False)
    failures += check_true("low allowed", low_decision.allowed is True)
    failures += check_true("low does not need confirmation", low_decision.needs_user_confirmation is False)
    failures += check_true("low executed False", low_decision.executed is False)
    failures += check_true("critical needs confirmation", critical_decision.needs_user_confirmation is True)
    failures += check_true("critical executed False", critical_decision.executed is False)
    failures += check_true("critical blocked", critical_decision.allowed is False)
    failures += check_true("unknown needs confirmation", unknown_decision.needs_user_confirmation is True)
    failures += check_true("unknown executed False", unknown_decision.executed is False)

    return failures


def check_permission_message():
    from core.tool_adapter import ToolRequest
    from core.tool_permission import build_permission_message, evaluate_tool_permission

    request = ToolRequest(
        tool_name="web_reader",
        action="read",
        input_data={"url": "https://example.com"},
        requires_permission=True,
        risk_level="medium",
    )
    decision = evaluate_tool_permission(request)
    message = build_permission_message(decision, request)

    failures = 0
    failures += check_true("message has tool_name", "web_reader" in message)
    failures += check_true("message has action", "read" in message)
    failures += check_true("message has risk_level", "medium" in message)
    failures += check_true("message has confirmation", "確認" in message)
    failures += check_true("message says not executed without permission", "未許可なら実行しない" in message)

    return failures


def main():
    failures = 0

    tool_permission = PROJECT_ROOT / "core" / "tool_permission.py"
    tool_adapter = PROJECT_ROOT / "core" / "tool_adapter.py"
    tool_registry = PROJECT_ROOT / "core" / "tool_registry.py"
    check_ver150 = PROJECT_ROOT / "scripts" / "check_ver150.py"
    run_ver1_checks = PROJECT_ROOT / "scripts" / "run_ver1_checks.py"
    tool_permission_design = PROJECT_ROOT / "docs" / "tool_permission_design.md"
    changelog = PROJECT_ROOT / "docs" / "changelog.md"
    project_handoff = PROJECT_ROOT / "docs" / "project_handoff.md"

    failures += check_file_exists("tool_permission.py", tool_permission)
    failures += check_file_exists("tool_adapter.py", tool_adapter)
    failures += check_file_exists("tool_registry.py", tool_registry)
    failures += check_file_exists("check_ver150.py", check_ver150)
    failures += check_file_exists("run_ver1_checks.py", run_ver1_checks)
    failures += check_file_exists("tool_permission_design.md", tool_permission_design)
    failures += check_file_exists("changelog.md", changelog)
    failures += check_file_exists("project_handoff.md", project_handoff)

    failures += check_imports()
    failures += check_permission_decision()
    failures += check_evaluate_tool_permission()
    failures += check_permission_message()

    failures += check_words(
        "run_ver1_checks.py",
        run_ver1_checks,
        [
            "check_ver150.py",
            "check_ver140.py",
            "check_ver130.py",
            "check_ver120.py",
            "check_ver110.py",
            "All Ver1 checks passed",
        ],
    )

    failures += check_words(
        "tool_permission_design.md",
        tool_permission_design,
        [
            "ToolPermissionDecision",
            "evaluate_tool_permission",
            "build_permission_message",
            "PermissionManager",
            "risk_level",
            "requires_permission",
            "未許可ならToolを実行しない",
            "実行したふりをしない",
            "Reader",
            "Adapter",
        ],
    )

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
