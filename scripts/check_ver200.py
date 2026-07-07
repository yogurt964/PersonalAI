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
        from core.tool_execution_log import ToolExecutionLogger
        from core.tool_permission import evaluate_tool_permission
        from core.tool_registry import ToolRegistry
        from core.tool_runner import ToolRunResult, run_tool_request
        from core.web_reader_adapter import WebReaderAdapter, extract_url_from_text, strip_html_to_text
    except Exception as error:
        print(f"[NG] imports failed -> {error}")
        return 1

    WebReaderAdapter
    extract_url_from_text
    strip_html_to_text
    run_tool_request
    ToolRunResult
    ToolRequest
    ToolResult
    ToolRegistry
    evaluate_tool_permission
    ToolExecutionLogger
    PersonalAI
    CapabilityManager

    print("[OK] imports")
    return 0


def check_url_extract():
    from core.web_reader_adapter import extract_url_from_text

    failures = 0
    failures += check_true(
        "extract URL from Japanese text",
        extract_url_from_text("このURLを読んで https://example.com") == "https://example.com",
    )
    failures += check_true(
        "extract URL with query",
        extract_url_from_text("https://example.com/test?a=1") == "https://example.com/test?a=1",
    )
    failures += check_true(
        "no URL returns None",
        extract_url_from_text("URLはありません") is None,
    )

    return failures


def check_html_to_text():
    from core.web_reader_adapter import strip_html_to_text

    html = "<html><head><title>Example</title><script>secret()</script></head><body><h1>Hello</h1><p>World</p><style>.x{}</style></body></html>"
    text = strip_html_to_text(html)

    failures = 0
    failures += check_true("HTML text has Hello", "Hello" in text)
    failures += check_true("HTML text has World", "World" in text)
    failures += check_true("script content is excluded", "secret" not in text)
    failures += check_true("style content is excluded", ".x" not in text)

    return failures


def check_web_reader_with_fake_fetcher():
    from core.tool_adapter import ToolRequest, ToolResult
    from core.web_reader_adapter import WebReaderAdapter

    def fake_fetcher(url):
        return {
            "html": "<html><head><title>Example Domain</title></head><body><h1>Example Domain</h1><p>This is a test page.</p></body></html>",
            "final_url": url,
            "status_code": 200,
            "content_type": "text/html",
        }

    adapter = WebReaderAdapter(fetcher=fake_fetcher)
    request = ToolRequest(
        tool_name="web_reader",
        action="read_url",
        input_data={"url": "https://example.com"},
        requires_permission=True,
        risk_level="medium",
    )
    result = adapter.execute(request)

    failures = 0
    failures += check_true("adapter is available", adapter.is_available() is True)
    failures += check_true("execute returns ToolResult", isinstance(result, ToolResult))
    failures += check_true("fake fetch success", result.success is True)
    failures += check_true("fake fetch executed", result.executed is True)
    failures += check_true("result has url", result.data.get("url") == "https://example.com")
    failures += check_true(
        "result text has Example Domain",
        "Example Domain" in result.data.get("text", "")
        or "Example Domain" in result.data.get("text_preview", ""),
    )

    return failures


def check_missing_url():
    from core.tool_adapter import ToolRequest
    from core.web_reader_adapter import WebReaderAdapter

    adapter = WebReaderAdapter(fetcher=lambda url: "")
    request = ToolRequest(
        tool_name="web_reader",
        action="read_url",
        input_data={"original_input": "URLなしで読んで"},
        requires_permission=True,
        risk_level="medium",
    )
    result = adapter.execute(request)

    failures = 0
    failures += check_true("missing URL fails", result.success is False)
    failures += check_true("missing URL not executed", result.executed is False)
    failures += check_true("missing URL message honest", "実行していません" in result.message)

    return failures


def check_tool_runner_permission():
    from core.tool_adapter import ToolRequest
    from core.tool_execution_log import ToolExecutionLogger
    from core.tool_registry import ToolRegistry
    from core.tool_runner import run_tool_request
    from core.web_reader_adapter import WebReaderAdapter

    calls = {"count": 0}

    def fake_fetcher(url):
        calls["count"] += 1
        return {
            "html": "<html><head><title>Example Domain</title></head><body><h1>Example Domain</h1><p>This is a test page.</p></body></html>",
            "final_url": url,
        }

    registry = ToolRegistry()
    registry.register(WebReaderAdapter(fetcher=fake_fetcher))
    logger = ToolExecutionLogger()
    request = ToolRequest(
        tool_name="web_reader",
        action="read_url",
        input_data={"url": "https://example.com"},
        requires_permission=True,
        risk_level="medium",
    )

    blocked = run_tool_request(
        request,
        registry=registry,
        user_confirmed=False,
        logger=logger,
    )
    calls_after_blocked = calls["count"]
    executed = run_tool_request(
        request,
        registry=registry,
        user_confirmed=True,
        logger=logger,
    )

    failures = 0
    failures += check_true("permission needed", blocked.permission_decision.needs_user_confirmation is True)
    failures += check_true("no permission not executed", blocked.result.executed is False)
    failures += check_true("no permission record not executed", blocked.execution_record.executed is False)
    failures += check_true("fake fetcher not called before permission", calls_after_blocked == 0)
    failures += check_true("confirmed executed", executed.result.executed is True)
    failures += check_true("confirmed success", executed.result.success is True)
    failures += check_true("confirmed fake fetcher called once", calls["count"] == 1)
    failures += check_true("confirmed record executed", executed.execution_record.executed is True)
    failures += check_true("confirmed record success", executed.execution_record.success is True)
    failures += check_true("confirmed text has Example Domain", "Example Domain" in executed.result.data.get("text", ""))
    failures += check_true("logger recorded both results", logger.count() == 2)

    return failures


def main():
    failures = 0

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"
    core = PROJECT_ROOT / "core"

    files = [
        ("web_reader_adapter.py", core / "web_reader_adapter.py"),
        ("tool_runner.py", core / "tool_runner.py"),
        ("tool_adapter.py", core / "tool_adapter.py"),
        ("tool_permission.py", core / "tool_permission.py"),
        ("tool_execution_log.py", core / "tool_execution_log.py"),
        ("check_ver200.py", scripts / "check_ver200.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("web_reader_design.md", docs / "web_reader_design.md"),
        ("changelog.md", docs / "changelog.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_imports()
    failures += check_url_extract()
    failures += check_html_to_text()
    failures += check_web_reader_with_fake_fetcher()
    failures += check_missing_url()
    failures += check_tool_runner_permission()

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
            "check_ver200.py",
            "run_ver1_checks.py",
            "All Ver2 checks passed",
        ],
    )

    failures += check_words(
        "web_reader_design.md",
        docs / "web_reader_design.md",
        [
            "Web Reader",
            "Ver2.0",
            "ToolRequest",
            "ToolResult",
            "ToolExecutionLog",
            "Permission",
            "user_confirmed",
            "executed=True",
            "executed=False",
            "実行したふりをしない",
            "未許可なら実行しない",
            "自動checkでは実Webアクセスしない",
            "PDF Reader",
            "Image Reader",
            "YouTube Reader",
            "未実装",
        ],
    )

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
