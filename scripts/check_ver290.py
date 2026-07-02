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


def check_db_unchanged(before):
    after = get_db_timestamp()
    return check_true("check_ver290 does not write DB", before == after)


def check_check_script_is_docs_only():
    source = (PROJECT_ROOT / "scripts" / "check_ver290.py").read_text(encoding="utf-8")

    # 文字列を分け、実行系のimportや呼び出しがないことを確認する。
    forbidden_words = [
        "url" + "lib",
        "req" + "uests",
        "url" + "open",
        "Personal" + "AI(",
        "ask_" + "llm(",
        "core.tool_" + "runner",
        "run_tool" + "_request(",
        "WebReader" + "Adapter(",
        "fetch" + "(",
        "save_" + "memory(",
        "save_" + "message(",
        "create_" + "database(",
        "Base.metadata." + "create_all",
    ]
    found_words = [word for word in forbidden_words if word in source]

    if found_words:
        print(f"[NG] check_ver290 has forbidden execution words -> {found_words}")
        return 1

    print("[OK] check_ver290 is docs-only")
    return 0


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"

    reader_memory_policy = docs / "reader_memory_policy.md"
    project_handoff = docs / "project_handoff.md"
    changelog = docs / "changelog.md"
    check_workflow = docs / "check_workflow.md"
    web_reader_design = docs / "web_reader_design.md"
    final_product_vision = docs / "final_product_vision.md"
    check_ver290 = scripts / "check_ver290.py"
    run_ver2_checks = scripts / "run_ver2_checks.py"

    files = [
        ("reader_memory_policy.md", reader_memory_policy),
        ("project_handoff.md", project_handoff),
        ("changelog.md", changelog),
        ("check_workflow.md", check_workflow),
        ("web_reader_design.md", web_reader_design),
        ("final_product_vision.md", final_product_vision),
        ("check_ver290.py", check_ver290),
        ("run_ver2_checks.py", run_ver2_checks),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_words(
        "reader_memory_policy.md",
        reader_memory_policy,
        [
            "Reader結果のMemory保存",
            "勝手に何でも保存しない",
            "重要な情報",
            "低重要度情報",
            "圧縮",
            "Archive",
            "機密情報",
            "個人情報",
            "保存前にユーザー確認",
            "Memory Candidate",
            "Project Knowledge",
            "User Preference",
            "Web Readerは読み取り結果を会話返答に出すだけ",
            "Memory保存はまだしない",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        project_handoff,
        [
            "現在バージョン: Ver2.9",
            "Ver2.9: Reader結果のMemory保存方針設計",
            "docs/reader_memory_policy.md",
            "Memory Candidate生成やユーザー確認つき保存へ進める土台を整理",
            "Memory保存の本実装はまだしていない",
            "Ver2.10: Memory Candidate生成のdry-run設計",
        ],
    )

    failures += check_words(
        "changelog.md",
        changelog,
        [
            "## Version 2.9",
            "Reader結果のMemory保存方針をdocs化",
            "docs/reader_memory_policy.md",
            "Memory Candidate / Project Knowledge / User Preference / Archive",
            "Memory保存の本実装はまだしない",
            "Web Reader結果のMemory保存はまだしない",
            "scripts/check_ver290.py",
        ],
    )

    failures += check_words(
        "check_workflow.md",
        check_workflow,
        [
            "scripts/check_ver290.py",
            "Reader結果のMemory保存方針docs",
            "実Webアクセス、DB書き込み、LLM実行、ToolRunner実行をしない",
        ],
    )

    failures += check_words(
        "web_reader_design.md",
        web_reader_design,
        [
            "Ver2.9: Reader結果のMemory保存方針をdocs化",
            "Memory Candidate",
            "Project Knowledge",
            "保存前にユーザー確認",
            "Web Reader結果のMemory保存はまだしない",
        ],
    )

    failures += check_words(
        "final_product_vision.md",
        final_product_vision,
        [
            "docs/reader_memory_policy.md",
            "Memory Candidate",
            "Project Knowledge",
            "User Preference",
            "保存前にユーザー確認",
        ],
    )

    failures += check_words(
        "run_ver2_checks.py",
        run_ver2_checks,
        [
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

    failures += check_check_script_is_docs_only()
    failures += check_db_unchanged(db_timestamp_before)

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
