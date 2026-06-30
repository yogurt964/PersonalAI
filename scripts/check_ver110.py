import sys
from pathlib import Path
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from ai.memory_context import build_memory_context
from ai.memory_usage_policy import decide_memory_usage


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


def check_not_contains(label, text, unexpected):
    if unexpected not in text:
        print(f"[OK] {label}")
        return 0

    print(f"[NG] {label} -> unexpected: {unexpected}")
    return 1


def check_memory_usage_decisions():
    failures = 0

    failures += check_equal(
        "こんにちは -> minimal",
        decide_memory_usage("こんにちは"),
        "minimal",
    )
    failures += check_equal(
        "短く応援してください -> minimal",
        decide_memory_usage("短く応援してください"),
        "minimal",
    )
    failures += check_equal(
        "私について覚えていること -> detailed",
        decide_memory_usage("私について覚えていることを教えてください"),
        "detailed",
    )
    failures += check_equal(
        "何を覚えてる？ -> detailed",
        decide_memory_usage("何を覚えてる？"),
        "detailed",
    )
    failures += check_equal(
        "提案 -> normal",
        decide_memory_usage("私に合いそうなものを提案して"),
        "normal",
    )

    return failures


def check_memory_context_guidance():
    memory_context_file = PROJECT_ROOT / "ai" / "memory_context.py"
    text = memory_context_file.read_text(encoding="utf-8")

    failures = 0
    failures += check_contains(
        "MemoryContext says minimal",
        text,
        "通常会話ではMemoryを控えめに使う",
    )
    failures += check_contains(
        "MemoryContext says no repeated preference",
        text,
        "Preference情報を毎回話題に出さない",
    )
    failures += check_contains(
        "MemoryContext says detailed reference",
        text,
        "ユーザーが明示的に記憶参照を求めた場合は詳しく使う",
    )

    minimal_context = build_memory_context(
        [
            build_dummy_memory("ユーザーの名前は巧弥", "name"),
            build_dummy_memory(
                "ユーザーはカレーが好き",
                "preference",
                memory_key="preference:food:カレー",
            ),
        ],
        memory_usage="minimal",
    )
    detailed_context = build_memory_context(
        [
            build_dummy_memory("ユーザーの名前は巧弥", "name"),
            build_dummy_memory(
                "ユーザーはカレーが好き",
                "preference",
                memory_key="preference:food:カレー",
            ),
        ],
        memory_usage="detailed",
    )

    failures += check_not_contains(
        "minimal context hides preference detail",
        minimal_context,
        "カレー",
    )
    failures += check_contains(
        "detailed context keeps preference detail",
        detailed_context,
        "カレー",
    )

    return failures


def build_dummy_memory(content, category, memory_key=None):
    return SimpleNamespace(
        content=content,
        category=category,
        importance=8,
        confidence=90,
        scope="global",
        memory_key=memory_key,
        is_active=True,
        updated_at="2026-07-01T10:00:00",
        created_at="2026-07-01T09:00:00",
    )


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

    failures += check_file_exists(
        "memory_usage_policy.py",
        PROJECT_ROOT / "ai" / "memory_usage_policy.py",
    )
    failures += check_file_exists(
        "check_ver110.py",
        PROJECT_ROOT / "scripts" / "check_ver110.py",
    )
    failures += check_memory_usage_decisions()
    failures += check_memory_context_guidance()
    failures += check_imports()

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
