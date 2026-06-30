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
        from core.tool_adapter import ToolRequest, ToolResult
        from core.tool_execution_log import (
            ToolExecutionLogger,
            ToolExecutionRecord,
            build_tool_execution_record,
        )
        from core.tool_permission import evaluate_tool_permission
    except Exception as error:
        print(f"[NG] imports failed -> {error}")
        return 1

    PersonalAI
    CapabilityManager
    ToolRequest
    ToolResult
    evaluate_tool_permission
    ToolExecutionRecord
    ToolExecutionLogger
    build_tool_execution_record

    print("[OK] imports")
    return 0


def check_tool_execution_record():
    from core.tool_execution_log import ToolExecutionRecord

    record = ToolExecutionRecord(
        tool_name="web_reader",
        action="read_url",
        risk_level="medium",
        executed=False,
        success=False,
        message="未実行: test",
    )

    failures = 0
    failures += check_true("ToolExecutionRecord can be created", bool(record.record_id))
    failures += check_true("record keeps tool_name", record.tool_name == "web_reader")
    failures += check_true("record keeps action", record.action == "read_url")
    failures += check_true("record keeps risk_level", record.risk_level == "medium")
    failures += check_true("record keeps executed False", record.executed is False)
    failures += check_true("record keeps success False", record.success is False)
    failures += check_true("record has created_at", bool(record.created_at))

    return failures


def check_build_tool_execution_record():
    from core.tool_adapter import ToolRequest, ToolResult
    from core.tool_execution_log import build_tool_execution_record
    from core.tool_permission import evaluate_tool_permission

    request = ToolRequest(
        tool_name="web_reader",
        action="read_url",
        input_data={"original_input": "このURLを読んで"},
        requires_permission=True,
        risk_level="medium",
    )
    permission_decision = evaluate_tool_permission(request)

    dry_run_record = build_tool_execution_record(
        request,
        permission_decision=permission_decision,
        result=None,
        adapter_available=False,
    )

    unimplemented_result = ToolResult(
        success=False,
        message="このToolはまだ未実装です",
        executed=False,
        error="unimplemented_tool",
    )
    unimplemented_record = build_tool_execution_record(
        request,
        permission_decision=permission_decision,
        result=unimplemented_result,
        adapter_available=False,
        attempted=True,
    )

    preview_result = ToolResult(
        success=True,
        message="dry-run preview only",
        executed=False,
    )
    preview_record = build_tool_execution_record(
        request,
        permission_decision=permission_decision,
        result=preview_result,
        adapter_available=False,
        attempted=False,
    )

    failures = 0
    failures += check_true("dry-run tool_name", dry_run_record.tool_name == "web_reader")
    failures += check_true("dry-run action", dry_run_record.action == "read_url")
    failures += check_true("dry-run risk_level", dry_run_record.risk_level == "medium")
    failures += check_true("dry-run permission_needed", dry_run_record.permission_needed is True)
    failures += check_true("dry-run executed False", dry_run_record.executed is False)
    failures += check_true("dry-run success False", dry_run_record.success is False)
    failures += check_true(
        "dry-run message says not executed",
        "未実行" in dry_run_record.message or "実行していません" in dry_run_record.message,
    )

    failures += check_true("unimplemented executed False", unimplemented_record.executed is False)
    failures += check_true("unimplemented success False", unimplemented_record.success is False)
    failures += check_true("unimplemented message", "未実装" in unimplemented_record.message)

    failures += check_true("preview success True", preview_record.success is True)
    failures += check_true("preview executed False", preview_record.executed is False)

    return failures


def check_tool_execution_logger():
    from core.tool_adapter import ToolRequest
    from core.tool_execution_log import ToolExecutionLogger, build_tool_execution_record
    from core.tool_permission import evaluate_tool_permission

    request = ToolRequest(
        tool_name="web_reader",
        action="read_url",
        input_data={"original_input": "このURLを読んで"},
        requires_permission=True,
        risk_level="medium",
    )
    record = build_tool_execution_record(
        request,
        permission_decision=evaluate_tool_permission(request),
    )

    logger = ToolExecutionLogger()

    failures = 0
    failures += check_true("logger starts empty", logger.count() == 0)
    logger.add(record)
    failures += check_true("logger count increases", logger.count() == 1)
    failures += check_true("logger latest returns record", logger.latest() == record)
    failures += check_true("logger list_records returns list", isinstance(logger.list_records(), list))
    logger.clear()
    failures += check_true("logger clear works", logger.count() == 0)

    return failures


def main():
    failures = 0

    tool_execution_log = PROJECT_ROOT / "core" / "tool_execution_log.py"
    tool_adapter = PROJECT_ROOT / "core" / "tool_adapter.py"
    tool_permission = PROJECT_ROOT / "core" / "tool_permission.py"
    tool_request_builder = PROJECT_ROOT / "core" / "tool_request_builder.py"
    check_ver170 = PROJECT_ROOT / "scripts" / "check_ver170.py"
    run_ver1_checks = PROJECT_ROOT / "scripts" / "run_ver1_checks.py"
    tool_execution_log_design = PROJECT_ROOT / "docs" / "tool_execution_log_design.md"
    changelog = PROJECT_ROOT / "docs" / "changelog.md"
    project_handoff = PROJECT_ROOT / "docs" / "project_handoff.md"

    failures += check_file_exists("tool_execution_log.py", tool_execution_log)
    failures += check_file_exists("tool_adapter.py", tool_adapter)
    failures += check_file_exists("tool_permission.py", tool_permission)
    failures += check_file_exists("tool_request_builder.py", tool_request_builder)
    failures += check_file_exists("check_ver170.py", check_ver170)
    failures += check_file_exists("run_ver1_checks.py", run_ver1_checks)
    failures += check_file_exists("tool_execution_log_design.md", tool_execution_log_design)
    failures += check_file_exists("changelog.md", changelog)
    failures += check_file_exists("project_handoff.md", project_handoff)

    failures += check_imports()
    failures += check_tool_execution_record()
    failures += check_build_tool_execution_record()
    failures += check_tool_execution_logger()

    failures += check_words(
        "run_ver1_checks.py",
        run_ver1_checks,
        [
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

    failures += check_words(
        "tool_execution_log_design.md",
        tool_execution_log_design,
        [
            "ToolExecutionRecord",
            "ToolExecutionLogger",
            "build_tool_execution_record",
            "executed=False",
            "success",
            "未実行",
            "未実装",
            "実行したふりをしない",
            "DB保存はまだ行わない",
            "ToolResult",
            "Permission",
        ],
    )

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
