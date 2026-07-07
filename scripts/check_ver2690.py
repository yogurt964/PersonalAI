from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def check_true(label, condition):
    if condition:
        print(f"[OK] {label}")
        return 0

    print(f"[NG] {label}")
    return 1


def check_file_exists(label, path):
    if path.exists():
        print(f"[OK] {label} exists")
        return 0

    print(f"[NG] {label} missing -> {path}")
    return 1


def check_file_absent(label, path):
    if not path.exists():
        print(f"[OK] {label} is absent")
        return 0

    print(f"[NG] {label} still exists -> {path}")
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


def check_no_word(label, path, word):
    if not path.exists():
        print(f"[NG] {label} missing -> {path}")
        return 1

    text = path.read_text(encoding="utf-8")

    if word in text:
        print(f"[NG] {label} still contains -> {word}")
        return 1

    print(f"[OK] {label} no longer references {word}")
    return 0


def get_db_timestamp():
    db_path = PROJECT_ROOT / "data" / "personal_ai.db"
    return db_path.stat().st_mtime_ns if db_path.exists() else None


def check_db_unchanged(before):
    after = get_db_timestamp()
    return check_true("check_ver2690 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2690.py").read_text(encoding="utf-8")
    forbidden_words = [
        "req" + "uests.get",
        "req" + "uests.post",
        "Base.metadata." + "create_all(bind=engine)",
        "create_" + "database(",
        "reset --" + "hard",
        "force " + "push",
        "re" + "base",
    ]
    found_words = [word for word in forbidden_words if word in source]

    if found_words:
        print(f"[NG] check_ver2690 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2690 has no forbidden words")
    return 0


def check_dead_modules_removed():
    core = PROJECT_ROOT / "core"
    scripts = PROJECT_ROOT / "scripts"

    failures = 0
    failures += check_file_absent("core/tool_request_builder.py", core / "tool_request_builder.py")
    failures += check_file_absent("core/tool_flow.py", core / "tool_flow.py")
    failures += check_file_absent("scripts/check_ver160.py", scripts / "check_ver160.py")

    return failures


def check_live_tool_modules_still_present():
    """tool_flow.py経由ではなく独立して使われている現役コードは削除対象から除外されている。"""
    core = PROJECT_ROOT / "core"

    failures = 0
    for name in [
        "tool_adapter.py",
        "tool_registry.py",
        "tool_execution_log.py",
        "tool_runner.py",
        "tool_permission.py",
    ]:
        failures += check_file_exists(name, core / name)

    return failures


def check_no_stray_imports_in_scripts():
    """8本の既存チェックスクリプトから、削除済みモジュールへの参照が消えていることを確認する。"""
    scripts = PROJECT_ROOT / "scripts"

    failures = 0
    for name in [
        "check_ver170.py",
        "check_ver190.py",
        "check_ver1100.py",
        "check_ver200.py",
        "check_ver2300.py",
    ]:
        failures += check_no_word(name, scripts / name, "tool_request_builder")

    # check_ver180.py / check_ver2660.py は削除の経緯を説明するコメントとして
    # モジュール名を残しているため、実際のimport文が消えていることだけを確認する。
    for name in ["check_ver180.py", "check_ver2660.py"]:
        failures += check_no_word(name, scripts / name, "from core.tool_request_builder")
        failures += check_no_word(name, scripts / name, "from core import tool_request_builder")

    return failures


def check_imports_still_work():
    """削除後も、現役のtool系モジュールが問題なくimportできることを確認する。"""
    import sys

    sys.path.insert(0, str(PROJECT_ROOT))

    try:
        from core.tool_adapter import ToolRequest
        from core.tool_registry import ToolRegistry
        from core.tool_execution_log import ToolExecutionLogger, build_tool_execution_record
        from core.tool_runner import run_tool_request
        from core.tool_permission import evaluate_tool_permission
        from core.capability_manager import CapabilityManager
        from core.personal_ai import PersonalAI
    except Exception as error:
        print(f"[NG] live tool module imports failed -> {error}")
        return 1

    ToolRequest
    ToolRegistry
    ToolExecutionLogger
    build_tool_execution_record
    run_tool_request
    evaluate_tool_permission
    CapabilityManager
    PersonalAI

    print("[OK] live tool module imports")
    return 0


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"

    files = [
        ("check_ver2690.py", scripts / "check_ver2690.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("run_ver1_checks.py", scripts / "run_ver1_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_dead_modules_removed()
    failures += check_live_tool_modules_still_present()
    failures += check_no_stray_imports_in_scripts()
    failures += check_imports_still_work()

    failures += check_no_word("run_ver1_checks.py", scripts / "run_ver1_checks.py", "check_ver160.py")

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        ["check_ver2690.py"],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        ["## Version 2.69", "scripts/check_ver2690.py"],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        ["現在バージョン:", "Ver2.69:"],
    )

    failures += check_check_script_has_no_forbidden_words()
    failures += check_db_unchanged(db_timestamp_before)

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
