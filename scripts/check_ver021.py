import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


DOC_CHECKS = [
    (
        "project_handoff",
        PROJECT_ROOT / "docs" / "project_handoff.md",
        [
            "Ver0.21",
            "PersonalAI",
            "GitHub",
            "ChatGPT再開用プロンプト",
            "Codex再開用プロンプト",
        ],
    ),
    (
        "recovery_guide",
        PROJECT_ROOT / "docs" / "recovery_guide.md",
        [
            "venv",
            "app.py",
            "git status",
            "check_ver020.py",
        ],
    ),
    (
        "core_principles",
        PROJECT_ROOT / "docs" / "core_principles.md",
        [
            "回答精度",
            "許可",
            "未実装",
            "壊れにく",
        ],
    ),
]


def check_file_exists(label, path):
    if not path.exists():
        print(f"[NG] {label} does not exist -> {path}")
        return 1

    print(f"[OK] {label} exists")
    return 0


def check_file_contains(label, path, required_words):
    text = path.read_text(encoding="utf-8")
    failures = 0

    for word in required_words:
        if word not in text:
            print(f"[NG] {label} missing word -> {word}")
            failures += 1

    if failures:
        return failures

    print(f"[OK] {label} required words")
    return 0


def check_personal_ai_import():
    from core.personal_ai import PersonalAI

    PersonalAI
    print("[OK] PersonalAI import")
    return 0


def main():
    failures = 0

    for label, path, required_words in DOC_CHECKS:
        failures += check_file_exists(label, path)

        if path.exists():
            failures += check_file_contains(label, path, required_words)

    failures += check_personal_ai_import()

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
