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
    return check_true("check_ver2140 does not write DB", before == after)


def check_check_script_is_docs_only():
    source = (PROJECT_ROOT / "scripts" / "check_ver2140.py").read_text(encoding="utf-8")
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
        print(f"[NG] check_ver2140 has forbidden execution words -> {found_words}")
        return 1

    print("[OK] check_ver2140 is docs-only")
    return 0


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"

    agents = PROJECT_ROOT / "AGENTS.md"
    development_workflow = docs / "development_workflow.md"
    project_handoff = docs / "project_handoff.md"
    changelog = docs / "changelog.md"
    check_workflow = docs / "check_workflow.md"
    check_ver2140 = scripts / "check_ver2140.py"
    run_ver2_checks = scripts / "run_ver2_checks.py"
    migration = PROJECT_ROOT / "MIGRATION.md"

    files = [
        ("AGENTS.md", agents),
        ("development_workflow.md", development_workflow),
        ("project_handoff.md", project_handoff),
        ("changelog.md", changelog),
        ("check_workflow.md", check_workflow),
        ("MIGRATION.md", migration),
        ("check_ver2140.py", check_ver2140),
        ("run_ver2_checks.py", run_ver2_checks),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_words(
        "AGENTS.md",
        agents,
        [
            "PersonalAI",
            "後から修正できる操作は確認不要",
            "git add",
            "git commit",
            "git push",
            "不可逆操作",
            "DB削除",
            "Memory物理削除",
            "課金",
            "完了まとめ",
        ],
    )

    failures += check_words(
        "development_workflow.md",
        development_workflow,
        [
            "開発速度",
            "ユーザー確認",
            "実用面",
            "コード差分",
            "Git操作",
            "dry-run",
            "ポートフォリオ",
            "Claude Code",
            "Cursor",
            "MIGRATION.md",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        project_handoff,
        [
            "Ver2.14: 開発自走方針",
            "AGENTS.md",
            "docs/development_workflow.md",
        ],
    )

    failures += check_words(
        "changelog.md",
        changelog,
        [
            "## Version 2.14",
            "開発自走方針",
            "AGENTS.md",
            "docs/development_workflow.md",
        ],
    )

    failures += check_words(
        "check_workflow.md",
        check_workflow,
        [
            "scripts/check_ver2140.py",
            "開発自走方針",
            "DB書き込み、実Webアクセス、LLM実行、Memory保存をしない",
        ],
    )

    failures += check_words(
        "run_ver2_checks.py",
        run_ver2_checks,
        [
            "scripts/check_ver2140.py",
            "scripts/check_ver2130.py",
            "scripts/check_ver2120.py",
            "scripts/check_ver2110.py",
            "scripts/check_ver2100.py",
            "scripts/check_ver290.py",
            "scripts/check_ver280.py",
            "scripts/check_ver270.py",
            "scripts/check_ver260.py",
            "scripts/check_ver250.py",
            "scripts/check_ver240.py",
            "scripts/check_ver230.py",
            "scripts/check_ver220.py",
            "scripts/check_ver210.py",
            "scripts/check_ver200.py",
            "scripts/run_ver1_checks.py",
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
