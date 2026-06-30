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
    final_check_doc = PROJECT_ROOT / "docs" / "version_1_0_final_check.md"
    project_handoff_doc = PROJECT_ROOT / "docs" / "project_handoff.md"
    check_script = PROJECT_ROOT / "scripts" / "check_v1_final_preparation.py"

    failures += check_file_exists("version_1_0_release_decision.md", release_decision_doc)
    failures += check_file_exists("version_1_0_final_check.md", final_check_doc)
    failures += check_file_exists("project_handoff.md", project_handoff_doc)
    failures += check_file_exists("check_v1_final_preparation.py", check_script)

    failures += check_words(
        "version_1_0_release_decision.md",
        release_decision_doc,
        [
            "総合判定",
            "GO",
            "Git状態",
            "OK",
            "Ver1.0",
            "実用テスト版",
            "Ver1.1以降",
            "Memory",
            "未実装機能",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        project_handoff_doc,
        [
            "Ver1.0 Final Preparation",
            "Ver1.0直前",
            "git tag",
            "v1.0.0",
            "GitHub Release",
            "Memory利用バランス調整",
            "Reader",
            "Tool",
            "Adapter",
        ],
    )

    failures += check_imports()

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
