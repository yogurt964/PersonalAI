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

    future_doc = PROJECT_ROOT / "docs" / "future_app_integrations.md"
    manual_test_doc = PROJECT_ROOT / "docs" / "version_1_0_manual_test.md"
    check_script = PROJECT_ROOT / "scripts" / "check_ver026.py"

    failures += check_file_exists("future_app_integrations.md", future_doc)
    failures += check_file_exists("version_1_0_manual_test.md", manual_test_doc)
    failures += check_file_exists("check_ver026.py", check_script)

    failures += check_words(
        "future_app_integrations.md",
        future_doc,
        [
            "ゲーム開発",
            "アプリ開発",
            "動画制作",
            "イラスト制作",
            "音楽制作",
            "3Dモデリング",
            "Vtuber",
            "動画配信",
            "予定管理",
            "ファイル整理",
            "Tool",
            "Adapter",
            "Permission",
        ],
    )

    failures += check_words(
        "version_1_0_manual_test.md",
        manual_test_doc,
        [
            "通常会話",
            "記憶保存",
            "Preference",
            "未実装",
            "Capability",
            "Permission",
            "忘却dry-run",
            "軽量性ベンチマーク",
            "引き継ぎ",
        ],
    )

    failures += check_imports()

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
