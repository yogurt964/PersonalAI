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
    return check_true("check_ver2220 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2220.py").read_text(encoding="utf-8")
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
        print(f"[NG] check_ver2220 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2220 has no forbidden words")
    return 0


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"

    readme = PROJECT_ROOT / "README.md"
    migration = PROJECT_ROOT / "MIGRATION.md"
    agents = PROJECT_ROOT / "AGENTS.md"
    changelog = docs / "changelog.md"
    check_workflow = docs / "check_workflow.md"
    project_handoff = docs / "project_handoff.md"
    development_workflow = docs / "development_workflow.md"
    portfolio_policy = docs / "portfolio_readme_policy.md"
    check_ver2220 = scripts / "check_ver2220.py"
    run_ver2_checks = scripts / "run_ver2_checks.py"

    files = [
        ("README.md", readme),
        ("MIGRATION.md", migration),
        ("AGENTS.md", agents),
        ("changelog.md", changelog),
        ("check_workflow.md", check_workflow),
        ("project_handoff.md", project_handoff),
        ("development_workflow.md", development_workflow),
        ("portfolio_readme_policy.md", portfolio_policy),
        ("check_ver2220.py", check_ver2220),
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
            "Memory検索",
            "確認待ち状態",
            "ポートフォリオ",
            "デモ",
            "Mermaid",
            "アーキテクチャ",
            "現在できること",
            "未実装",
            "将来的に扱いたい領域",
            "具体的なアプリ名は固定せず",
        ],
    )

    failures += check_words(
        "README.md Mermaid",
        readme,
        [
            "```mermaid",
            "flowchart",
            "sequenceDiagram",
        ],
    )

    failures += check_words(
        "changelog.md",
        changelog,
        [
            "## Version 2.22",
            "README",
            "ポートフォリオ",
            "Mermaid",
            "デモ導線",
            "アーキテクチャ図",
            "scripts/check_ver2220.py",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        project_handoff,
        [
            "現在バージョン: Ver2.26",
            "Ver2.22: READMEのポートフォリオ見せ方強化",
            "README",
            "Mermaid",
            "デモ導線",
            "ポートフォリオ",
        ],
    )

    failures += check_words(
        "check_workflow.md",
        check_workflow,
        [
            "scripts/check_ver2220.py",
            "README",
            "Mermaid",
            "デモ導線",
            "アーキテクチャ図",
        ],
    )

    failures += check_words(
        "development_workflow.md",
        development_workflow,
        [
            "docs/portfolio_readme_policy.md",
            "README",
            "ポートフォリオ",
            "Mermaid",
        ],
    )

    failures += check_words(
        "portfolio_readme_policy.md",
        portfolio_policy,
        [
            "README",
            "就活ポートフォリオ",
            "実装済みと未実装",
            "デモ",
            "Mermaid",
            "技術的工夫",
            "具体アプリ名は固定しない",
            "致命的リスク中心の安全管理",
        ],
    )

    failures += check_words(
        "run_ver2_checks.py",
        run_ver2_checks,
        [
            "scripts/check_ver2220.py",
            "scripts/check_ver2210.py",
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
