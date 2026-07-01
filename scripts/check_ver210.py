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


def check_no_db_write():
    """Ver2.1チェックではDB接続や実Webアクセスを行いません。"""
    print("[OK] check_ver210.py does not write DB")
    return 0


def main():
    failures = 0

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"

    manual_test = docs / "web_reader_manual_test.md"
    ui_plan = docs / "web_reader_ui_connection_plan.md"
    design = docs / "web_reader_design.md"
    project_handoff = docs / "project_handoff.md"
    check_ver210 = scripts / "check_ver210.py"
    run_ver2_checks = scripts / "run_ver2_checks.py"

    files = [
        ("web_reader_manual_test.md", manual_test),
        ("web_reader_ui_connection_plan.md", ui_plan),
        ("web_reader_design.md", design),
        ("project_handoff.md", project_handoff),
        ("check_ver210.py", check_ver210),
        ("run_ver2_checks.py", run_ver2_checks),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    common_words = [
        "user_confirmed",
        "https://example.com",
        "ToolRunner",
        "WebReaderAdapter",
        "ToolExecutionLog",
        "会話UI",
    ]

    failures += check_words(
        "web_reader_manual_test.md",
        manual_test,
        common_words
        + [
            "自動チェックでは実Webアクセスしない",
            "user_confirmed=False",
            "success=True",
            "executed=True",
            "読めたふりをしない",
        ],
    )

    failures += check_words(
        "web_reader_ui_connection_plan.md",
        ui_plan,
        common_words
        + [
            "URLを検出しただけで勝手にアクセスしない",
            "user_confirmed=False",
            "success=False",
            "executed=False",
            "Memory",
        ],
    )

    failures += check_words(
        "web_reader_design.md",
        design,
        [
            "Ver2.1",
            "手動実行テスト",
            "会話UI接続方針",
            "自動チェックでは実Webアクセスしない",
            "実Webアクセスはユーザー確認つきの手動確認",
            "PDF Reader",
            "Image Reader",
            "YouTube Reader",
            "File Reader",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        project_handoff,
        [
            "Ver2.0.0",
            "v2.0.0",
            "PersonalAI Version 2.0.0",
            "Ver2.1でWeb Reader手動実行テストと会話UI接続方針を整理済み",
            "Web Reader手動実行テストと会話UI接続方針整理",
            "Web Readerの会話UI自動接続はまだ未実装",
        ],
    )

    failures += check_words(
        "run_ver2_checks.py",
        run_ver2_checks,
        [
            "check_ver210.py",
            "check_ver200.py",
            "run_ver1_checks.py",
            "All Ver2 checks passed",
        ],
    )

    failures += check_no_db_write()
    failures += check_true("check_ver210 does not perform real Web access", True)

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
