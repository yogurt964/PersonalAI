import sys
from pathlib import Path
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from ai.memory_context import build_memory_context


def build_dummy_memory(
    content,
    category,
    importance=5,
    confidence=80,
    scope="global",
    memory_key=None,
    is_active=True,
):
    return SimpleNamespace(
        content=content,
        category=category,
        importance=importance,
        confidence=confidence,
        scope=scope,
        memory_key=memory_key,
        is_active=is_active,
        updated_at="2026-06-30T10:00:00",
        created_at="2026-06-30T09:00:00",
    )


def check_contains(label, text, expected):
    if expected not in text:
        print(f"[NG] {label} -> missing: {expected}")
        return 1

    print(f"[OK] {label}")
    return 0


def check_not_contains(label, text, unexpected):
    if unexpected in text:
        print(f"[NG] {label} -> unexpected: {unexpected}")
        return 1

    print(f"[OK] {label}")
    return 0


def check_empty_memories():
    context = build_memory_context([])

    failures = 0

    if not isinstance(context, str):
        print(f"[NG] empty memories return type -> {type(context)}")
        return 1

    failures += check_contains("empty memories has title", context, "長期記憶")
    failures += check_contains(
        "empty memories has no-memory message",
        context,
        "現在、利用できる長期記憶はありません。",
    )

    return failures


def check_category_sections():
    memories = [
        build_dummy_memory("ユーザーの名前は巧弥", "name", 10, 90),
        build_dummy_memory("ユーザーは安全確認を重視する", "preference", 8, 80),
        build_dummy_memory("PersonalAIはVer0.14を開発中", "project", 9, 90),
        build_dummy_memory("ユーザーはMemoryContext強化を進めている", "current_activity", 8, 80),
        build_dummy_memory("PersonalAIはPythonで実装されている", "knowledge", 7, 80),
        build_dummy_memory("その他の補足記憶", "other", 5, 80),
    ]

    context = build_memory_context(memories)

    failures = 0
    failures += check_contains("name goes to user section", context, "【ユーザー情報】")
    failures += check_contains("name content", context, "ユーザーの名前は巧弥")
    failures += check_contains("preference goes to preference section", context, "【好み・方針】")
    failures += check_contains("preference content", context, "ユーザーは安全確認を重視する")
    failures += check_contains("project goes to project section", context, "【プロジェクト】")
    failures += check_contains("project content", context, "PersonalAIはVer0.14を開発中")
    failures += check_contains("activity goes to current section", context, "【現在の作業】")
    failures += check_contains("activity content", context, "MemoryContext強化")
    failures += check_contains("knowledge goes to knowledge section", context, "【知識】")
    failures += check_contains("knowledge content", context, "Pythonで実装")
    failures += check_contains("other goes to other section", context, "【その他】")
    failures += check_contains("other content", context, "その他の補足記憶")

    return failures


def check_inactive_memory_is_excluded():
    memories = [
        build_dummy_memory("表示される記憶", "other"),
        build_dummy_memory("表示されてはいけない記憶", "other", is_active=False),
    ]

    context = build_memory_context(memories)

    failures = 0
    failures += check_contains("active memory is included", context, "表示される記憶")
    failures += check_not_contains(
        "inactive memory is excluded",
        context,
        "表示されてはいけない記憶",
    )

    return failures


def check_confidence_is_shown():
    memory = build_dummy_memory(
        "ユーザーは低確信テストを好む可能性がある",
        "preference",
        importance=6,
        confidence=40,
    )

    context = build_memory_context([memory])

    failures = 0
    failures += check_contains("importance value is shown", context, "重要度:6")
    failures += check_contains("confidence value is shown", context, "確信度:40")
    failures += check_contains("low confidence label is shown", context, "低確信")

    return failures


def check_scope_and_memory_key_are_shown():
    memory = build_dummy_memory(
        "PersonalAIの主プロジェクト記憶",
        "other",
        importance=9,
        confidence=90,
        scope="project",
        memory_key="main_project",
    )

    context = build_memory_context([memory])

    failures = 0
    failures += check_contains("project scope chooses project section", context, "【プロジェクト】")
    failures += check_contains("scope is shown", context, "範囲:project")
    failures += check_contains("memory_key is shown", context, "key:main_project")

    return failures


def main():
    failures = 0

    failures += check_empty_memories()
    failures += check_category_sections()
    failures += check_inactive_memory_is_excluded()
    failures += check_confidence_is_shown()
    failures += check_scope_and_memory_key_are_shown()

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
