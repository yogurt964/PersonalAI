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


REQUIRED_CANDIDATE_FIELDS = [
    "source_tool",
    "source_url",
    "title",
    "summary",
    "candidate_type",
    "importance",
    "risk_level",
    "requires_user_confirmation",
    "reasons",
    "should_save",
]


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
    return check_true("check_ver2110 does not write DB", before == after)


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
    ai.last_memory_candidate = None
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


def check_success_creates_memory_candidate_dry_run():
    calls = []
    ai = build_lightweight_personal_ai(make_fake_fetcher(calls))

    confirmation_response = ai.handle_user_input("このURLを読んで https://example.com")
    response = ai.handle_user_input("はい")
    candidate = ai.last_memory_candidate

    failures = 0
    failures += check_true("confirmation shown", "Web Readerで読み取ってもよいですか" in confirmation_response)
    failures += check_true("fake fetcher called once", len(calls) == 1)
    failures += check_true("success says read", "Web Readerで読み取りました" in response)
    failures += check_true("response has Memory Candidate dry-run", "Memory Candidate dry-run:" in response)
    failures += check_true("response says not saved", "保存実行: しない" in response)
    failures += check_true("response shows candidate_type", "保存候補タイプ:" in response)
    failures += check_true("response shows importance", "重要度:" in response)
    failures += check_true("response shows risk", "リスク:" in response)
    failures += check_true("response shows confirmation", "確認必要:" in response)
    failures += check_true("response shows reasons", "理由:" in response)
    failures += check_true("last_memory_candidate is dict", isinstance(candidate, dict))

    for field in REQUIRED_CANDIDATE_FIELDS:
        failures += check_true(f"candidate has {field}", field in candidate)

    failures += check_true("candidate source_tool", candidate["source_tool"] == "web_reader")
    failures += check_true("candidate source_url", candidate["source_url"] == "https://example.com/")
    failures += check_true("candidate title", candidate["title"] == "Example Domain")
    failures += check_true("candidate summary", "documentation examples" in candidate["summary"])
    failures += check_true("candidate reasons list", isinstance(candidate["reasons"], list))
    failures += check_true("candidate should_save False", candidate["should_save"] is False)

    return failures


def check_failure_does_not_create_memory_candidate():
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
    failures += check_true("failure has no dry-run response", "Memory Candidate dry-run:" not in response)
    failures += check_true("failure has no last_memory_candidate", ai.last_memory_candidate is None)

    return failures


def check_user_confirmed_false_does_not_create_memory_candidate():
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
    failures += check_true("user_confirmed False has no dry-run response", "Memory Candidate dry-run:" not in response)
    failures += check_true("user_confirmed False has no last_memory_candidate", ai.last_memory_candidate is None)

    return failures


def check_check_script_uses_fake_fetcher_only():
    source = (PROJECT_ROOT / "scripts" / "check_ver2110.py").read_text(encoding="utf-8")
    forbidden_words = [
        "url" + "lib",
        "req" + "uests",
        "url" + "open",
        "ask_" + "llm(",
        "save_" + "memory(",
        "Base.metadata." + "create_all",
    ]
    found_words = [word for word in forbidden_words if word in source]

    if found_words:
        print(f"[NG] check_ver2110 has forbidden execution words -> {found_words}")
        return 1

    print("[OK] check_ver2110 uses fake fetcher only")
    return 0


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    core = PROJECT_ROOT / "core"
    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"

    files = [
        ("personal_ai.py", core / "personal_ai.py"),
        ("memory_candidate.py", core / "memory_candidate.py"),
        ("check_ver2110.py", scripts / "check_ver2110.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("check_workflow.md", docs / "check_workflow.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
        ("reader_memory_policy.md", docs / "reader_memory_policy.md"),
        ("web_reader_design.md", docs / "web_reader_design.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_success_creates_memory_candidate_dry_run()
    failures += check_failure_does_not_create_memory_candidate()
    failures += check_user_confirmed_false_does_not_create_memory_candidate()

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
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
        "docs",
        docs / "changelog.md",
        [
            "## Version 2.11",
            "Memory CandidateをWeb Reader結果にdry-run接続",
            "Web Reader成功時に保存候補を作る",
            "まだMemory保存はしない",
            "Memory CandidateもDB保存しない",
            "fake fetcher",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        [
            "現在バージョン: Ver2.11",
            "Ver2.11: Memory CandidateをWeb Reader結果にdry-run接続",
            "Web Reader成功時に保存候補を作る",
            "失敗時・未実行時はMemory Candidateを作らない",
        ],
    )

    failures += check_words(
        "reader_memory_policy.md",
        docs / "reader_memory_policy.md",
        [
            "Ver2.11",
            "Memory CandidateをWeb Reader結果にdry-run接続",
            "Memory CandidateもDB保存しない",
            "失敗時・未実行時はMemory Candidateを作らない",
        ],
    )

    failures += check_words(
        "web_reader_design.md",
        docs / "web_reader_design.md",
        [
            "Ver2.11",
            "Web Reader成功時に保存候補を作る",
            "Memory Candidate dry-run",
            "fake fetcher",
        ],
    )

    failures += check_check_script_uses_fake_fetcher_only()
    failures += check_db_unchanged(db_timestamp_before)

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
