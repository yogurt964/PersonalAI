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
        from core.personal_ai import build_web_reader_confirmation_response
        from core.web_reader_confirmation import build_web_reader_confirmation
    except Exception as error:
        print(f"[NG] imports failed -> {error}")
        return 1

    build_web_reader_confirmation_response
    build_web_reader_confirmation

    print("[OK] imports")
    return 0


def check_conversation_response_dry_run():
    from core.input_analyzer import InputAnalyzer
    from core.personal_ai import build_web_reader_confirmation_response
    from core.web_reader_confirmation import build_web_reader_confirmation

    analyzer = InputAnalyzer()
    user_input = "このURLを読んで https://example.com"
    input_analysis = analyzer.analyze(user_input)
    confirmation = build_web_reader_confirmation(user_input)
    response = build_web_reader_confirmation_response(
        user_input,
        input_analysis=input_analysis,
        confirmation=confirmation,
    )
    normal_response = build_web_reader_confirmation_response(
        "こんにちは",
        input_analysis=analyzer.analyze("こんにちは"),
    )
    youtube_response = build_web_reader_confirmation_response(
        "このYouTubeをまとめて https://youtube.com/watch?v=abc",
        input_analysis=analyzer.analyze("このYouTubeをまとめて https://youtube.com/watch?v=abc"),
    )

    failures = 0
    failures += check_true("URL input returns confirmation response", response is not None)
    failures += check_true("response contains URL", "https://example.com" in response)
    failures += check_true("response asks Web Reader confirmation", "Web Readerで読み取ってもよいですか" in response)
    failures += check_true("response says external Web access needs confirmation", "外部Webへアクセス" in response and "確認が必要" in response)
    failures += check_true("no URL input does not return Web Reader confirmation", normal_response is None)
    failures += check_true("YouTube URL keeps non-Web Reader path", youtube_response is None)

    return failures


def check_personal_ai_connection_source():
    from core.personal_ai import build_web_reader_confirmation_response

    personal_ai_path = PROJECT_ROOT / "core" / "personal_ai.py"
    text = personal_ai_path.read_text(encoding="utf-8")
    helper_source = inspect.getsource(build_web_reader_confirmation_response)

    forbidden_execution_words = [
        "run_tool_request",
        "ToolRunner",
        "WebReaderAdapter(",
        ".fetch(",
        "urlopen",
    ]
    forbidden_db_words = [
        "create_database",
        "save_message",
        "save_memory",
        "Base.metadata.create_all",
    ]

    failures = 0
    failures += check_true("PersonalAI imports Web Reader confirmation", "build_web_reader_confirmation" in text)
    failures += check_true("PersonalAI stores pending Web Reader confirmation", "pending_web_reader_confirmation" in text)
    failures += check_true("PersonalAI returns confirmation response", "build_web_reader_confirmation_response" in text)
    failures += check_true(
        "PersonalAI does not call ToolRunner",
        "run_tool_request" not in text and "ToolRunner" not in text,
    )
    failures += check_true(
        "PersonalAI does not call WebReaderAdapter fetch",
        "WebReaderAdapter(" not in text and ".fetch(" not in text and "urlopen" not in text,
    )
    failures += check_true(
        "confirmation helper has no execution calls",
        all(word not in helper_source for word in forbidden_execution_words),
    )
    failures += check_true(
        "confirmation helper has no DB writes",
        all(word not in helper_source for word in forbidden_db_words),
    )

    return failures


def check_yes_response_does_not_execute():
    from core.personal_ai import PersonalAI

    ai = PersonalAI.__new__(PersonalAI)
    ai.pending_web_reader_confirmation = {
        "url": "https://example.com",
        "tool_name": "web_reader",
        "action": "read_url",
    }

    response = ai.handle_pending_web_reader_confirmation("はい")

    failures = 0
    failures += check_true("yes response returns unimplemented message", "未実装" in response)
    failures += check_true("yes response clears pending confirmation", ai.pending_web_reader_confirmation is None)
    failures += check_true("yes response does not pretend execution", "読み取りました" not in response)

    return failures


def check_db_file_unchanged_by_helper():
    from core.input_analyzer import InputAnalyzer
    from core.personal_ai import build_web_reader_confirmation_response

    db_path = PROJECT_ROOT / "data" / "personal_ai.db"
    before = db_path.stat().st_mtime_ns if db_path.exists() else None

    analyzer = InputAnalyzer()
    build_web_reader_confirmation_response(
        "このURLを読んで https://example.com",
        input_analysis=analyzer.analyze("このURLを読んで https://example.com"),
    )

    after = db_path.stat().st_mtime_ns if db_path.exists() else None

    return check_true("DB file timestamp unchanged by helper", before == after)


def main():
    failures = 0

    core = PROJECT_ROOT / "core"
    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"

    files = [
        ("personal_ai.py", core / "personal_ai.py"),
        ("web_reader_confirmation.py", core / "web_reader_confirmation.py"),
        ("check_ver230.py", scripts / "check_ver230.py"),
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
    failures += check_conversation_response_dry_run()
    failures += check_personal_ai_connection_source()
    failures += check_yes_response_does_not_execute()
    failures += check_db_file_unchanged_by_helper()

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
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
            "Ver2.3",
            "URL確認メッセージを会話返答として表示",
            "Webアクセスはまだしない",
            "ToolRunner",
            "user_confirmed=True",
            "Ver2.3 checkは実Webアクセスしない",
        ],
    )

    failures += check_words(
        "web_reader_design.md",
        docs / "web_reader_design.md",
        [
            "Ver2.3",
            "会話返答として表示するdry-run接続",
            "ToolRunnerは会話UIから呼ばない",
            "WebReaderAdapterのfetchは実行しない",
        ],
    )

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
