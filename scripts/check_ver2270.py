import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

RELAXED_CHECK_SCRIPTS = [
    "check_ver2180.py",
    "check_ver2190.py",
    "check_ver2200.py",
    "check_ver2210.py",
    "check_ver2220.py",
    "check_ver2230.py",
    "check_ver2240.py",
    "check_ver2250.py",
    "check_ver2260.py",
]

FIXED_VERSION_PIN_PATTERN = re.compile(r"現在バージョン:\s*Ver\d")


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
    return check_true("check_ver2270 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2270.py").read_text(encoding="utf-8")
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
        print(f"[NG] check_ver2270 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2270 has no forbidden words")
    return 0


def check_no_fixed_version_pin(script_path):
    if not script_path.exists():
        print(f"[NG] {script_path.name} missing")
        return 1

    text = script_path.read_text(encoding="utf-8")
    matches = FIXED_VERSION_PIN_PATTERN.findall(text)

    if matches:
        print(f"[NG] {script_path.name} still pins an exact current version -> {matches}")
        return 1

    print(f"[OK] {script_path.name} does not pin an exact current version")
    return 0


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    scripts = PROJECT_ROOT / "scripts"
    docs = PROJECT_ROOT / "docs"

    project_handoff = docs / "project_handoff.md"
    changelog = docs / "changelog.md"
    check_workflow = docs / "check_workflow.md"
    check_ver2270 = scripts / "check_ver2270.py"
    run_ver2_checks = scripts / "run_ver2_checks.py"

    files = [
        ("project_handoff.md", project_handoff),
        ("changelog.md", changelog),
        ("check_workflow.md", check_workflow),
        ("check_ver2270.py", check_ver2270),
        ("run_ver2_checks.py", run_ver2_checks),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    for name in RELAXED_CHECK_SCRIPTS:
        failures += check_file_exists(name, scripts / name)

    for name in RELAXED_CHECK_SCRIPTS:
        failures += check_no_fixed_version_pin(scripts / name)

    failures += check_words(
        "project_handoff.md",
        project_handoff,
        [
            "現在バージョン: Ver2.27",
            "Ver2.27でproject_handoff.mdの現在バージョン固定依存を解消",
        ],
    )

    failures += check_words(
        "changelog.md",
        changelog,
        [
            "## Version 2.27",
            "project_handoff.mdの現在バージョン固定依存を解消",
            "scripts/check_ver2270.py",
        ],
    )

    failures += check_words(
        "check_workflow.md",
        check_workflow,
        [
            "scripts/check_ver2270.py",
        ],
    )

    failures += check_words(
        "run_ver2_checks.py",
        run_ver2_checks,
        [
            "scripts/check_ver2270.py",
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
