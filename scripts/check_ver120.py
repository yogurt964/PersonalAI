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


def check_imports():
    try:
        from ai.memory_usage_policy import decide_memory_usage
        from core.capability_manager import CapabilityManager
        from core.personal_ai import PersonalAI
    except Exception as error:
        print(f"[NG] imports failed -> {error}")
        return 1

    PersonalAI
    CapabilityManager
    decide_memory_usage
    print("[OK] imports")
    return 0


def main():
    failures = 0

    run_ver1_checks = PROJECT_ROOT / "scripts" / "run_ver1_checks.py"
    check_ver120 = PROJECT_ROOT / "scripts" / "check_ver120.py"
    changelog = PROJECT_ROOT / "docs" / "changelog.md"
    project_handoff = PROJECT_ROOT / "docs" / "project_handoff.md"
    check_workflow = PROJECT_ROOT / "docs" / "check_workflow.md"

    failures += check_file_exists("run_ver1_checks.py", run_ver1_checks)
    failures += check_file_exists("check_ver120.py", check_ver120)
    failures += check_file_exists("changelog.md", changelog)
    failures += check_file_exists("project_handoff.md", project_handoff)

    failures += check_words(
        "check_workflow.md",
        check_workflow,
        [
            "Ver1.x",
            "quick check",
            "standard check",
            "full pre-release check",
            "run_ver1_checks.py",
            "check_ver110.py",
            "check_ver120.py",
            "run_pre_v1_checks.py",
        ],
    )

    failures += check_words(
        "run_ver1_checks.py",
        run_ver1_checks,
        [
            "check_ver110.py",
            "check_v1_final_preparation.py",
            "check_ver031.py",
            "All Ver1 checks passed",
        ],
    )

    failures += check_imports()

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
