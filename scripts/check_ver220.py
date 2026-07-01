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
        from core.web_reader_confirmation import (
            WebReaderConfirmation,
            build_web_reader_confirmation,
        )
    except Exception as error:
        print(f"[NG] imports failed -> {error}")
        return 1

    WebReaderConfirmation
    build_web_reader_confirmation

    print("[OK] imports")
    return 0


def check_confirmation_dry_run():
    from core.web_reader_confirmation import build_web_reader_confirmation

    result = build_web_reader_confirmation("このURLを読んでください https://example.com")
    no_url = build_web_reader_confirmation("こんにちは")

    failures = 0
    failures += check_true("URL input needs confirmation", result.needs_confirmation is True)
    failures += check_true("URL is detected", result.url == "https://example.com")
    failures += check_true("tool_name is web_reader", result.tool_name == "web_reader")
    failures += check_true("action is read_url", result.action == "read_url")
    failures += check_true("message contains URL", "https://example.com" in result.message)
    failures += check_true("message asks Web access confirmation", "外部Webへアクセス" in result.message)
    failures += check_true("message says confirmation needed", "確認が必要" in result.message)
    failures += check_true("no URL needs no confirmation", no_url.needs_confirmation is False)
    failures += check_true("no URL keeps url None", no_url.url is None)
    failures += check_true("no URL has no tool", no_url.tool_name is None)

    return failures


def check_no_execution_code():
    confirmation_file = PROJECT_ROOT / "core" / "web_reader_confirmation.py"
    text = confirmation_file.read_text(encoding="utf-8")

    forbidden_words = [
        "run_tool_request",
        "WebReaderAdapter(",
        "urlopen",
        "create_database",
        "save_memory",
        "save_message",
    ]

    missing_execution_calls = all(word not in text for word in forbidden_words)

    failures = 0
    failures += check_true("ToolRunner is not executed", "run_tool_request" not in text)
    failures += check_true("WebReaderAdapter fetch is not executed", "WebReaderAdapter(" not in text and "urlopen" not in text)
    failures += check_true("DB write code is not used", "create_database" not in text and "save_memory" not in text and "save_message" not in text)
    failures += check_true("no forbidden execution words", missing_execution_calls)

    return failures


def main():
    failures = 0

    core = PROJECT_ROOT / "core"
    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"

    files = [
        ("web_reader_confirmation.py", core / "web_reader_confirmation.py"),
        ("check_ver220.py", scripts / "check_ver220.py"),
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
    failures += check_confirmation_dry_run()
    failures += check_no_execution_code()

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
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
            "Ver2.2",
            "URL入力検出",
            "確認メッセージ",
            "dry-run",
            "Webアクセスはまだしない",
            "会話UIへの実接続はまだしない",
            "user_confirmed=True",
        ],
    )

    failures += check_words(
        "web_reader_design.md",
        docs / "web_reader_design.md",
        [
            "Ver2.2",
            "URL入力検出",
            "確認メッセージ生成",
            "ToolRunnerは呼ばない",
            "WebReaderAdapterのfetchは実行しない",
        ],
    )

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
