import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from ai.conversation_quality_policy import (
    build_conversation_quality_guidance,
    classify_conversation_mode,
)


def check_file_exists(label, path):
    if path.exists():
        print(f"[OK] {label} exists")
        return 0

    print(f"[NG] {label} missing -> {path}")
    return 1


def check_equal(label, actual, expected):
    if actual == expected:
        print(f"[OK] {label}")
        return 0

    print(f"[NG] {label} -> expected {expected}, got {actual}")
    return 1


def check_contains(label, text, expected):
    if expected in text:
        print(f"[OK] {label}")
        return 0

    print(f"[NG] {label} -> missing: {expected}")
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


def check_conversation_mode():
    failures = 0
    failures += check_equal(
        "こんにちは -> casual",
        classify_conversation_mode("こんにちは"),
        "casual",
    )
    failures += check_equal(
        "どちらがいいですか -> advice",
        classify_conversation_mode("どちらがいいですか？"),
        "advice",
    )
    failures += check_equal(
        "Python error -> development",
        classify_conversation_mode("Pythonでエラーが出ました"),
        "development",
    )
    return failures


def check_guidance_words():
    casual_guidance = build_conversation_quality_guidance("こんにちは")
    development_guidance = build_conversation_quality_guidance("Pythonでエラーが出ました")

    failures = 0
    failures += check_contains("guidance has natural short response", casual_guidance, "短めで自然")
    failures += check_contains("guidance avoids assumptions", casual_guidance, "不明点を断定しない")
    failures += check_contains(
        "guidance avoids false execution",
        casual_guidance,
        "実行していないことを実行したと言わない",
    )
    failures += check_contains(
        "guidance limits Memory",
        casual_guidance,
        "MemoryやPreferenceを必要以上に出さない",
    )
    failures += check_contains(
        "guidance organizes steps",
        development_guidance,
        "手順を順番に整理する",
    )
    return failures


def check_imports():
    try:
        from ai.conversation_quality_policy import build_conversation_quality_guidance
        from ai.memory_usage_policy import decide_memory_usage
        from core.capability_manager import CapabilityManager
        from core.personal_ai import PersonalAI
    except Exception as error:
        print(f"[NG] imports failed -> {error}")
        return 1

    PersonalAI
    CapabilityManager
    decide_memory_usage
    build_conversation_quality_guidance
    print("[OK] imports")
    return 0


def main():
    failures = 0

    conversation_quality_policy = PROJECT_ROOT / "ai" / "conversation_quality_policy.py"
    check_ver130 = PROJECT_ROOT / "scripts" / "check_ver130.py"
    run_ver1_checks = PROJECT_ROOT / "scripts" / "run_ver1_checks.py"
    changelog = PROJECT_ROOT / "docs" / "changelog.md"
    project_handoff = PROJECT_ROOT / "docs" / "project_handoff.md"
    conversation_quality_doc = PROJECT_ROOT / "docs" / "conversation_quality.md"

    failures += check_file_exists("conversation_quality_policy.py", conversation_quality_policy)
    failures += check_file_exists("check_ver130.py", check_ver130)
    failures += check_file_exists("run_ver1_checks.py", run_ver1_checks)
    failures += check_file_exists("changelog.md", changelog)
    failures += check_file_exists("project_handoff.md", project_handoff)

    failures += check_conversation_mode()
    failures += check_guidance_words()

    failures += check_words(
        "run_ver1_checks.py",
        run_ver1_checks,
        [
            "check_ver130.py",
            "check_ver120.py",
            "check_ver110.py",
            "All Ver1 checks passed",
        ],
    )

    failures += check_words(
        "conversation_quality.md",
        conversation_quality_doc,
        [
            "会話品質",
            "短めで自然",
            "Memory",
            "Preference",
            "結論",
            "手順",
            "断定しない",
            "実行していないことを実行したと言わない",
            "未実装",
        ],
    )

    failures += check_imports()

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
