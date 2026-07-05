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
    return check_true("check_ver2190 does not write DB", before == after)


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


def check_confirmation_intent_resolver():
    from core.confirmation_intent import resolve_confirmation_intent

    failures = 0

    for text in ["いいよ", "お願いします", "OKです", "うん"]:
        result = resolve_confirmation_intent(text, context_type="web_reader")
        failures += check_true(
            f"web reader affirmative intent: {text}",
            result["status"] == "confirmed"
            and result["context_type"] == "web_reader"
            and result["confidence"] in ["high", "medium"],
        )

    for text in ["キャンセル", "やめて", "今回はいい"]:
        result = resolve_confirmation_intent(text, context_type="web_reader")
        failures += check_true(
            f"web reader negative intent: {text}",
            result["status"] == "rejected"
            and result["context_type"] == "web_reader",
        )

    for text in ["よくわからない", "別の話だけど"]:
        result = resolve_confirmation_intent(text, context_type="web_reader")
        failures += check_true(
            f"web reader unclear intent: {text}",
            result["status"] == "unclear"
            and result["context_type"] == "web_reader",
        )

    return failures


def check_web_reader_confirmation_flow(user_reply):
    calls = []
    ai = build_lightweight_personal_ai(make_fake_fetcher(calls))

    confirmation_response = ai.handle_user_input("このURLを読んで https://example.com")
    read_response = ai.handle_user_input(user_reply)

    failures = 0
    failures += check_true(f"{user_reply} confirmation shown", "Web Readerで読み取ってもよいですか" in confirmation_response)
    failures += check_true(f"{user_reply} calls fake fetcher once", len(calls) == 1)
    failures += check_true(f"{user_reply} reads with Web Reader", "Web Readerで読み取りました" in read_response)
    failures += check_true(f"{user_reply} shows Memory Candidate", "Memory Candidate dry-run:" in read_response)
    failures += check_true(f"{user_reply} does not say unsupported", "Web Reader未対応" not in read_response and "Web Readerは未実装" not in read_response)
    failures += check_true(f"{user_reply} clears pending", ai.pending_web_reader_confirmation is None)

    return failures


def check_web_reader_cancel_flow():
    calls = []
    ai = build_lightweight_personal_ai(make_fake_fetcher(calls))

    ai.handle_user_input("このURLを読んで https://example.com")
    response = ai.handle_user_input("キャンセル")

    failures = 0
    failures += check_true("cancel does not call fake fetcher", len(calls) == 0)
    failures += check_true("cancel says not executed", "Web Readerは実行しませんでした" in response)
    failures += check_true("cancel clears pending", ai.pending_web_reader_confirmation is None)

    return failures


def check_web_reader_unclear_flow():
    calls = []
    ai = build_lightweight_personal_ai(make_fake_fetcher(calls))

    ai.handle_user_input("このURLを読んで https://example.com")
    response = ai.handle_user_input("よくわからない")

    failures = 0
    failures += check_true("unclear does not call fake fetcher", len(calls) == 0)
    failures += check_true("unclear asks confirmation again", "Web Readerを実行するか確認中です" in response)
    failures += check_true("unclear keeps pending", ai.pending_web_reader_confirmation is not None)
    failures += check_true("unclear does not say unsupported", "Web Reader未対応" not in response and "Web Readerは未実装" not in response)

    return failures


def check_memory_candidate_confirmation_words():
    from core.memory_candidate_confirmation import resolve_memory_candidate_confirmation_response

    candidate = {"title": "Example Domain", "summary": "Example summary"}
    expectations = [
        ("保存して", "confirmed"),
        ("覚えて", "confirmed"),
        ("記憶して", "confirmed"),
        ("保存しないで", "rejected"),
        ("覚えないで", "rejected"),
        ("後回し", "postponed"),
        ("修正して保存", "edit_requested"),
        ("編集したい", "edit_requested"),
    ]
    failures = 0

    for user_input, expected_status in expectations:
        result = resolve_memory_candidate_confirmation_response(user_input, candidate)
        failures += check_true(
            f"memory candidate response {user_input}",
            result["status"] == expected_status
            and result["should_save"] is False
            and result["should_execute"] is False,
        )

    return failures


def check_existing_saved_memory_flow():
    import core.personal_ai as personal_ai_module

    saved_items = []
    original_save_memory = personal_ai_module.save_memory
    personal_ai_module.save_memory = make_fake_save_memory(saved_items)

    try:
        calls = []
        ai = build_lightweight_personal_ai(make_fake_fetcher(calls))

        confirmation_response = ai.handle_user_input("このURLを読んで https://example.com")
        web_response = ai.handle_user_input("はい")
        save_response = ai.handle_user_input("保存する")
        recent_response = ai.handle_user_input("今保存した記憶を確認して")
    finally:
        personal_ai_module.save_memory = original_save_memory

    failures = 0
    failures += check_true("existing flow confirmation shown", "Web Readerで読み取ってもよいですか" in confirmation_response)
    failures += check_true("existing flow fetcher called once", len(calls) == 1)
    failures += check_true("existing flow candidate shown", "Memory Candidate dry-run:" in web_response)
    failures += check_true("existing flow fake save called once", len(saved_items) == 1)
    failures += check_true("existing flow save response", "Memory Candidateを長期記憶に保存しました" in save_response)
    failures += check_true("existing flow recent response", "直近保存したMemory" in recent_response)

    return failures


def check_no_forbidden_words():
    source_paths = [
        PROJECT_ROOT / "core" / "confirmation_intent.py",
        PROJECT_ROOT / "core" / "web_reader_confirmation.py",
        PROJECT_ROOT / "core" / "memory_candidate_confirmation.py",
        PROJECT_ROOT / "core" / "personal_ai.py",
        PROJECT_ROOT / "scripts" / "check_ver2190.py",
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
        ("confirmation_intent.py", core / "confirmation_intent.py"),
        ("web_reader_confirmation.py", core / "web_reader_confirmation.py"),
        ("memory_candidate_confirmation.py", core / "memory_candidate_confirmation.py"),
        ("personal_ai.py", core / "personal_ai.py"),
        ("check_ver2190.py", scripts / "check_ver2190.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("check_workflow.md", docs / "check_workflow.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
        ("web_reader_memory_candidate_demo.md", demo_logs / "web_reader_memory_candidate_demo.md"),
        ("development_workflow.md", docs / "development_workflow.md"),
        ("README.md", PROJECT_ROOT / "README.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_confirmation_intent_resolver()
    failures += check_web_reader_confirmation_flow("いいよ")
    failures += check_web_reader_confirmation_flow("お願いします")
    failures += check_web_reader_cancel_flow()
    failures += check_web_reader_unclear_flow()
    failures += check_memory_candidate_confirmation_words()
    failures += check_existing_saved_memory_flow()

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
            "scripts/check_ver2190.py",
            "scripts/check_ver2180.py",
            "scripts/check_ver2170.py",
            "scripts/run_ver1_checks.py",
            "All Ver2 checks passed",
        ],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        [
            "## Version 2.19",
            "確認待ち状態の文脈解釈",
            "confirmation intent",
            "いいよ",
            "お願いします",
            "キャンセル",
            "Web Reader",
            "Memory Candidate",
            "LLM解釈はまだ実装しない",
            "scripts/check_ver2190.py",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        [
            "現在バージョン: Ver2.23",
            "Ver2.19: 確認待ち状態の文脈解釈",
            "core/confirmation_intent.py",
            "いいよ",
            "お願いします",
            "キャンセル",
            "Web Reader未対応という誤解を避ける",
            "LLMによるIntent判定はまだ未実装",
        ],
    )

    failures += check_words(
        "web_reader_memory_candidate_demo.md",
        demo_logs / "web_reader_memory_candidate_demo.md",
        [
            "Ver2.19以降",
            "いいよ",
            "お願いします",
            "確認待ち中に不明な入力",
            "通常会話へ流さず確認を聞き直す",
        ],
    )

    failures += check_words(
        "development_workflow.md",
        docs / "development_workflow.md",
        [
            "LLMで文脈込みにIntent解釈",
            "PermissionManager",
            "risk判定",
            "状態管理",
            "Ver2.19時点では、LLM判定は入れず",
        ],
    )

    failures += check_words(
        "README.md",
        PROJECT_ROOT / "README.md",
        [
            "現在はVer2.23です。",
            "確認待ち状態の文脈解釈",
            "いいよ",
            "お願いします",
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
