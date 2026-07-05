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
    return check_true("check_ver2280 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2280.py").read_text(encoding="utf-8")
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
        print(f"[NG] check_ver2280 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2280 has no forbidden words")
    return 0


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"

    migration = PROJECT_ROOT / "MIGRATION.md"
    claude_md = PROJECT_ROOT / "CLAUDE.md"
    agents = PROJECT_ROOT / "AGENTS.md"
    readme = PROJECT_ROOT / "README.md"
    claude_start = docs / "claude_code_start.md"
    design_doc = docs / "llm_intent_resolver_design.md"
    project_handoff = docs / "project_handoff.md"
    changelog = docs / "changelog.md"
    check_workflow = docs / "check_workflow.md"
    check_ver2280 = scripts / "check_ver2280.py"
    run_ver2_checks = scripts / "run_ver2_checks.py"

    files = [
        ("MIGRATION.md", migration),
        ("CLAUDE.md", claude_md),
        ("AGENTS.md", agents),
        ("README.md", readme),
        ("claude_code_start.md", claude_start),
        ("llm_intent_resolver_design.md", design_doc),
        ("project_handoff.md", project_handoff),
        ("changelog.md", changelog),
        ("check_workflow.md", check_workflow),
        ("check_ver2280.py", check_ver2280),
        ("run_ver2_checks.py", run_ver2_checks),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_words(
        "MIGRATION.md",
        migration,
        [
            "月間上限額",
            "初めて実接続する前に",
            "都度確認しない",
            "APIキーの新規設定・変更は、引き続き都度ユーザー確認する",
            "作業や回答の精度が最優先",
        ],
    )

    failures += check_words(
        "CLAUDE.md",
        claude_md,
        [
            "monthly budget cap",
            "do not need per-call confirmation",
            "API key setup",
            "external transmission of private/confidential data always requires confirmation",
            "accuracy is the top priority",
        ],
    )

    failures += check_words(
        "AGENTS.md",
        agents,
        [
            "monthly budget cap",
            "accuracy is the top priority",
        ],
    )

    failures += check_words(
        "README.md",
        readme,
        [
            "月間上限額",
        ],
    )

    failures += check_words(
        "claude_code_start.md",
        claude_start,
        [
            "月間上限額",
        ],
    )

    failures += check_words(
        "llm_intent_resolver_design.md",
        design_doc,
        [
            "月間上限額",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        project_handoff,
        [
            "現在バージョン:",
            "Ver2.28: OpenAI利用方針の見直し（月間上限額制・都度確認省略）",
        ],
    )

    failures += check_words(
        "changelog.md",
        changelog,
        [
            "## Version 2.28",
            "OpenAI利用方針を見直し",
            "月間上限額",
            "scripts/check_ver2280.py",
        ],
    )

    failures += check_words(
        "check_workflow.md",
        check_workflow,
        [
            "scripts/check_ver2280.py",
        ],
    )

    failures += check_words(
        "run_ver2_checks.py",
        run_ver2_checks,
        [
            "scripts/check_ver2280.py",
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
