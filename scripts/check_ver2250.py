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


def check_words_absent(label, path, words):
    if not path.exists():
        print(f"[NG] {label} missing -> {path}")
        return 1

    text = path.read_text(encoding="utf-8")
    found_words = [word for word in words if word in text]

    if found_words:
        print(f"[NG] {label} has stale words -> {found_words}")
        return 1

    print(f"[OK] {label} has no stale words")
    return 0


def get_db_timestamp():
    db_path = PROJECT_ROOT / "data" / "personal_ai.db"
    return db_path.stat().st_mtime_ns if db_path.exists() else None


def check_db_unchanged(before):
    after = get_db_timestamp()
    return check_true("check_ver2250 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2250.py").read_text(encoding="utf-8")
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
        print(f"[NG] check_ver2250 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2250 has no forbidden words")
    return 0


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"

    claude_md = PROJECT_ROOT / "CLAUDE.md"
    agents = PROJECT_ROOT / "AGENTS.md"
    migration = PROJECT_ROOT / "MIGRATION.md"
    readme = PROJECT_ROOT / "README.md"
    claude_start = docs / "claude_code_start.md"
    development_workflow = docs / "development_workflow.md"
    project_handoff = docs / "project_handoff.md"
    check_workflow = docs / "check_workflow.md"
    changelog = docs / "changelog.md"
    check_ver2250 = scripts / "check_ver2250.py"
    run_ver2_checks = scripts / "run_ver2_checks.py"

    files = [
        ("CLAUDE.md", claude_md),
        ("AGENTS.md", agents),
        ("MIGRATION.md", migration),
        ("README.md", readme),
        ("claude_code_start.md", claude_start),
        ("development_workflow.md", development_workflow),
        ("project_handoff.md", project_handoff),
        ("check_workflow.md", check_workflow),
        ("changelog.md", changelog),
        ("check_ver2250.py", check_ver2250),
        ("run_ver2_checks.py", run_ver2_checks),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_words(
        "CLAUDE.md",
        claude_md,
        [
            "PersonalAI",
            "Claude Code",
            "AGENTS.md",
            "MIGRATION.md",
            "README.md",
            "Autonomous development",
            "User preferences",
            "Cost rules",
            "Failure handling",
            "Confirmation rules",
            "git commit",
            "git push",
            "reset --" + "hard",
            "force " + "push",
            "API key",
            "DB",
            "data/personal_ai.db",
            "PermissionManager",
            "【VerX.XX 完了まとめ】",
        ],
    )

    failures += check_words_absent(
        "README.md fixed version staleness",
        readme,
        [
            "現在はVer2.23です",
            "現在はVer2.24です",
        ],
    )

    failures += check_words(
        "README.md",
        readme,
        [
            "docs/project_handoff.md",
            "docs/changelog.md",
        ],
    )

    failures += check_words(
        "AGENTS.md",
        agents,
        [
            "CLAUDE.md",
            "Claude Code",
        ],
    )

    failures += check_words(
        "MIGRATION.md",
        migration,
        [
            "CLAUDE.md",
            "AGENTS.md",
            "MIGRATION.md",
            "README.md",
        ],
    )

    failures += check_words(
        "claude_code_start.md",
        claude_start,
        [
            "CLAUDE.md",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        project_handoff,
        [
            "現在バージョン: Ver2.25",
            "Ver2.25: Claude Code自走運用モード整備",
            "Ver2.26: LLM Intent Resolver設計",
        ],
    )

    failures += check_words(
        "changelog.md",
        changelog,
        [
            "## Version 2.25",
            "CLAUDE.md",
            "Claude Code",
            "自走運用",
        ],
    )

    failures += check_words(
        "run_ver2_checks.py",
        run_ver2_checks,
        [
            "scripts/check_ver2250.py",
        ],
    )

    relaxed_check_scripts = [
        scripts / "check_ver2190.py",
        scripts / "check_ver2200.py",
        scripts / "check_ver2210.py",
        scripts / "check_ver2220.py",
        scripts / "check_ver2230.py",
        scripts / "check_ver2240.py",
    ]

    for check_path in relaxed_check_scripts:
        failures += check_words_absent(
            f"{check_path.name} README version pin staleness",
            check_path,
            [
                "現在はVer2.23です",
                "現在はVer2.24です",
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
