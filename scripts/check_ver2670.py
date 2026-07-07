import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


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
    return check_true("check_ver2670 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2670.py").read_text(encoding="utf-8")
    forbidden_words = [
        "req" + "uests.get",
        "req" + "uests.post",
        "ask_" + "llm(",
        "Base.metadata." + "create_all(bind=engine)",
        "create_" + "database(",
        "reset --" + "hard",
        "force " + "push",
        "re" + "base",
    ]
    found_words = [word for word in forbidden_words if word in source]

    if found_words:
        print(f"[NG] check_ver2670 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2670 has no forbidden words")
    return 0


def check_imports():
    try:
        from ai.openai_client import ask_openai_with_web_search
    except Exception as error:
        print(f"[NG] imports failed -> {error}")
        return 1

    ask_openai_with_web_search

    print("[OK] imports")
    return 0


def check_docstring_reflects_investigation_result():
    ai_dir = PROJECT_ROOT / "ai"

    return check_words(
        "ask_openai_with_web_search docstring reflects the Ver2.67 finding",
        ai_dir / "openai_client.py",
        [
            "web_search_call項目には検索クエリのみが含まれ",
            "sourcesは常にnull",
            "分離は実現不可能と判断し",
        ],
    )


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"
    ai_dir = PROJECT_ROOT / "ai"

    files = [
        ("openai_client.py", ai_dir / "openai_client.py"),
        ("check_ver2670.py", scripts / "check_ver2670.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_imports()
    failures += check_docstring_reflects_investigation_result()

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        ["check_ver2670.py"],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        ["## Version 2.67", "scripts/check_ver2670.py"],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        ["現在バージョン:", "Ver2.67:"],
    )

    failures += check_check_script_has_no_forbidden_words()
    failures += check_db_unchanged(db_timestamp_before)

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
