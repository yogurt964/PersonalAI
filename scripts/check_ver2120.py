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
    return check_true("check_ver2120 does not write DB", before == after)


def check_check_script_is_docs_only():
    source = (PROJECT_ROOT / "scripts" / "check_ver2120.py").read_text(encoding="utf-8")
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
        print(f"[NG] check_ver2120 has forbidden execution words -> {found_words}")
        return 1

    print("[OK] check_ver2120 is docs-only")
    return 0


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"

    memory_candidate_ui_policy = docs / "memory_candidate_ui_policy.md"
    project_handoff = docs / "project_handoff.md"
    changelog = docs / "changelog.md"
    check_workflow = docs / "check_workflow.md"
    reader_memory_policy = docs / "reader_memory_policy.md"
    final_product_vision = docs / "final_product_vision.md"
    check_ver2120 = scripts / "check_ver2120.py"
    run_ver2_checks = scripts / "run_ver2_checks.py"

    files = [
        ("memory_candidate_ui_policy.md", memory_candidate_ui_policy),
        ("project_handoff.md", project_handoff),
        ("changelog.md", changelog),
        ("check_workflow.md", check_workflow),
        ("reader_memory_policy.md", reader_memory_policy),
        ("final_product_vision.md", final_product_vision),
        ("check_ver2120.py", check_ver2120),
        ("run_ver2_checks.py", run_ver2_checks),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_words(
        "memory_candidate_ui_policy.md",
        memory_candidate_ui_policy,
        [
            "Memory Candidateは勝手に保存しない",
            "保存前",
            "保存候補タイプ",
            "重要度",
            "リスク",
            "出典URL",
            "保存先候補",
            "保存する",
            "保存しない",
            "編集して保存",
            "後で確認",
            "高リスク候補",
            "自動保存しない",
            "Memory保存の本実装",
            "DBスキーマ変更",
            "Memory CandidateのDB保存",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        project_handoff,
        [
            "現在バージョン: Ver2.12",
            "Ver2.12: Memory Candidate確認UI方針",
            "docs/memory_candidate_ui_policy.md",
            "保存前にユーザーが確認できる形を整理",
            "高リスク候補は自動保存しない",
            "Memory CandidateのDB保存もしない",
        ],
    )

    failures += check_words(
        "changelog.md",
        changelog,
        [
            "## Version 2.12",
            "Memory Candidate確認UI方針をdocs化",
            "保存 / 保存しない / 編集 / 後で確認",
            "高リスク候補は自動保存しない",
            "まだMemory保存はしない",
            "Memory CandidateのDB保存もしない",
            "scripts/check_ver2120.py",
        ],
    )

    failures += check_words(
        "check_workflow.md",
        check_workflow,
        [
            "scripts/check_ver2120.py",
            "Memory Candidate確認UI方針",
            "docs確認のみ",
            "実Webアクセス、DB書き込み、LLM実行、ToolRunner実行、Memory保存をしない",
        ],
    )

    failures += check_words(
        "reader_memory_policy.md",
        reader_memory_policy,
        [
            "Ver2.12",
            "Memory Candidate確認UI方針",
            "保存 / 保存しない / 編集 / 後で確認",
            "Memory CandidateのDB保存もしない",
        ],
    )

    failures += check_words(
        "final_product_vision.md",
        final_product_vision,
        [
            "docs/memory_candidate_ui_policy.md",
            "Memory Candidate確認UI",
            "保存前にユーザーが確認できる形",
            "高リスク候補は自動保存しない",
        ],
    )

    failures += check_words(
        "run_ver2_checks.py",
        run_ver2_checks,
        [
            "check_ver2120.py",
            "check_ver2110.py",
            "check_ver2100.py",
            "check_ver290.py",
            "check_ver280.py",
            "check_ver270.py",
            "check_ver260.py",
            "check_ver250.py",
            "check_ver240.py",
            "check_ver230.py",
            "check_ver220.py",
            "check_ver210.py",
            "check_ver200.py",
            "run_ver1_checks.py",
            "All Ver2 checks passed",
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
