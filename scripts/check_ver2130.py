import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


FAKE_HTML = """
<html>
  <head><title>Example Domain</title></head>
  <body>
    <h1>Example Domain</h1>
    <p>This domain is for use in documentation examples without needing permission.</p>
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
    return check_true("check_ver2130 does not write DB", before == after)


def make_candidate():
    return {
        "source_tool": "web_reader",
        "source_url": "https://example.com/",
        "title": "Example Domain",
        "summary": "Example summary",
        "candidate_type": "reader_summary",
        "importance": "medium",
        "risk_level": "low",
        "requires_user_confirmation": True,
        "reasons": ["dry-run"],
        "should_save": False,
    }


def check_response_case(user_input, expected_status, expected_action, requires_followup=False):
    from core.memory_candidate_confirmation import resolve_memory_candidate_confirmation_response

    result = resolve_memory_candidate_confirmation_response(user_input, make_candidate())

    failures = 0
    failures += check_true(f"{user_input} status", result["status"] == expected_status)
    failures += check_true(f"{user_input} action", result["action"] == expected_action)
    failures += check_true(f"{user_input} should_save False", result["should_save"] is False)
    failures += check_true(f"{user_input} should_execute False", result["should_execute"] is False)
    failures += check_true(f"{user_input} requires_followup", result["requires_followup"] is requires_followup)
    failures += check_true(f"{user_input} message", bool(result["message"]))
    failures += check_true(f"{user_input} candidate", result["candidate"]["title"] == "Example Domain")

    return failures


def check_confirmation_resolver_patterns():
    failures = 0

    for user_input in ["保存する", "はい", "1"]:
        failures += check_response_case(user_input, "confirmed", "save_requested_dry_run")

    for user_input in ["保存しない", "いいえ", "3"]:
        failures += check_response_case(user_input, "rejected", "discard_candidate")

    for user_input in ["後で確認", "後で", "4"]:
        failures += check_response_case(user_input, "postponed", "postpone_candidate")

    for user_input in ["編集して保存", "編集", "2"]:
        failures += check_response_case(user_input, "edit_requested", "edit_candidate_dry_run", True)

    failures += check_response_case("よくわからない", "unclear", "ask_clarification", True)

    return failures


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
    ai.pending_memory_candidate_confirmation = None
    ai.pending_web_reader_confirmation = None
    ai.last_web_reader_confirmation = None
    ai.last_web_reader_confirmation_result = None
    ai.last_web_reader_tool_request_candidate = None
    ai.last_web_reader_tool_run_result = None
    ai.last_web_reader_tool_result = None
    ai.last_tool_execution_record = None
    ai.last_memory_candidate = None
    ai.last_memory_candidate_confirmation_result = None
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


def check_personal_ai_memory_candidate_pending_flow():
    import core.personal_ai as personal_ai_module

    def forbidden_memory_writer(*_args, **_kwargs):
        raise AssertionError("save_memory must not be called in Ver2.13 dry-run")

    personal_ai_module.save_memory = forbidden_memory_writer

    calls = []
    ai = build_lightweight_personal_ai(make_fake_fetcher(calls))

    confirmation_response = ai.handle_user_input("このURLを読んで https://example.com")
    web_response = ai.handle_user_input("はい")
    pending_candidate = ai.pending_memory_candidate_confirmation
    save_response = ai.handle_user_input("保存する")
    result = ai.last_memory_candidate_confirmation_result

    failures = 0
    failures += check_true("Web Reader confirmation shown", "Web Readerで読み取ってもよいですか" in confirmation_response)
    failures += check_true("fake fetcher called once", len(calls) == 1)
    failures += check_true("Web Reader success response", "Web Readerで読み取りました" in web_response)
    failures += check_true("Memory Candidate dry-run response", "Memory Candidate dry-run:" in web_response)
    failures += check_true("pending candidate created", isinstance(pending_candidate, dict))
    failures += check_true("pending candidate should_save False", pending_candidate["should_save"] is False)
    failures += check_true("save response dry-run", "Ver2.13ではまだMemory保存しません" in save_response)
    failures += check_true("confirmation result exists", isinstance(result, dict))
    failures += check_true("save requested status", result["status"] == "confirmed")
    failures += check_true("save requested action", result["action"] == "save_requested_dry_run")
    failures += check_true("save requested should_save False", result["should_save"] is False)
    failures += check_true("save requested should_execute False", result["should_execute"] is False)
    failures += check_true("pending cleared after save request", ai.pending_memory_candidate_confirmation is None)

    return failures


def check_no_forbidden_execution_words():
    source_paths = [
        PROJECT_ROOT / "core" / "memory_candidate_confirmation.py",
        PROJECT_ROOT / "scripts" / "check_ver2130.py",
    ]
    forbidden_words = [
        "url" + "lib",
        "req" + "uests",
        "url" + "open",
        "ask_" + "llm(",
        "core.tool_" + "runner",
        "run_tool" + "_request(",
        "save_" + "memory(",
        "create_" + "database(",
        "Base.metadata." + "create_all",
    ]
    failures = 0

    for path in source_paths:
        text = path.read_text(encoding="utf-8")
        found_words = [word for word in forbidden_words if word in text]
        failures += check_true(f"{path.name} has no forbidden execution words", not found_words)

        if found_words:
            print(f"[NG] found in {path.name}: {found_words}")

    return failures


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    core = PROJECT_ROOT / "core"
    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"

    files = [
        ("memory_candidate_confirmation.py", core / "memory_candidate_confirmation.py"),
        ("personal_ai.py", core / "personal_ai.py"),
        ("check_ver2130.py", scripts / "check_ver2130.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("check_workflow.md", docs / "check_workflow.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
        ("reader_memory_policy.md", docs / "reader_memory_policy.md"),
        ("memory_candidate_ui_policy.md", docs / "memory_candidate_ui_policy.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_confirmation_resolver_patterns()
    failures += check_personal_ai_memory_candidate_pending_flow()

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
            "check_ver2130.py",
            "check_ver2120.py",
            "check_ver2110.py",
            "check_ver2100.py",
            "check_ver290.py",
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
        "changelog.md",
        docs / "changelog.md",
        [
            "## Version 2.13",
            "Memory Candidate確認応答のdry-run",
            "保存する / 保存しない / 編集して保存 / 後で確認",
            "まだMemory保存はしない",
            "Memory CandidateのDB保存もしない",
            "保存する」と言われてもdry-runで止める",
            "scripts/check_ver2130.py",
        ],
    )

    failures += check_words(
        "check_workflow.md",
        docs / "check_workflow.md",
        [
            "scripts/check_ver2130.py",
            "Memory Candidate確認応答のdry-run",
            "保存する / 保存しない / 編集して保存 / 後で確認",
            "実Webアクセス、DB書き込み、LLM実行、Memory保存をしない",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        [
            "Ver2.13: Memory Candidate確認応答のdry-run",
            "core/memory_candidate_confirmation.py",
            "保存する」と言われてもdry-runで止める",
        ],
    )

    failures += check_words(
        "reader_memory_policy.md",
        docs / "reader_memory_policy.md",
        [
            "Ver2.13",
            "Memory Candidate確認応答のdry-run",
            "保存する / 保存しない / 編集して保存 / 後で確認",
            "Memory CandidateのDB保存もしない",
        ],
    )

    failures += check_words(
        "memory_candidate_ui_policy.md",
        docs / "memory_candidate_ui_policy.md",
        [
            "Ver2.13",
            "Memory Candidate確認応答のdry-run",
            "保存する」と言われてもdry-runで止める",
            "DBスキーマ変更はしない",
        ],
    )

    failures += check_no_forbidden_execution_words()
    failures += check_db_unchanged(db_timestamp_before)

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
