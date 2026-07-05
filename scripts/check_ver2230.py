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
    return check_true("check_ver2230 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2230.py").read_text(encoding="utf-8")
    forbidden_words = [
        "req" + "uests",
        "url" + "lib",
        "url" + "open",
        "ask_" + "llm(",
        "Base.metadata." + "create_all",
        "create_" + "database(",
        "reset --" + "hard",
        "force " + "push",
        "re" + "base",
    ]
    found_words = [word for word in forbidden_words if word in source]

    if found_words:
        print(f"[NG] check_ver2230 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2230 has no forbidden words")
    return 0


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"

    claude_start = docs / "claude_code_start.md"
    migration = PROJECT_ROOT / "MIGRATION.md"
    agents = PROJECT_ROOT / "AGENTS.md"
    readme = PROJECT_ROOT / "README.md"
    development_workflow = docs / "development_workflow.md"
    project_handoff = docs / "project_handoff.md"
    check_workflow = docs / "check_workflow.md"
    changelog = docs / "changelog.md"
    portfolio_policy = docs / "portfolio_readme_policy.md"
    check_ver2230 = scripts / "check_ver2230.py"
    run_ver2_checks = scripts / "run_ver2_checks.py"

    files = [
        ("claude_code_start.md", claude_start),
        ("MIGRATION.md", migration),
        ("AGENTS.md", agents),
        ("README.md", readme),
        ("development_workflow.md", development_workflow),
        ("project_handoff.md", project_handoff),
        ("check_workflow.md", check_workflow),
        ("changelog.md", changelog),
        ("portfolio_readme_policy.md", portfolio_policy),
        ("check_ver2230.py", check_ver2230),
        ("run_ver2_checks.py", run_ver2_checks),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_words(
        "claude_code_start.md",
        claude_start,
        [
            "Claude Code",
            "PersonalAI",
            "git status",
            "git log --oneline -5",
            "run_ver2_checks.py",
            "AGENTS.md",
            "MIGRATION.md",
            "README.md",
            "ユーザー対応方針",
            "コスト方針",
            "失敗時対応",
            "致命的リスク",
            "無駄なAPI消費",
            "DBを削除しない",
            "reset --" + "hard",
            "force " + "push",
            "引継ぎ確認",
            "Ver2.24",
            "LLM Intent Resolver",
            "File Reader",
        ],
    )

    failures += check_words(
        "README.md",
        readme,
        [
            "docs/claude_code_start.md",
            "docs/project_handoff.md",
        ],
    )

    failures += check_words(
        "MIGRATION.md",
        migration,
        [
            "docs/claude_code_start.md",
            "Claude Code移行時の入口",
        ],
    )

    failures += check_words(
        "AGENTS.md",
        agents,
        [
            "docs/claude_code_start.md",
            "For Claude Code migration",
        ],
    )

    failures += check_words(
        "changelog.md",
        changelog,
        [
            "## Version 2.23",
            "Claude Code",
            "移行準備",
            "docs/claude_code_start.md",
            "引継ぎ確認",
            "scripts/check_ver2230.py",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        project_handoff,
        [
            "現在バージョン: Ver2.26",
            "Ver2.23: Claude Code移行準備パッケージ",
            "docs/claude_code_start.md",
            "Claude Code",
            "引継ぎ確認",
        ],
    )

    failures += check_words(
        "check_workflow.md",
        check_workflow,
        [
            "scripts/check_ver2230.py",
            "Claude Code移行準備パッケージ",
            "docs/claude_code_start.md",
        ],
    )

    failures += check_words(
        "development_workflow.md",
        development_workflow,
        [
            "docs/claude_code_start.md",
            "Claude Code移行時",
            "引継ぎ確認タスク",
        ],
    )

    failures += check_words(
        "portfolio_readme_policy.md",
        portfolio_policy,
        [
            "docs/claude_code_start.md",
            "Claude Code移行時",
        ],
    )

    failures += check_words(
        "run_ver2_checks.py",
        run_ver2_checks,
        [
            "scripts/check_ver2230.py",
            "scripts/check_ver2220.py",
            "scripts/run_ver1_checks.py",
        ],
    )

    failures += check_check_script_has_no_forbidden_words()
    failures += check_db_unchanged(db_timestamp_before)

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
