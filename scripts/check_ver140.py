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


def check_contains(label, text, expected):
    if expected in text:
        print(f"[OK] {label}")
        return 0

    print(f"[NG] {label} -> missing: {expected}")
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
    print("[OK] imports")
    return 0


def check_tool_request_and_result():
    from core.tool_adapter import ToolRequest, ToolResult

    request = ToolRequest(
        tool_name="web_reader",
        action="read",
        input_data={"url": "https://example.com"},
        requires_permission=True,
        risk_level="medium",
    )
    result = ToolResult(
        success=False,
        message="not executed",
        data=None,
        error="test_error",
        executed=False,
    )

    failures = 0
    failures += check_true("ToolRequest can be created", request.tool_name == "web_reader")
    failures += check_true("ToolResult can be created", result.message == "not executed")
    failures += check_true("ToolResult executed False", result.executed is False)
    failures += check_true("ToolResult success False", result.success is False)

    return failures


def check_unimplemented_adapter():
    from core.tool_adapter import ToolRequest, ToolResult, UnimplementedToolAdapter

    adapter = UnimplementedToolAdapter(
        name="web_reader",
        description="test web reader",
    )
    request = ToolRequest(
        tool_name="web_reader",
        action="read",
        input_data={"url": "https://example.com"},
    )
    result = adapter.execute(request)

    failures = 0
    failures += check_true("Unimplemented is unavailable", adapter.is_available() is False)
    failures += check_true("execute returns ToolResult", isinstance(result, ToolResult))
    failures += check_true("unimplemented success False", result.success is False)
    failures += check_true("unimplemented executed False", result.executed is False)
    failures += check_true(
        "unimplemented message",
        "未実装" in result.message or "unimplemented" in result.message.lower(),
    )

    return failures


def check_tool_registry():
    from core.tool_adapter import ToolAdapter, UnimplementedToolAdapter
    from core.tool_registry import ToolRegistry

    registry = ToolRegistry(register_default_tools=False)
    unknown_adapter = registry.get("missing_tool")

    class DummyAvailableAdapter(ToolAdapter):
        def is_available(self):
            return True

    dummy_adapter = DummyAvailableAdapter(
        name="dummy_tool",
        description="test adapter",
    )
    registry.register(dummy_adapter)

    failures = 0
    failures += check_true("ToolRegistry can be created", isinstance(registry, ToolRegistry))
    failures += check_true(
        "unknown tool returns unimplemented",
        isinstance(unknown_adapter, UnimplementedToolAdapter),
    )
    failures += check_true("unknown is unavailable", registry.is_available("missing_tool") is False)
    failures += check_true("registered adapter available", registry.is_available("dummy_tool") is True)
    failures += check_true("list_tools works", "dummy_tool" in registry.list_tools())

    default_registry = ToolRegistry()
    failures += check_true("default web_reader registered", "web_reader" in default_registry.list_tools())
    failures += check_true("default web_reader unavailable", default_registry.is_available("web_reader") is False)

    return failures


def main():
    failures = 0

    tool_adapter = PROJECT_ROOT / "core" / "tool_adapter.py"
    tool_registry = PROJECT_ROOT / "core" / "tool_registry.py"
    check_ver140 = PROJECT_ROOT / "scripts" / "check_ver140.py"
    run_ver1_checks = PROJECT_ROOT / "scripts" / "run_ver1_checks.py"
    changelog = PROJECT_ROOT / "docs" / "changelog.md"
    project_handoff = PROJECT_ROOT / "docs" / "project_handoff.md"
    tool_adapter_design = PROJECT_ROOT / "docs" / "tool_adapter_design.md"

    failures += check_file_exists("tool_adapter.py", tool_adapter)
    failures += check_file_exists("tool_registry.py", tool_registry)
    failures += check_file_exists("check_ver140.py", check_ver140)
    failures += check_file_exists("run_ver1_checks.py", run_ver1_checks)
    failures += check_file_exists("changelog.md", changelog)
    failures += check_file_exists("project_handoff.md", project_handoff)

    failures += check_imports()
    failures += check_tool_request_and_result()
    failures += check_unimplemented_adapter()
    failures += check_tool_registry()

    failures += check_words(
        "run_ver1_checks.py",
        run_ver1_checks,
        [
            "check_ver140.py",
            "check_ver130.py",
            "check_ver120.py",
            "check_ver110.py",
            "All Ver1 checks passed",
        ],
    )

    failures += check_words(
        "tool_adapter_design.md",
        tool_adapter_design,
        [
            "ToolRequest",
            "ToolResult",
            "ToolAdapter",
            "ToolRegistry",
            "未実装",
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
