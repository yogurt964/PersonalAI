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
    return check_true("check_ver2160 does not write DB", before == after)


def make_candidate():
    return {
        "source_tool": "web_reader",
        "source_url": "https://example.com/",
        "title": "Example Domain",
        "summary": "Old summary",
        "candidate_type": "reader_summary",
        "importance": "medium",
        "risk_level": "low",
        "requires_user_confirmation": True,
        "reasons": ["dry-run"],
        "should_save": False,
    }


def check_edit_resolver():
    from core.memory_candidate_confirmation import resolve_memory_candidate_edit_response

    failures = 0
    edit_text = "このページはWeb Readerテスト用ページとして覚える候補にする"
    result = resolve_memory_candidate_edit_response(edit_text, make_candidate())
    edited_candidate = result["edited_candidate"]

    failures += check_true("edit status", result["status"] == "edited_dry_run")
    failures += check_true("edit action", result["action"] == "edit_candidate_content_dry_run")
    failures += check_true("edit should_save False", result["should_save"] is False)
    failures += check_true("edit should_execute False", result["should_execute"] is False)
    failures += check_true("edit requires_followup False", result["requires_followup"] is False)
    failures += check_true("edited summary", result["edited_summary"] == edit_text)
    failures += check_true("edited candidate summary", edited_candidate["summary"] == edit_text)
    failures += check_true("edited candidate flag", edited_candidate["edited"] is True)
    failures += check_true("edited candidate should_save False", edited_candidate["should_save"] is False)

    empty_result = resolve_memory_candidate_edit_response("", make_candidate())
    failures += check_true("empty status", empty_result["status"] == "edit_empty")
    failures += check_true("empty requires_followup True", empty_result["requires_followup"] is True)
    failures += check_true("empty should_save False", empty_result["should_save"] is False)
    failures += check_true("empty should_execute False", empty_result["should_execute"] is False)

    for user_input in ["キャンセル", "保存しない"]:
        cancel_result = resolve_memory_candidate_edit_response(user_input, make_candidate())
        failures += check_true(f"{user_input} status", cancel_result["status"] == "edit_cancelled")
        failures += check_true(f"{user_input} should_save False", cancel_result["should_save"] is False)
        failures += check_true(f"{user_input} should_execute False", cancel_result["should_execute"] is False)

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
    ai.pending_memory_candidate_edit = None
    ai.pending_web_reader_confirmation = None
    ai.last_web_reader_confirmation = None
    ai.last_web_reader_confirmation_result = None
    ai.last_web_reader_tool_request_candidate = None
    ai.last_web_reader_tool_run_result = None
    ai.last_web_reader_tool_result = None
    ai.last_tool_execution_record = None
    ai.last_memory_candidate = None
    ai.last_memory_candidate_confirmation_result = None
    ai.last_memory_candidate_save_result = None
    ai.last_input_analysis = None
    ai.last_response = None
    ai.save_user_message = lambda _message: None
    ai.save_assistant_message = lambda _message: None
    return ai


def make_fake_fetcher(calls):
    def fake_fetcher(url):
        calls.append(url)
        return {
            "html": FAKE_HTML,
            "final_url": "https://example.com/",
            "status_code": 200,
            "content_type": "text/html",
        }

    return fake_fetcher


def check_personal_ai_edit_flow():
    import core.personal_ai as personal_ai_module

    def forbidden_memory_writer(*_args, **_kwargs):
        raise AssertionError("Memory write must not be called in Ver2.16 dry-run")

    personal_ai_module.save_memory = forbidden_memory_writer

    calls = []
    ai = build_lightweight_personal_ai(make_fake_fetcher(calls))
    edit_text = "このページはWeb Readerテスト用ページとして覚える候補にする"

    confirmation_response = ai.handle_user_input("このURLを読んで https://example.com")
    web_response = ai.handle_user_input("はい")
    edit_request_response = ai.handle_user_input("編集して保存")
    edit_response = ai.handle_user_input(edit_text)
    result = ai.last_memory_candidate_confirmation_result

    failures = 0
    failures += check_true("Web Reader confirmation shown", "Web Readerで読み取ってもよいですか" in confirmation_response)
    failures += check_true("fake fetcher called once", len(calls) == 1)
    failures += check_true("Memory Candidate dry-run shown", "Memory Candidate dry-run:" in web_response)
    failures += check_true("edit request asks content", "編集内容を送ってください" in edit_request_response)
    failures += check_true("edit request says not saved", "まだMemory保存しません" in edit_request_response)
    failures += check_true("edited dry-run response", "編集済みMemory Candidate dry-run:" in edit_response)
    failures += check_true("edited response says not saved", "保存実行: しない" in edit_response)
    failures += check_true("result is dict", isinstance(result, dict))
    failures += check_true("result edited status", result["status"] == "edited_dry_run")
    failures += check_true("result should_save False", result["should_save"] is False)
    failures += check_true("result should_execute False", result["should_execute"] is False)
    failures += check_true("edited candidate exists", isinstance(result["edited_candidate"], dict))
    failures += check_true("edited summary kept", result["edited_summary"] == edit_text)
    failures += check_true("pending edit cleared", ai.pending_memory_candidate_edit is None)
    failures += check_true("pending confirmation keeps edited candidate", isinstance(ai.pending_memory_candidate_confirmation, dict))

    return failures


def check_no_forbidden_execution_words():
    source_paths = [
        PROJECT_ROOT / "core" / "memory_candidate_confirmation.py",
        PROJECT_ROOT / "scripts" / "check_ver2160.py",
    ]
    forbidden_words = [
        "req" + "uests",
        "url" + "lib",
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
        ("check_ver2160.py", scripts / "check_ver2160.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("check_workflow.md", docs / "check_workflow.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
        ("reader_memory_policy.md", docs / "reader_memory_policy.md"),
        ("memory_candidate_ui_policy.md", docs / "memory_candidate_ui_policy.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_words(
        "memory_candidate_confirmation.py",
        core / "memory_candidate_confirmation.py",
        [
            "resolve_memory_candidate_edit_response",
            "edited_candidate",
            "edited_summary",
            "should_save",
            "should_execute",
        ],
    )
    failures += check_edit_resolver()
    failures += check_personal_ai_edit_flow()

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
            "scripts/check_ver2160.py",
            "scripts/check_ver2150.py",
            "scripts/check_ver2140.py",
            "scripts/check_ver2130.py",
            "scripts/run_ver1_checks.py",
            "All Ver2 checks passed",
        ],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        [
            "## Version 2.16",
            "Memory Candidate編集dry-run",
            "編集して保存",
            "編集内容",
            "まだMemory保存はしない",
            "DBスキーマ変更はしない",
            "scripts/check_ver2160.py",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        [
            "Ver2.16: Memory Candidate編集dry-run",
            "core/memory_candidate_confirmation.py",
            "pending_memory_candidate_edit",
            "まだMemory保存はしない",
        ],
    )

    failures += check_words(
        "check_workflow.md",
        docs / "check_workflow.md",
        [
            "scripts/check_ver2160.py",
            "Memory Candidate編集dry-run",
            "編集して保存",
            "編集内容",
            "実Webアクセス、DB書き込み、LLM実行、Memory保存をしない",
        ],
    )

    failures += check_words(
        "reader_memory_policy.md",
        docs / "reader_memory_policy.md",
        [
            "Ver2.16",
            "Memory Candidate編集dry-run",
            "編集内容",
            "まだMemory保存はしない",
            "DBスキーマ変更はしない",
            "Memory CandidateのDB保存もしない",
        ],
    )

    failures += check_words(
        "memory_candidate_ui_policy.md",
        docs / "memory_candidate_ui_policy.md",
        [
            "Ver2.16",
            "Memory Candidate編集dry-run",
            "編集して保存",
            "編集内容",
            "まだMemory保存はしない",
            "Memory CandidateのDB保存もしない",
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
