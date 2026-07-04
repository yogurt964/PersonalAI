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
    return check_true("check_ver2170 does not write DB", before == after)


def make_candidate(risk_level="low"):
    return {
        "source_tool": "web_reader",
        "source_url": "https://example.com/",
        "title": "Example Domain",
        "summary": "Example summary",
        "candidate_type": "reader_summary",
        "importance": "medium",
        "risk_level": risk_level,
        "requires_user_confirmation": True,
        "reasons": ["dry-run"],
        "should_save": False,
    }


def make_fake_save_memory(saved_items):
    def fake_save_memory(memory_text, *args, **kwargs):
        saved_items.append({
            "memory_text": memory_text,
            "args": args,
            "kwargs": kwargs,
        })
        return True

    return fake_save_memory


def check_saver_success():
    from core.memory_candidate_saver import save_memory_candidate

    saved_items = []
    result = save_memory_candidate(make_candidate(), make_fake_save_memory(saved_items))
    memory_text = result["memory_text"]

    failures = 0
    failures += check_true("saver status saved", result["status"] == "saved")
    failures += check_true("saver should_save True", result["should_save"] is True)
    failures += check_true("saver should_execute True", result["should_execute"] is True)
    failures += check_true("fake save called once", len(saved_items) == 1)
    failures += check_true("memory text has title", "Example Domain" in memory_text)
    failures += check_true("memory text has url", "https://example.com/" in memory_text)
    failures += check_true("memory text has summary", "Example summary" in memory_text)

    return failures


def check_saver_high_risk_block():
    from core.memory_candidate_saver import save_memory_candidate

    saved_items = []
    result = save_memory_candidate(make_candidate(risk_level="high"), make_fake_save_memory(saved_items))

    failures = 0
    failures += check_true("high risk blocked", result["status"] == "save_blocked_high_risk")
    failures += check_true("high risk should_save False", result["should_save"] is False)
    failures += check_true("high risk should_execute False", result["should_execute"] is False)
    failures += check_true("high risk fake save not called", len(saved_items) == 0)

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


def check_personal_ai_save_flow():
    import core.personal_ai as personal_ai_module

    saved_items = []
    personal_ai_module.save_memory = make_fake_save_memory(saved_items)

    calls = []
    ai = build_lightweight_personal_ai(make_fake_fetcher(calls))

    confirmation_response = ai.handle_user_input("このURLを読んで https://example.com")
    web_response = ai.handle_user_input("はい")
    save_response = ai.handle_user_input("保存する")
    save_result = ai.last_memory_candidate_save_result

    failures = 0
    failures += check_true("Web Reader confirmation shown", "Web Readerで読み取ってもよいですか" in confirmation_response)
    failures += check_true("fake fetcher called once", len(calls) == 1)
    failures += check_true("Memory Candidate dry-run shown", "Memory Candidate dry-run:" in web_response)
    failures += check_true("save response success", "長期記憶に保存しました" in save_response)
    failures += check_true("fake save called once", len(saved_items) == 1)
    failures += check_true("save result exists", isinstance(save_result, dict))
    failures += check_true("save result status", save_result["status"] == "saved")
    failures += check_true("pending confirmation cleared", ai.pending_memory_candidate_confirmation is None)

    return failures


def check_personal_ai_edited_save_flow():
    import core.personal_ai as personal_ai_module

    saved_items = []
    personal_ai_module.save_memory = make_fake_save_memory(saved_items)

    calls = []
    ai = build_lightweight_personal_ai(make_fake_fetcher(calls))
    edit_text = "このページはWeb Readerテスト用ページとして覚える候補にする"

    ai.handle_user_input("このURLを読んで https://example.com")
    ai.handle_user_input("はい")
    edit_request_response = ai.handle_user_input("編集して保存")
    edit_response = ai.handle_user_input(edit_text)
    save_response = ai.handle_user_input("保存する")
    save_result = ai.last_memory_candidate_save_result
    memory_text = saved_items[0]["memory_text"] if saved_items else ""

    failures = 0
    failures += check_true("edit request asks content", "編集内容を送ってください" in edit_request_response)
    failures += check_true("edited dry-run shown", "編集済みMemory Candidate dry-run:" in edit_response)
    failures += check_true("edited fake save called once", len(saved_items) == 1)
    failures += check_true("edited save response success", "長期記憶に保存しました" in save_response)
    failures += check_true("edited save result saved", save_result["status"] == "saved")
    failures += check_true("edited memory text has edit", edit_text in memory_text)
    failures += check_true("edited should_save True", save_result["should_save"] is True)
    failures += check_true("edited should_execute True", save_result["should_execute"] is True)

    return failures


def check_no_forbidden_execution_words():
    source_paths = [
        PROJECT_ROOT / "core" / "memory_candidate_saver.py",
        PROJECT_ROOT / "scripts" / "check_ver2170.py",
    ]
    forbidden_words = [
        "req" + "uests",
        "url" + "lib",
        "url" + "open",
        "ask_" + "llm(",
        "Base.metadata." + "create_all",
        "create_" + "database(",
        "reset --" + "hard",
        "force " + "push",
        "re" + "base",
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
    demo_logs = docs / "demo_logs"

    files = [
        ("personal_ai.py", core / "personal_ai.py"),
        ("memory_candidate_confirmation.py", core / "memory_candidate_confirmation.py"),
        ("memory_candidate_saver.py", core / "memory_candidate_saver.py"),
        ("check_ver2170.py", scripts / "check_ver2170.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("check_workflow.md", docs / "check_workflow.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
        ("reader_memory_policy.md", docs / "reader_memory_policy.md"),
        ("memory_candidate_ui_policy.md", docs / "memory_candidate_ui_policy.md"),
        ("web_reader_memory_candidate_demo.md", demo_logs / "web_reader_memory_candidate_demo.md"),
        ("README.md", PROJECT_ROOT / "README.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_saver_success()
    failures += check_saver_high_risk_block()
    failures += check_personal_ai_save_flow()
    failures += check_personal_ai_edited_save_flow()

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
            "scripts/check_ver2170.py",
            "scripts/check_ver2160.py",
            "scripts/check_ver2150.py",
            "scripts/run_ver1_checks.py",
            "All Ver2 checks passed",
        ],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        [
            "## Version 2.17",
            "Memory Candidateのユーザー確認つき保存",
            "保存する",
            "既存の長期記憶保存機構",
            "DBスキーマ変更はしない",
            "自動チェックでは実DB保存しない",
            "scripts/check_ver2170.py",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        [
            "現在バージョン: Ver2.17",
            "Ver2.17: Memory Candidateのユーザー確認つき保存",
            "core/memory_candidate_saver.py",
            "last_memory_candidate_save_result",
            "自動チェックでは実DB保存しない",
        ],
    )

    failures += check_words(
        "README.md",
        PROJECT_ROOT / "README.md",
        [
            "Memory Candidateをユーザー確認つきで長期記憶へ保存する基礎",
            "高リスク候補は自動保存しない",
            "DBスキーマ変更はしていない",
        ],
    )

    for label, path in [
        ("check_workflow.md", docs / "check_workflow.md"),
        ("reader_memory_policy.md", docs / "reader_memory_policy.md"),
        ("memory_candidate_ui_policy.md", docs / "memory_candidate_ui_policy.md"),
        ("web_reader_memory_candidate_demo.md", demo_logs / "web_reader_memory_candidate_demo.md"),
    ]:
        failures += check_words(
            label,
            path,
            [
                "Ver2.17",
                "Memory Candidateのユーザー確認つき保存",
                "自動チェックでは実DB保存しない",
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
