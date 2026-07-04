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
    return check_true("check_ver2150 does not write DB", before == after)


def check_check_script_is_docs_only():
    source = (PROJECT_ROOT / "scripts" / "check_ver2150.py").read_text(encoding="utf-8")
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
        print(f"[NG] check_ver2150 has forbidden execution words -> {found_words}")
        return 1

    print("[OK] check_ver2150 is docs-only")
    return 0


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    demo_logs = docs / "demo_logs"
    scripts = PROJECT_ROOT / "scripts"

    readme = PROJECT_ROOT / "README.md"
    portfolio_notes = docs / "portfolio_notes.md"
    demo_log = demo_logs / "web_reader_memory_candidate_demo.md"
    project_handoff = docs / "project_handoff.md"
    changelog = docs / "changelog.md"
    check_workflow = docs / "check_workflow.md"
    check_ver2150 = scripts / "check_ver2150.py"
    run_ver2_checks = scripts / "run_ver2_checks.py"
    migration = PROJECT_ROOT / "MIGRATION.md"

    files = [
        ("README.md", readme),
        ("portfolio_notes.md", portfolio_notes),
        ("web_reader_memory_candidate_demo.md", demo_log),
        ("project_handoff.md", project_handoff),
        ("changelog.md", changelog),
        ("check_workflow.md", check_workflow),
        ("MIGRATION.md", migration),
        ("check_ver2150.py", check_ver2150),
        ("run_ver2_checks.py", run_ver2_checks),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_words(
        "README.md",
        readme,
        [
            "PersonalAI",
            "ローカルLLM",
            "長期記憶",
            "Web Reader",
            "Memory Candidate",
            "PermissionManager",
            "ToolRunner",
            "安全設計",
            "ロードマップ",
            "ポートフォリオ",
        ],
    )

    failures += check_words(
        "portfolio_notes.md",
        portfolio_notes,
        [
            "就活",
            "面接",
            "1分説明",
            "3分説明",
            "技術的にアピール",
            "設計",
            "未実装",
        ],
    )

    failures += check_words(
        "web_reader_memory_candidate_demo.md",
        demo_log,
        [
            "このURLを読んで",
            "https://example.com",
            "Web Readerで読み取りました",
            "Memory Candidate dry-run",
            "保存する",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        project_handoff,
        [
            "Ver2.15: ポートフォリオREADME",
            "docs/portfolio_notes.md",
            "docs/demo_logs/web_reader_memory_candidate_demo.md",
        ],
    )

    failures += check_words(
        "changelog.md",
        changelog,
        [
            "## Version 2.15",
            "ポートフォリオREADME",
            "docs/portfolio_notes.md",
            "docs/demo_logs/web_reader_memory_candidate_demo.md",
        ],
    )

    failures += check_words(
        "check_workflow.md",
        check_workflow,
        [
            "scripts/check_ver2150.py",
        ],
    )

    failures += check_words(
        "run_ver2_checks.py",
        run_ver2_checks,
        [
            "scripts/check_ver2150.py",
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
