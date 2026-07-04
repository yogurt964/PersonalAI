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
    return check_true("check_ver2180 does not write DB", before == after)


def make_fake_save_memory(saved_items):
    def fake_save_memory(memory_text, *args, **kwargs):
        saved_items.append({
            "memory_text": memory_text,
            "args": args,
            "kwargs": kwargs,
        })
        return True

    return fake_save_memory


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
    ai.last_saved_memory_candidate_result = None
    ai.last_input_analysis = None
    ai.last_response = None
    ai.save_user_message = lambda _message: None
    ai.save_assistant_message = lambda _message: None
    return ai


def check_personal_ai_recent_saved_flow():
    import core.personal_ai as personal_ai_module

    saved_items = []
    personal_ai_module.save_memory = make_fake_save_memory(saved_items)

    calls = []
    ai = build_lightweight_personal_ai(make_fake_fetcher(calls))

    confirmation_response = ai.handle_user_input("このURLを読んで https://example.com")
    web_response = ai.handle_user_input("はい")
    save_response = ai.handle_user_input("保存する")
    confirm_response = ai.handle_user_input("今保存した記憶を確認して")
    save_result = ai.last_memory_candidate_save_result
    recent_result = ai.last_saved_memory_candidate_result

    failures = 0
    failures += check_true("Web Reader confirmation shown", "Web Readerで読み取ってもよいですか" in confirmation_response)
    failures += check_true("fake fetcher called once", len(calls) == 1)
    failures += check_true("Memory Candidate dry-run shown", "Memory Candidate dry-run:" in web_response)
    failures += check_true("fake save called once", len(saved_items) == 1)
    failures += check_true("save response has preview", "保存内容:" in save_response)
    failures += check_true("save response has title", "Example Domain" in save_response)
    failures += check_true("save response has url", "https://example.com/" in save_response)
    failures += check_true("last_saved result is dict", isinstance(recent_result, dict))
    failures += check_true("save result should_save True", save_result["should_save"] is True)
    failures += check_true("save result should_execute True", save_result["should_execute"] is True)
    failures += check_true("confirm response title", "Example Domain" in confirm_response)
    failures += check_true("confirm response url", "https://example.com/" in confirm_response)
    failures += check_true("confirm response says recent", "直近保存したMemory" in confirm_response)

    return failures


def check_personal_ai_recent_edited_saved_flow():
    import core.personal_ai as personal_ai_module

    saved_items = []
    personal_ai_module.save_memory = make_fake_save_memory(saved_items)

    calls = []
    ai = build_lightweight_personal_ai(make_fake_fetcher(calls))
    edit_text = "このページはWeb Readerテスト用ページとして覚える候補にする"

    ai.handle_user_input("このURLを読んで https://example.com")
    ai.handle_user_input("はい")
    ai.handle_user_input("編集して保存")
    ai.handle_user_input(edit_text)
    ai.handle_user_input("保存する")
    confirm_response = ai.handle_user_input("今保存した記憶を確認して")

    failures = 0
    failures += check_true("edited fake save called once", len(saved_items) == 1)
    failures += check_true("edited memory text saved", edit_text in saved_items[0]["memory_text"])
    failures += check_true("edited confirmation shows summary", edit_text in confirm_response)

    return failures


def check_recent_saved_empty_flow():
    calls = []
    ai = build_lightweight_personal_ai(make_fake_fetcher(calls))
    response = ai.handle_user_input("今保存した記憶を確認して")

    return check_true(
        "no recent saved memory response",
        "直近保存Memoryはまだありません" in response,
    )


def check_no_forbidden_execution_words():
    source_paths = [
        PROJECT_ROOT / "core" / "personal_ai.py",
        PROJECT_ROOT / "core" / "memory_candidate_saver.py",
        PROJECT_ROOT / "scripts" / "check_ver2180.py",
    ]
    common_forbidden_words = [
        "req" + "uests",
        "url" + "lib",
        "url" + "open",
        "ask_" + "llm(",
        "Base.metadata." + "create_all",
        "reset --" + "hard",
        "force " + "push",
        "re" + "base",
    ]
    failures = 0

    for path in source_paths:
        forbidden_words = list(common_forbidden_words)

        if path.name != "personal_ai.py":
            forbidden_words.append("create_" + "database(")

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
        ("memory_candidate_saver.py", core / "memory_candidate_saver.py"),
        ("check_ver2180.py", scripts / "check_ver2180.py"),
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

    failures += check_words(
        "personal_ai.py",
        core / "personal_ai.py",
        [
            "last_saved_memory_candidate_result",
            "今保存した記憶",
            "直近保存",
        ],
    )

    failures += check_personal_ai_recent_saved_flow()
    failures += check_personal_ai_recent_edited_saved_flow()
    failures += check_recent_saved_empty_flow()

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
            "scripts/check_ver2180.py",
            "scripts/check_ver2170.py",
            "scripts/check_ver2160.py",
            "scripts/run_ver1_checks.py",
            "All Ver2 checks passed",
        ],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        [
            "## Version 2.18",
            "Memory保存後の確認",
            "直近保存したMemory",
            "保存内容プレビュー",
            "今保存した記憶を確認して",
            "DBスキーマ変更はしない",
            "scripts/check_ver2180.py",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        [
            "現在バージョン: Ver2.20",
            "Ver2.18: Memory保存後の確認・表示フロー",
            "last_saved_memory_candidate_result",
            "今保存した記憶を確認して",
            "DBスキーマ変更はしない",
        ],
    )

    failures += check_words(
        "README.md",
        PROJECT_ROOT / "README.md",
        [
            "保存したMemory Candidateの内容を直近保存結果として確認する基礎",
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
                "Ver2.18",
                "Memory保存後の確認",
                "直近保存したMemory",
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
