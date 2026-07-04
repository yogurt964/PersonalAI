from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


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


def check_ver260_does_not_touch_db(before):
    """Ver2.6チェックはdocs確認だけなので、DBを書き換えない。"""
    db_path = PROJECT_ROOT / "data" / "personal_ai.db"
    after = db_path.stat().st_mtime_ns if db_path.exists() else None

    return check_true("check_ver260 does not write DB", before == after)


def check_ver260_does_not_do_real_web():
    """実Webアクセスに使うimportや実行呼び出しがないことを確認する。"""
    source = (PROJECT_ROOT / "scripts" / "check_ver260.py").read_text(encoding="utf-8")

    # 文字列を分けて書くことで、このチェック自身が検出対象にならないようにする。
    forbidden_words = [
        "url" + "lib",
        "req" + "uests",
        "url" + "open",
        "WebReader" + "Adapter(",
        "Personal" + "AI(",
        "fe" + "tch(",
        "run_tool" + "_request(",
        "save_" + "memory(",
        "save_" + "message(",
        "create_" + "database(",
        "Base.metadata." + "create_all",
    ]

    found_words = [word for word in forbidden_words if word in source]

    if found_words:
        print(f"[NG] check_ver260 has forbidden execution words -> {found_words}")
        return 1

    print("[OK] check_ver260 does not perform real Web access")
    return 0


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"

    manual_test = docs / "web_reader_manual_test.md"
    project_handoff = docs / "project_handoff.md"
    changelog = docs / "changelog.md"
    check_workflow = docs / "check_workflow.md"
    web_reader_design = docs / "web_reader_design.md"
    ui_plan = docs / "web_reader_ui_connection_plan.md"
    check_ver260 = scripts / "check_ver260.py"
    run_ver2_checks = scripts / "run_ver2_checks.py"

    files = [
        ("web_reader_manual_test.md", manual_test),
        ("project_handoff.md", project_handoff),
        ("changelog.md", changelog),
        ("check_workflow.md", check_workflow),
        ("web_reader_design.md", web_reader_design),
        ("web_reader_ui_connection_plan.md", ui_plan),
        ("check_ver260.py", check_ver260),
        ("run_ver2_checks.py", run_ver2_checks),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_words(
        "web_reader_manual_test.md",
        manual_test,
        [
            "Ver2.5 実Web手動確認結果",
            "https://example.com",
            "Example Domain",
            "text_preview",
            "このURLを読んで https://example.com",
            "はい",
            "git status",
            "clean",
            "fake fetcher",
            "自動チェックでは引き続きfake fetcherを使い、実Webアクセスしない",
            "実Webアクセスは、ユーザー確認つきの手動確認でのみ行う",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        project_handoff,
        [
            "Ver2.6: Web Reader実Web手動テスト結果整理",
            "Ver2.5でuser_confirmed=True後にToolRunner経由でWeb Readerを実行する接続を追加",
            "Ver2.6で https://example.com の実Web手動テスト結果をdocsへ整理",
            "実Web手動確認では Example Domain と text_preview が返った",
            "自動checkでは実Webアクセスしない",
            "Reader結果全文のDB保存はまだしない",
            "PDF/Image/YouTube/File Readerはまだ未実装",
        ],
    )

    failures += check_words(
        "changelog.md",
        changelog,
        [
            "## Version 2.6",
            "Web Reader実Web手動テスト結果",
            "https://example.com",
            "Example Domain",
            "fake fetcher",
            "scripts/check_ver260.py",
        ],
    )

    failures += check_words(
        "check_workflow.md",
        check_workflow,
        [
            "scripts/check_ver260.py",
            "実Web手動テスト結果がdocsに記録",
            "このcheckはdocs確認のみを行い、実Webアクセスしない",
        ],
    )

    failures += check_words(
        "web_reader_design.md",
        web_reader_design,
        [
            "Ver2.6: 実Web手動テスト結果をdocsへ整理",
            "https://example.com",
            "Example Domain",
            "text_preview",
            "自動チェックでは引き続きfake fetcherを使い、実Webアクセスしない",
            "Reader結果のMemory保存はまだしない",
            "PDF Reader / Image Reader / YouTube Reader / File Reader は今後の段階追加",
        ],
    )

    failures += check_words(
        "web_reader_ui_connection_plan.md",
        ui_plan,
        [
            "Ver2.6",
            "このURLを読んで https://example.com",
            "Example Domain",
            "text_preview",
            "自動チェックでは引き続きfake fetcherを使い、実Webアクセスしない",
            "Reader結果のMemory保存はまだしない",
            "Ver2.5で、1から8までの最小接続はできた",
        ],
    )

    failures += check_words(
        "run_ver2_checks.py",
        run_ver2_checks,
        [
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

    failures += check_ver260_does_not_touch_db(db_timestamp_before)
    failures += check_ver260_does_not_do_real_web()

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
