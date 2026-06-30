import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.capability_manager import CapabilityManager
from core.personal_ai import PersonalAI


def check_file_exists(label, path):
    if path.exists():
        print(f"[OK] {label} exists")
        return 0

    print(f"[NG] {label} missing -> {path}")
    return 1


def check_words(label, path, words):
    text = path.read_text(encoding="utf-8")
    missing_words = [word for word in words if word not in text]

    if missing_words:
        print(f"[NG] {label} missing words -> {missing_words}")
        return 1

    print(f"[OK] {label} required words")
    return 0


def check_imports():
    PersonalAI
    CapabilityManager
    print("[OK] imports")
    return 0


def main():
    failures = 0

    final_check_doc = PROJECT_ROOT / "docs" / "version_1_0_final_check.md"
    runner_script = PROJECT_ROOT / "scripts" / "run_pre_v1_checks.py"
    check_script = PROJECT_ROOT / "scripts" / "check_ver027.py"

    failures += check_file_exists("version_1_0_final_check.md", final_check_doc)
    failures += check_file_exists("run_pre_v1_checks.py", runner_script)
    failures += check_file_exists("check_ver027.py", check_script)

    failures += check_words(
        "version_1_0_final_check.md",
        final_check_doc,
        [
            "Git状態確認",
            "自動check",
            "軽量性ベンチマーク",
            "手動テスト",
            "未実装機能",
            "Memory",
            "Preference",
            "忘却dry-run",
            "引き継ぎ",
            "Ver1.0",
        ],
    )

    failures += check_imports()

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
