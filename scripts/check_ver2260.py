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
    return check_true("check_ver2260 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2260.py").read_text(encoding="utf-8")
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
        print(f"[NG] check_ver2260 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2260 has no forbidden words")
    return 0


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    core = PROJECT_ROOT / "core"
    scripts = PROJECT_ROOT / "scripts"

    design_doc = docs / "llm_intent_resolver_design.md"
    confirmation_intent = core / "confirmation_intent.py"
    memory_candidate_confirmation = core / "memory_candidate_confirmation.py"
    project_handoff = docs / "project_handoff.md"
    changelog = docs / "changelog.md"
    check_workflow = docs / "check_workflow.md"
    check_ver2260 = scripts / "check_ver2260.py"
    run_ver2_checks = scripts / "run_ver2_checks.py"

    files = [
        ("llm_intent_resolver_design.md", design_doc),
        ("confirmation_intent.py", confirmation_intent),
        ("memory_candidate_confirmation.py", memory_candidate_confirmation),
        ("project_handoff.md", project_handoff),
        ("changelog.md", changelog),
        ("check_workflow.md", check_workflow),
        ("check_ver2260.py", check_ver2260),
        ("run_ver2_checks.py", run_ver2_checks),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_words(
        "llm_intent_resolver_design.md",
        design_doc,
        [
            "LLM Intent Resolver",
            "core/confirmation_intent.py",
            "core/memory_candidate_confirmation.py",
            "PermissionManager",
            "ToolRunner",
            "フォールバック",
            "ハイブリッド判定",
            "Qwen",
            "OpenAI",
            "プロンプトインジェクション",
            "Ver2.26でやらないこと",
            "DBスキーマ変更",
        ],
    )

    # Ver2.26 is a design-only version: the rule-based resolvers must stay
    # untouched so the existing confirmation flows keep working unchanged.
    failures += check_words(
        "confirmation_intent.py unchanged",
        confirmation_intent,
        [
            "今はルールベースですが、将来LLM Intent Resolverに差し替えやすいように",
        ],
    )

    failures += check_words(
        "memory_candidate_confirmation.py unchanged",
        memory_candidate_confirmation,
        [
            "Ver2.13ではまだMemory保存しません",
            "Ver2.16ではまだMemory保存しません",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        project_handoff,
        [
            "現在バージョン: Ver2.26",
            "Ver2.26: LLM Intent Resolver設計",
            "Ver2.27: project_handoff.mdの現在バージョン固定依存の解消",
        ],
    )

    failures += check_words(
        "changelog.md",
        changelog,
        [
            "## Version 2.26",
            "LLM Intent Resolver",
            "docs/llm_intent_resolver_design.md",
            "scripts/check_ver2260.py",
        ],
    )

    failures += check_words(
        "check_workflow.md",
        check_workflow,
        [
            "scripts/check_ver2260.py",
        ],
    )

    failures += check_words(
        "run_ver2_checks.py",
        run_ver2_checks,
        [
            "scripts/check_ver2260.py",
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
