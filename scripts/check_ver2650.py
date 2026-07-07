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
    return check_true("check_ver2650 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2650.py").read_text(encoding="utf-8")
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
        print(f"[NG] check_ver2650 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2650 has no forbidden words")
    return 0


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"
    core = PROJECT_ROOT / "core"

    design_doc = docs / "llm_intent_resolver_design.md"
    project_handoff = docs / "project_handoff.md"
    changelog = docs / "changelog.md"
    check_ver2650 = scripts / "check_ver2650.py"
    run_ver2_checks = scripts / "run_ver2_checks.py"

    files = [
        ("llm_intent_resolver_design.md", design_doc),
        ("project_handoff.md", project_handoff),
        ("changelog.md", changelog),
        ("check_ver2650.py", check_ver2650),
        ("run_ver2_checks.py", run_ver2_checks),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_words(
        "llm_intent_resolver_design.md",
        design_doc,
        [
            "Ver2.65",
            "層単位",
            "検証層A",
            "検証層B",
            "最大OpenAI呼び出し回数の上限",
            "上限に近づいた時点",
            "Ver2.65でやらないこと",
        ],
    )

    # Ver2.65は設計docのみで、既存の解釈・エスカレーションロジックは変更していないことを確認する。
    failures += check_words(
        "capability_manager.py unchanged by this design-only version",
        core / "capability_manager.py",
        [
            "_has_non_reading_action_intent",
        ],
    )

    failures += check_words(
        "web_search_intent.py unchanged by this design-only version",
        core / "web_search_intent.py",
        [
            "PRODUCT_AND_PRICING_MARKERS",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        project_handoff,
        [
            "現在バージョン:",
            "Ver2.65:",
        ],
    )

    failures += check_words(
        "changelog.md",
        changelog,
        [
            "## Version 2.65",
            "docs/llm_intent_resolver_design.md",
            "scripts/check_ver2650.py",
        ],
    )

    failures += check_words(
        "run_ver2_checks.py",
        run_ver2_checks,
        [
            "scripts/check_ver2650.py",
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
