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
    return check_true("check_ver2200 does not write DB", before == after)


def fake_search_func(query, limit=5):
    if "Example" in query:
        return [
            {
                "content": "[Reader Summary] Title: Example Domain URL: https://example.com Summary: Example summary",
                "source_url": "https://example.com",
                "source_tool": "web_reader",
                "created_at": "2026-07-05T00:00:00",
            }
        ][:limit]

    return []


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


def make_fake_save_memory(saved_items):
    def fake_save_memory(memory_text, *args, **kwargs):
        saved_items.append({
            "memory_text": memory_text,
            "args": args,
            "kwargs": kwargs,
        })
        return True

    return fake_save_memory


def build_lightweight_personal_ai(fake_fetcher=None, memory_search_func=None):
    from core.input_analyzer import InputAnalyzer
    from core.personal_ai import PersonalAI
    from core.tool_execution_log import ToolExecutionLogger

    ai = PersonalAI.__new__(PersonalAI)
    ai.input_analyzer = InputAnalyzer()
    ai.web_reader_fetcher = fake_fetcher
    ai.memory_search_func = memory_search_func
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
    ai.last_memory_search_intent = None
    ai.last_memory_search_result = None
    ai.last_input_analysis = None
    ai.last_response = None
    ai.save_user_message = lambda _message: None
    ai.save_assistant_message = lambda _message: None
    return ai


def check_memory_search_module():
    from core.memory_search import search_memories

    found = search_memories("Example", search_func=fake_search_func)
    not_found = search_memories("存在しない", search_func=fake_search_func)

    failures = 0
    failures += check_true("search status found", found["status"] == "found")
    failures += check_true("search result count", len(found["results"]) == 1)
    failures += check_true("search found message", "見つけました" in found["message"])
    failures += check_true("search result content", "Example Domain" in found["results"][0]["content"])
    failures += check_true("search result url", found["results"][0]["source_url"] == "https://example.com")
    failures += check_true("not found status", not_found["status"] == "not_found")
    failures += check_true("not found results empty", not_found["results"] == [])
    failures += check_true("not found message", "見つかりませんでした" in not_found["message"])

    return failures


def check_memory_search_intent():
    from core.memory_search import detect_memory_search_intent

    cases = [
        ("Example Domainについて覚えてる？", True, "Example Domain"),
        ("Web Readerテスト用ページについて記憶ある？", True, "Web Readerテスト用ページ"),
        ("普通の会話", False, ""),
        ("今保存した記憶を確認して", False, ""),
    ]
    failures = 0

    for user_input, expected_flag, expected_query in cases:
        result = detect_memory_search_intent(user_input)
        failures += check_true(
            f"intent {user_input}",
            result["is_memory_search"] is expected_flag
            and result["query"] == expected_query,
        )

    return failures


def check_personal_ai_memory_search_found():
    ai = build_lightweight_personal_ai(memory_search_func=fake_search_func)
    response = ai.handle_user_input("Example Domainについて覚えてる？")

    failures = 0
    failures += check_true("PersonalAI search found message", "保存済みMemoryから関連しそうな内容を見つけました" in response)
    failures += check_true("PersonalAI search includes content", "Example Domain" in response)
    failures += check_true("PersonalAI search includes URL", "https://example.com" in response)
    failures += check_true("PersonalAI search result stored", ai.last_memory_search_result["status"] == "found")

    return failures


def check_personal_ai_memory_search_not_found():
    ai = build_lightweight_personal_ai(memory_search_func=fake_search_func)
    response = ai.handle_user_input("存在しない内容について覚えてる？")

    failures = 0
    failures += check_true("PersonalAI search not found message", "見つかりませんでした" in response)
    failures += check_true("PersonalAI search not found stored", ai.last_memory_search_result["status"] == "not_found")

    return failures


def check_existing_flow_still_works():
    import core.personal_ai as personal_ai_module

    saved_items = []
    original_save_memory = personal_ai_module.save_memory
    personal_ai_module.save_memory = make_fake_save_memory(saved_items)

    try:
        calls = []
        ai = build_lightweight_personal_ai(
            fake_fetcher=make_fake_fetcher(calls),
            memory_search_func=fake_search_func,
        )
        confirmation_response = ai.handle_user_input("このURLを読んで https://example.com")
        read_response = ai.handle_user_input("いいよ")
        save_response = ai.handle_user_input("保存する")
        recent_response = ai.handle_user_input("今保存した記憶を確認して")
    finally:
        personal_ai_module.save_memory = original_save_memory

    failures = 0
    failures += check_true("existing flow confirmation shown", "Web Readerで読み取ってもよいですか" in confirmation_response)
    failures += check_true("existing flow fetcher called once", len(calls) == 1)
    failures += check_true("existing flow candidate shown", "Memory Candidate dry-run:" in read_response)
    failures += check_true("existing flow fake save called once", len(saved_items) == 1)
    failures += check_true("existing flow save response", "Memory Candidateを長期記憶に保存しました" in save_response)
    failures += check_true("existing flow recent response", "直近保存したMemory" in recent_response)

    return failures


def check_no_forbidden_words():
    source_paths = [
        PROJECT_ROOT / "core" / "memory_search.py",
        PROJECT_ROOT / "core" / "personal_ai.py",
        PROJECT_ROOT / "scripts" / "check_ver2200.py",
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
        ("memory_search.py", core / "memory_search.py"),
        ("personal_ai.py", core / "personal_ai.py"),
        ("check_ver2200.py", scripts / "check_ver2200.py"),
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

    failures += check_memory_search_module()
    failures += check_memory_search_intent()
    failures += check_personal_ai_memory_search_found()
    failures += check_personal_ai_memory_search_not_found()
    failures += check_existing_flow_still_works()

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
            "scripts/check_ver2200.py",
            "scripts/check_ver2190.py",
            "scripts/check_ver2180.py",
            "scripts/run_ver1_checks.py",
            "All Ver2 checks passed",
        ],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        [
            "## Version 2.20",
            "Memory検索の最小実用化",
            "覚えてる？",
            "保存済みMemory",
            "キーワード検索",
            "DBスキーマ変更はしない",
            "scripts/check_ver2200.py",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        [
            "現在バージョン:",  # version-agnostic: avoid pinning an exact VerX.X that future bumps must chase
            "Ver2.20: Memory検索の最小実用化",
            "core/memory_search.py",
            "覚えてる？",
            "保存済みMemoryを検索",
            "DBスキーマ変更はしない",
            "LLMによる検索query生成はまだ未実装",
        ],
    )

    for label, path in [
        ("reader_memory_policy.md", docs / "reader_memory_policy.md"),
        ("memory_candidate_ui_policy.md", docs / "memory_candidate_ui_policy.md"),
        ("web_reader_memory_candidate_demo.md", demo_logs / "web_reader_memory_candidate_demo.md"),
    ]:
        failures += check_words(
            label,
            path,
            [
                "Ver2.20",
                "Memory検索",
                "保存済みMemory",
                "DBスキーマ変更はしない",
            ],
        )

    failures += check_words(
        "README.md",
        PROJECT_ROOT / "README.md",
        [
            "保存済みMemoryを簡易キーワード検索する基礎",
            "ベクトル検索",
            "LLMによる高度な文脈検索",
            "docs/project_handoff.md",
        ],
    )

    failures += check_no_forbidden_words()
    failures += check_db_unchanged(db_timestamp_before)

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
