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
    # importできるかだけを確認し、ここではPersonalAIを実行しません。
    try:
        from core.capability_manager import CapabilityManager
        from core.personal_ai import PersonalAI
    except Exception as error:
        print(f"[NG] imports failed -> {error}")
        return 1

    PersonalAI
    CapabilityManager
    print("[OK] imports")
    return 0


def main():
    failures = 0

    release_decision_doc = PROJECT_ROOT / "docs" / "version_1_0_release_decision.md"
    check_script = PROJECT_ROOT / "scripts" / "check_ver028.py"

    failures += check_file_exists("version_1_0_release_decision.md", release_decision_doc)
    failures += check_file_exists("check_ver028.py", check_script)

    failures += check_words(
        "version_1_0_release_decision.md",
        release_decision_doc,
        [
            "Ver1.0",
            "GO",
            "HOLD",
            "NO-GO",
            "未実装",
            "Memory",
            "Preference",
            "Permission",
            "Capability",
            "忘却dry-run",
            "project_handoff",
            "recovery_guide",
        ],
    )

    failures += check_imports()

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
