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
    return check_true("check_ver2400 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2400.py").read_text(encoding="utf-8")
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
        print(f"[NG] check_ver2400 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2400 has no forbidden words")
    return 0


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"

    conversation_quality = docs / "conversation_quality.md"
    migration = PROJECT_ROOT / "MIGRATION.md"
    project_handoff = docs / "project_handoff.md"
    changelog = docs / "changelog.md"
    check_ver2400 = scripts / "check_ver2400.py"
    run_ver2_checks = scripts / "run_ver2_checks.py"

    files = [
        ("conversation_quality.md", conversation_quality),
        ("MIGRATION.md", migration),
        ("project_handoff.md", project_handoff),
        ("changelog.md", changelog),
        ("check_ver2400.py", check_ver2400),
        ("run_ver2_checks.py", run_ver2_checks),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_words(
        "conversation_quality.md",
        conversation_quality,
        [
            "データ分析・集計の正直さ",
            "分からない・自信がない場合は",
            "Qwen（ローカルモデル）自体の性能",
            "OpenAIを頼れるようにする",
            "あらためてユーザーと設計を確認する",
        ],
    )

    failures += check_words(
        "MIGRATION.md",
        migration,
        [
            "OpenAIエスカレーションの将来トリガー",
            "Qwenが複雑な分析・集計質問に安定して正確に答えられない場合",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        project_handoff,
        [
            "現在バージョン:",
            "Ver2.40: 応答の正直さ・Qwen性能・OpenAIエスカレーション方針をdocs化",
        ],
    )

    failures += check_words(
        "changelog.md",
        changelog,
        [
            "## Version 2.40",
            "OpenAIエスカレーション",
            "scripts/check_ver2400.py",
        ],
    )

    failures += check_words(
        "run_ver2_checks.py",
        run_ver2_checks,
        [
            "scripts/check_ver2400.py",
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
