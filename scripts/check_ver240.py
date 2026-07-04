import inspect
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
        from core.personal_ai import PersonalAI
        from core.web_reader_confirmation import (
            WebReaderConfirmationResult,
            build_web_reader_tool_request_candidate,
            resolve_web_reader_confirmation_response,
        )
    except Exception as error:
        print(f"[NG] imports failed -> {error}")
        return 1

    PersonalAI
    WebReaderConfirmationResult
    build_web_reader_tool_request_candidate
    resolve_web_reader_confirmation_response

    print("[OK] imports")
    return 0


def build_lightweight_personal_ai():
    from core.input_analyzer import InputAnalyzer
    from core.personal_ai import PersonalAI

    ai = PersonalAI.__new__(PersonalAI)
    ai.input_analyzer = InputAnalyzer()
    ai.pending_preference_confirmation = None
    ai.pending_web_reader_confirmation = None
    ai.last_web_reader_confirmation = None
    ai.last_web_reader_confirmation_result = None
    ai.last_web_reader_tool_request_candidate = None
    ai.last_input_analysis = None
    ai.last_response = None
    ai.save_user_message = lambda _message: None
    ai.save_assistant_message = lambda _message: None
    return ai


def check_url_input_creates_pending():
    ai = build_lightweight_personal_ai()

    response = ai.handle_user_input("このURLを読んで https://example.com")

    failures = 0
    failures += check_true("URL input returns confirmation", "Web Readerで読み取ってもよいですか" in response)
    failures += check_true("URL input creates pending", ai.pending_web_reader_confirmation is not None)
    failures += check_true("pending keeps URL", ai.pending_web_reader_confirmation.get("url") == "https://example.com")
    failures += check_true("pending keeps original input", "original_input" in ai.pending_web_reader_confirmation)

    return failures


def check_confirmed_response_dry_run():
    from core.web_reader_confirmation import resolve_web_reader_confirmation_response

    result = resolve_web_reader_confirmation_response(
        "はい",
        {
        "url": "https://example.com",
        "tool_name": "web_reader",
        "action": "read_url",
        "original_input": "このURLを読んで https://example.com",
        },
    )
    candidate = result.tool_request_candidate

    failures = 0
    failures += check_true("yes response says dry-run", "dry-run" in result.message)
    failures += check_true("yes response does not execute in resolver", result.should_execute is False)
    failures += check_true("yes response status confirmed", result.status == "confirmed")
    failures += check_true("yes response user_confirmed True", result.user_confirmed is True)
    failures += check_true("yes creates candidate", candidate is not None)
    failures += check_true("candidate tool_name web_reader", candidate["tool_name"] == "web_reader")
    failures += check_true("candidate action read_url", candidate["action"] == "read_url")
    failures += check_true("candidate user_confirmed True", candidate["user_confirmed"] is True)
    failures += check_true("candidate URL", candidate["input_data"]["url"] == "https://example.com")
    failures += check_true("yes does not pretend read in resolver", "読み取りました" not in result.message)

    return failures


def check_cancelled_response_dry_run():
    ai = build_lightweight_personal_ai()
    ai.pending_web_reader_confirmation = {
        "url": "https://example.com",
        "tool_name": "web_reader",
        "action": "read_url",
    }

    response = ai.handle_pending_web_reader_confirmation("いいえ")

    failures = 0
    failures += check_true("no response cancels", "実行しません" in response)
    failures += check_true("no status cancelled", ai.last_web_reader_confirmation_result["status"] == "cancelled")
    failures += check_true("no clears pending", ai.pending_web_reader_confirmation is None)
    failures += check_true("no creates no candidate", ai.last_web_reader_tool_request_candidate is None)

    return failures


def check_unclear_response_keeps_pending():
    ai = build_lightweight_personal_ai()
    ai.pending_web_reader_confirmation = {
        "url": "https://example.com",
        "tool_name": "web_reader",
        "action": "read_url",
    }

    response = ai.handle_pending_web_reader_confirmation("ところで今日の作業を続けよう")

    failures = 0
    failures += check_true("unclear response asks again", "Web Readerを実行するか確認中です" in response)
    failures += check_true("unclear response status unclear", ai.last_web_reader_confirmation_result["status"] == "unclear")
    failures += check_true("unclear response keeps pending", ai.pending_web_reader_confirmation is not None)
    failures += check_true("unclear response creates no candidate", ai.last_web_reader_tool_request_candidate is None)

    return failures


def check_no_pending_and_youtube():
    from core.input_analyzer import InputAnalyzer
    from core.personal_ai import build_web_reader_confirmation_response

    ai = build_lightweight_personal_ai()
    no_pending_response = ai.handle_pending_web_reader_confirmation("はい")
    analyzer = InputAnalyzer()
    youtube_response = build_web_reader_confirmation_response(
        "このYouTubeをまとめて https://youtube.com/watch?v=abc",
        input_analysis=analyzer.analyze("このYouTubeをまとめて https://youtube.com/watch?v=abc"),
    )

    failures = 0
    failures += check_true("no pending yes is not Web Reader execution", no_pending_response is None)
    failures += check_true("YouTube URL is not Web Reader confirmation", youtube_response is None)

    return failures


def check_no_execution_code():
    from core.web_reader_confirmation import (
        build_web_reader_tool_request_candidate,
        resolve_web_reader_confirmation_response,
    )

    personal_ai_text = (PROJECT_ROOT / "core" / "personal_ai.py").read_text(encoding="utf-8")
    resolver_source = inspect.getsource(resolve_web_reader_confirmation_response)
    candidate_source = inspect.getsource(build_web_reader_tool_request_candidate)
    combined_helper_source = resolver_source + candidate_source

    failures = 0
    failures += check_true(
        "PersonalAI uses Tool runner only after confirmation",
        "run_tool_request" in personal_ai_text,
    )
    failures += check_true(
        "PersonalAI does not call WebReaderAdapter fetch directly",
        ".fetch(" not in personal_ai_text and "urlopen" not in personal_ai_text,
    )
    failures += check_true(
        "confirmation response helper does not execute Tool",
        "run_tool_request" not in combined_helper_source and "ToolRunner" not in combined_helper_source,
    )
    failures += check_true(
        "confirmation response helper does not fetch",
        "WebReaderAdapter(" not in combined_helper_source and ".fetch(" not in combined_helper_source and "urlopen" not in combined_helper_source,
    )
    failures += check_true(
        "confirmation response helper has no DB writes",
        "create_database" not in combined_helper_source
        and "save_message" not in combined_helper_source
        and "save_memory" not in combined_helper_source
        and "Base.metadata.create_all" not in combined_helper_source,
    )

    return failures


def check_db_file_unchanged_by_dry_run():
    from core.web_reader_confirmation import resolve_web_reader_confirmation_response

    db_path = PROJECT_ROOT / "data" / "personal_ai.db"
    before = db_path.stat().st_mtime_ns if db_path.exists() else None

    resolve_web_reader_confirmation_response(
        "はい",
        {
            "url": "https://example.com",
            "tool_name": "web_reader",
            "action": "read_url",
        },
    )

    after = db_path.stat().st_mtime_ns if db_path.exists() else None

    return check_true("DB file timestamp unchanged by dry-run", before == after)


def main():
    failures = 0

    core = PROJECT_ROOT / "core"
    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"

    files = [
        ("personal_ai.py", core / "personal_ai.py"),
        ("web_reader_confirmation.py", core / "web_reader_confirmation.py"),
        ("check_ver240.py", scripts / "check_ver240.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("web_reader_ui_connection_plan.md", docs / "web_reader_ui_connection_plan.md"),
        ("web_reader_design.md", docs / "web_reader_design.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
        ("changelog.md", docs / "changelog.md"),
        ("check_workflow.md", docs / "check_workflow.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_imports()
    failures += check_url_input_creates_pending()
    failures += check_confirmed_response_dry_run()
    failures += check_cancelled_response_dry_run()
    failures += check_unclear_response_keeps_pending()
    failures += check_no_pending_and_youtube()
    failures += check_no_execution_code()
    failures += check_db_file_unchanged_by_dry_run()

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
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
        "web_reader_ui_connection_plan.md",
        docs / "web_reader_ui_connection_plan.md",
        [
            "Ver2.4",
            "確認応答",
            "ToolRequest候補",
            "実行はまだしない",
            "run_tool_request",
            "Ver2.4 checkは実Webアクセスしない",
        ],
    )

    failures += check_words(
        "web_reader_design.md",
        docs / "web_reader_design.md",
        [
            "Ver2.4",
            "確認応答",
            "ToolRequest候補",
            "WebReaderAdapterのfetchは実行しない",
            "実Webアクセスしない",
        ],
    )

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
