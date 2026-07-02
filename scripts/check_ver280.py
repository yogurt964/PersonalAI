import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


FAKE_HTML = """
<html>
  <head><title>Example Domain</title></head>
  <body>
    <h1>Example Domain</h1>
    <p>This   domain is for use in documentation examples without needing permission.</p>
    <p>Avoid use in operations.</p>
    <p>Learn more</p>
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


def get_db_timestamp():
    db_path = PROJECT_ROOT / "data" / "personal_ai.db"
    return db_path.stat().st_mtime_ns if db_path.exists() else None


def check_db_unchanged(before):
    after = get_db_timestamp()
    return check_true("check_ver280 does not write DB", before == after)


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


def check_success_response_format():
    calls = []
    ai = build_lightweight_personal_ai(make_fake_fetcher(calls))

    confirmation_response = ai.handle_user_input("このURLを読んで https://example.com")
    response = ai.handle_user_input("はい")

    failures = 0
    failures += check_true("confirmation shown", "Web Readerで読み取ってもよいですか" in confirmation_response)
    failures += check_true("fake fetcher called once", len(calls) == 1)
    failures += check_true("success says read", "Web Readerで読み取りました" in response)
    failures += check_true("title label is readable", "タイトル:\nExample Domain" in response)
    failures += check_true("url label is readable", "URL:\nhttps://example.com/" in response)
    failures += check_true("preview label exists", "本文プレビュー:" in response)
    failures += check_true("preview contains text", "This domain is for use in documentation examples" in response)
    failures += check_true("preview splits title line", "本文プレビュー:\nExample Domain\n" in response)
    failures += check_true("preview splits sentence", "Avoid use in operations." in response)
    failures += check_true("extra spaces are normalized", "This   domain" not in response)

    return failures


def check_long_preview_is_shortened():
    from core.personal_ai import PersonalAI
    from core.tool_adapter import ToolResult

    ai = PersonalAI.__new__(PersonalAI)
    long_preview = " ".join([f"word{i}" for i in range(120)])
    response = ai.build_web_reader_tool_response(
        ToolResult(
            success=True,
            message="ok",
            data={
                "title": "Long Page",
                "final_url": "https://example.com/long",
                "text_preview": long_preview,
            },
            error=None,
            executed=True,
        )
    )

    failures = 0
    failures += check_true("long preview keeps success", "Web Readerで読み取りました" in response)
    failures += check_true("long preview is shortened", "..." in response)
    failures += check_true("long preview response stays compact", len(response) < 650)

    return failures


def check_empty_fields_do_not_crash():
    from core.personal_ai import PersonalAI
    from core.tool_adapter import ToolResult

    ai = PersonalAI.__new__(PersonalAI)
    response = ai.build_web_reader_tool_response(
        ToolResult(
            success=True,
            message="ok",
            data={
                "title": "",
                "final_url": "https://example.com/empty",
                "text_preview": "",
            },
            error=None,
            executed=True,
        )
    )

    failures = 0
    failures += check_true("empty title fallback", "(タイトルなし)" in response)
    failures += check_true("empty preview fallback", "(本文プレビューなし)" in response)
    failures += check_true("empty fields still success", "Web Readerで読み取りました" in response)

    return failures


def check_failure_response_does_not_pretend_success():
    calls = []

    def failing_fetcher(url):
        calls.append(url)
        raise RuntimeError("fake fetch failed")

    ai = build_lightweight_personal_ai(failing_fetcher)
    ai.handle_user_input("このURLを読んで https://example.com")
    response = ai.handle_user_input("はい")

    failures = 0
    failures += check_true("failure fake fetcher called once", len(calls) == 1)
    failures += check_true("failure says failed", "失敗しました" in response)
    failures += check_true("failure has reason section", "理由:" in response)
    failures += check_true("failure has next action section", "次にできること:" in response)
    failures += check_true("failure does not pretend success", "Web Readerで読み取りました" not in response)

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

    failures = 0
    failures += check_true("user_confirmed False does not call fetcher", len(calls) == 0)
    failures += check_true("user_confirmed False says not executed", "Web Readerは実行されませんでした" in response)
    failures += check_true("user_confirmed False does not pretend success", "Web Readerで読み取りました" not in response)

    return failures


def check_check_script_uses_no_real_web():
    source = (PROJECT_ROOT / "scripts" / "check_ver280.py").read_text(encoding="utf-8")

    forbidden_words = [
        "url" + "lib",
        "req" + "uests",
        "url" + "open",
    ]
    found_words = [word for word in forbidden_words if word in source]

    if found_words:
        print(f"[NG] check_ver280 has real web access words -> {found_words}")
        return 1

    print("[OK] check_ver280 uses fake fetcher only")
    return 0


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    core = PROJECT_ROOT / "core"
    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"

    files = [
        ("personal_ai.py", core / "personal_ai.py"),
        ("check_ver280.py", scripts / "check_ver280.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("check_workflow.md", docs / "check_workflow.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
        ("web_reader_design.md", docs / "web_reader_design.md"),
        ("web_reader_manual_test.md", docs / "web_reader_manual_test.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_success_response_format()
    failures += check_long_preview_is_shortened()
    failures += check_empty_fields_do_not_crash()
    failures += check_failure_response_does_not_pretend_success()
    failures += check_user_confirmed_false_does_not_execute()

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
            "check_ver280.py",
            "check_ver270.py",
            "check_ver260.py",
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
        "docs",
        docs / "changelog.md",
        [
            "## Version 2.8",
            "Web Reader結果の会話品質を改善",
            "成功時の返答を見やすくした",
            "失敗時に読めたふりをしない",
            "fake fetcher",
            "Reader結果のMemory保存はまだしない",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        [
            "現在バージョン: Ver2.8",
            "Ver2.8: Web Reader結果の会話品質改善",
            "成功時の返答を見やすくした",
            "Reader結果のMemory保存はまだしない",
        ],
    )

    failures += check_check_script_uses_no_real_web()
    failures += check_db_unchanged(db_timestamp_before)

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
