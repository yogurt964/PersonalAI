import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


FAKE_HTML = """
<html>
  <head><title>Example Domain</title></head>
  <body>
    <h1>Example Domain</h1>
    <p>This domain is for use in illustrative examples.</p>
  </body>
</html>
"""


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
        from core.personal_ai import PersonalAI
        from core.tool_adapter import ToolRequest
        from core.tool_runner import run_tool_request
        from core.web_reader_adapter import WebReaderAdapter
    except Exception as error:
        print(f"[NG] imports failed -> {error}")
        return 1

    PersonalAI
    ToolRequest
    run_tool_request
    WebReaderAdapter

    print("[OK] imports")
    return 0


def build_lightweight_personal_ai(fake_fetcher):
    from core.input_analyzer import InputAnalyzer
    from core.personal_ai import PersonalAI
    from core.tool_execution_log import ToolExecutionLogger

    ai = PersonalAI.__new__(PersonalAI)
    ai.input_analyzer = InputAnalyzer()
    ai.web_reader_fetcher = fake_fetcher
    ai.tool_registry = ai.build_tool_registry(fake_fetcher)
    ai.tool_execution_logger = ToolExecutionLogger()
    ai.pending_preference_confirmation = None
    ai.pending_web_reader_confirmation = None
    ai.last_web_reader_confirmation = None
    ai.last_web_reader_confirmation_result = None
    ai.last_web_reader_tool_request_candidate = None
    ai.last_web_reader_tool_run_result = None
    ai.last_web_reader_tool_result = None
    ai.last_tool_execution_record = None
    ai.last_input_analysis = None
    ai.last_response = None
    ai.save_user_message = lambda _message: None
    ai.save_assistant_message = lambda _message: None
    return ai


def make_fake_fetcher(calls, html=FAKE_HTML):
    def fake_fetcher(url):
        calls.append(url)
        return {
            "html": html,
            "final_url": "https://example.com/",
            "status_code": 200,
            "content_type": "text/html",
        }

    return fake_fetcher


def check_confirmed_web_reader_execution():
    calls = []
    ai = build_lightweight_personal_ai(make_fake_fetcher(calls))

    confirmation_response = ai.handle_user_input("このURLを読んで https://example.com")
    calls_after_confirmation = len(calls)
    read_response = ai.handle_user_input("はい")
    result = ai.last_web_reader_tool_result

    failures = 0
    failures += check_true("URL input returns confirmation message", "Web Readerで読み取ってもよいですか" in confirmation_response)
    failures += check_true("URL detection alone does not call fetcher", calls_after_confirmation == 0)
    failures += check_true("yes calls fake fetcher once", len(calls) == 1)
    failures += check_true("fake fetcher got URL", calls[0] == "https://example.com")
    failures += check_true("yes executes through ToolRunner", ai.last_web_reader_tool_run_result is not None)
    failures += check_true("success executed True", result.executed is True)
    failures += check_true("success success True", result.success is True)
    failures += check_true("response contains title", "Example Domain" in read_response)
    failures += check_true("response contains final_url", "https://example.com/" in read_response)
    failures += check_true("response contains text preview", "This domain is for use in illustrative examples." in read_response)
    failures += check_true("pending cleared after execution", ai.pending_web_reader_confirmation is None)
    failures += check_true("execution log recorded", ai.tool_execution_logger.count() == 1)
    failures += check_true("execution record executed", ai.last_tool_execution_record.executed is True)

    return failures


def check_negative_response_does_not_execute():
    calls = []
    ai = build_lightweight_personal_ai(make_fake_fetcher(calls))

    ai.handle_user_input("このURLを読んで https://example.com")
    response = ai.handle_user_input("いいえ")

    failures = 0
    failures += check_true("no response says not executed", "実行しません" in response)
    failures += check_true("no response does not call fetcher", len(calls) == 0)
    failures += check_true("no response clears pending", ai.pending_web_reader_confirmation is None)
    failures += check_true("no response creates no ToolResult", ai.last_web_reader_tool_result is None)

    return failures


def check_user_confirmed_false_does_not_execute():
    calls = []
    ai = build_lightweight_personal_ai(make_fake_fetcher(calls))
    candidate = {
        "tool_name": "web_reader",
        "action": "read_url",
        "input_data": {
            "url": "https://example.com",
            "original_input": "このURLを読んで https://example.com",
        },
        "risk_level": "medium",
        "requires_permission": True,
        "user_confirmed": False,
    }

    response = ai.execute_web_reader_tool_request_candidate(candidate)
    result = ai.last_web_reader_tool_result

    failures = 0
    failures += check_true("user_confirmed False does not call fetcher", len(calls) == 0)
    failures += check_true("user_confirmed False not executed", result.executed is False)
    failures += check_true("user_confirmed False success False", result.success is False)
    failures += check_true("user_confirmed False response says not executed", "実行されませんでした" in response)

    return failures


def check_youtube_does_not_flow_to_web_reader():
    from core.input_analyzer import InputAnalyzer
    from core.personal_ai import build_web_reader_confirmation_response

    analyzer = InputAnalyzer()
    response = build_web_reader_confirmation_response(
        "このYouTubeをまとめて https://youtube.com/watch?v=abc",
        input_analysis=analyzer.analyze("このYouTubeをまとめて https://youtube.com/watch?v=abc"),
    )

    return check_true("YouTube URL is not Web Reader confirmation", response is None)


def check_failure_response_does_not_pretend_success():
    calls = []

    def failing_fetcher(url):
        calls.append(url)
        raise RuntimeError("fake fetch failed")

    ai = build_lightweight_personal_ai(failing_fetcher)
    ai.handle_user_input("このURLを読んで https://example.com")
    response = ai.handle_user_input("はい")
    result = ai.last_web_reader_tool_result

    failures = 0
    failures += check_true("failure fake fetcher called", len(calls) == 1)
    failures += check_true("failure executed True", result.executed is True)
    failures += check_true("failure success False", result.success is False)
    failures += check_true("failure response says failed", "失敗しました" in response)
    failures += check_true("failure response does not pretend read", "Web Readerで読み取りました" not in response)

    return failures


def check_db_file_unchanged_by_fake_flow():
    db_path = PROJECT_ROOT / "data" / "personal_ai.db"
    before = db_path.stat().st_mtime_ns if db_path.exists() else None

    calls = []
    ai = build_lightweight_personal_ai(make_fake_fetcher(calls))
    ai.handle_user_input("このURLを読んで https://example.com")
    ai.handle_user_input("はい")

    after = db_path.stat().st_mtime_ns if db_path.exists() else None

    return check_true("DB file timestamp unchanged by fake flow", before == after)


def main():
    failures = 0

    core = PROJECT_ROOT / "core"
    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"

    files = [
        ("personal_ai.py", core / "personal_ai.py"),
        ("web_reader_adapter.py", core / "web_reader_adapter.py"),
        ("tool_runner.py", core / "tool_runner.py"),
        ("tool_registry.py", core / "tool_registry.py"),
        ("check_ver250.py", scripts / "check_ver250.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("web_reader_ui_connection_plan.md", docs / "web_reader_ui_connection_plan.md"),
        ("web_reader_design.md", docs / "web_reader_design.md"),
        ("web_reader_manual_test.md", docs / "web_reader_manual_test.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
        ("changelog.md", docs / "changelog.md"),
        ("check_workflow.md", docs / "check_workflow.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_imports()
    failures += check_confirmed_web_reader_execution()
    failures += check_negative_response_does_not_execute()
    failures += check_user_confirmed_false_does_not_execute()
    failures += check_youtube_does_not_flow_to_web_reader()
    failures += check_failure_response_does_not_pretend_success()
    failures += check_db_file_unchanged_by_fake_flow()

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
            "check_ver250.py",
            "check_ver240.py",
            "check_ver230.py",
            "check_ver220.py",
            "check_ver210.py",
            "check_ver200.py",
            "run_ver1_checks.py",
            "All Ver2 checks passed",
        ],
    )

    failures += check_words(
        "web_reader_design.md",
        docs / "web_reader_design.md",
        [
            "Ver2.5",
            "user_confirmed=True",
            "ToolRunner経由",
            "title",
            "final_url",
            "text_preview",
            "読めたふりをしない",
        ],
    )

    failures += check_words(
        "web_reader_ui_connection_plan.md",
        docs / "web_reader_ui_connection_plan.md",
        [
            "Ver2.5",
            "肯定応答",
            "保留中の確認",
            "ToolRunner経由",
            "URL検出だけではWebアクセスしない",
            "fake fetcher",
        ],
    )

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
