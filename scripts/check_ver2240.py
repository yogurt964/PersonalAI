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
    return check_true("check_ver2240 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2240.py").read_text(encoding="utf-8")
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
        print(f"[NG] check_ver2240 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2240 has no forbidden words")
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
    check_ver2240 = scripts / "check_ver2240.py"
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
        ("check_ver2240.py", check_ver2240),
        ("run_ver2_checks.py", run_ver2_checks),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_words(
        "claude_code_start.md",
        claude_start,
        [
            "Ver2.23",
            "Ver2.24",
            "Claude Code",
            "引継ぎ確認",
            "run_ver2_checks.py",
        ],
    )

    failures += check_words(
        "MIGRATION.md",
        migration,
        [
            "Qwen / OpenAIの利用方針",
            "OpenAI API",
            "APIキー",
            "外部送信",
            "LLM Intent Resolver",
            "Memory抽出",
            "資料読解",
            "複雑なコード読解",
            "ModelRouter",
            "Qwen / Ollama",
            "金額ライン",
            "未確定",
            "1回の試行",
            "1日の上限",
            "1か月の上限",
            "Ver2.28: File Reader最小実装",
        ],
    )

    failures += check_words_absent(
        "MIGRATION.md roadmap staleness",
        migration,
        [
            "Ver2.22: LLM Intent Resolver設計",
            "Ver2.22: File Reader",
            "Ver2.22: Claude Code",
        ],
    )

    failures += check_words(
        "README.md",
        readme,
        [
            "AIモデルの方針",
            "Qwen / Ollama",
            "OpenAI",
            "APIキー",
            "外部送信",
            "課金",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        project_handoff,
        [
            "現在バージョン:",  # version-agnostic: avoid pinning an exact VerX.X that future bumps must chase
            "Ver2.24: Claude Code引継ぎ確認結果の反映",
            "Ver2.26: LLM Intent Resolver設計",
        ],
    )

    failures += check_words(
        "changelog.md",
        changelog,
        [
            "## Version 2.24",
            "Claude Code",
            "引継ぎ確認",
            "コスト方針",
            "scripts/check_ver2240.py",
        ],
    )

    failures += check_words(
        "check_workflow.md",
        check_workflow,
        [
            "scripts/check_ver2240.py",
        ],
    )

    failures += check_words(
        "run_ver2_checks.py",
        run_ver2_checks,
        [
            "scripts/check_ver2240.py",
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
