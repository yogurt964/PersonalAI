import sys
from pathlib import Path

from sqlalchemy import or_

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from ai.memory_context import build_memory_context
from database.memory_manager import (
    get_memories,
    get_memory_by_id,
    save_memory,
    set_memory_active,
)
from database.models import Memory, SessionLocal


TEST_CONTENT = "Ver0.18 inactive memory context test"
TEST_MARK = "ver018_test"
TEST_MEMORY_KEY = "ver018_memory_context_active_test"


def cleanup_test_memories():
    """Ver0.18確認用データだけを削除します。ユーザー記憶には触りません。"""
    db = SessionLocal()

    try:
        db.query(Memory).filter(
            or_(
                Memory.source == TEST_MARK,
                Memory.tags == TEST_MARK,
                Memory.tags.like(f"%{TEST_MARK}%"),
                Memory.memory_key == TEST_MEMORY_KEY,
            )
        ).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


def check_imports():
    save_memory
    get_memory_by_id
    set_memory_active
    get_memories
    build_memory_context
    print("[OK] imports")
    return 0


def create_test_memory():
    save_memory(
        TEST_CONTENT,
        "test",
        "project",
        9,
        TEST_MARK,
        TEST_MARK,
        memory_key=TEST_MEMORY_KEY,
        scope="project",
        confidence=90,
    )

    db = SessionLocal()

    try:
        memory = (
            db.query(Memory)
            .filter(Memory.memory_key == TEST_MEMORY_KEY)
            .filter(Memory.source == TEST_MARK)
            .first()
        )

        if memory is None:
            return None

        memory_id = memory.id
    finally:
        db.close()

    return get_memory_by_id(memory_id, include_inactive=True)


def memory_context_from_active_memories():
    memories = get_memories(limit=50, active_only=True)
    return memories, build_memory_context(memories)


def contains_test_memory(memories):
    return any(getattr(memory, "content", "") == TEST_CONTENT for memory in memories)


def check_active_memory_is_in_context(memory_id):
    memory = get_memory_by_id(memory_id, include_inactive=False)

    if memory is None:
        print("[NG] active memory was not found by get_memory_by_id")
        return 1

    memories, context = memory_context_from_active_memories()

    if not contains_test_memory(memories):
        print("[NG] active memory was not returned by get_memories(active_only=True)")
        return 1

    if TEST_CONTENT not in context:
        print("[NG] active memory was not included in MemoryContext")
        return 1

    print("[OK] active memory is included in MemoryContext")
    return 0


def check_inactive_memory_is_excluded(memory_id):
    set_memory_active(memory_id, False)
    inactive_memory = get_memory_by_id(memory_id, include_inactive=True)

    if inactive_memory is None:
        print("[NG] inactive memory was not found with include_inactive=True")
        return 1

    if inactive_memory.is_active is not False and inactive_memory.is_active != 0:
        print(f"[NG] memory was not deactivated -> {inactive_memory.is_active}")
        return 1

    memories, context = memory_context_from_active_memories()

    if contains_test_memory(memories):
        print("[NG] inactive memory was returned by get_memories(active_only=True)")
        return 1

    if TEST_CONTENT in context:
        print("[NG] inactive memory was included in MemoryContext")
        return 1

    direct_context = build_memory_context([inactive_memory])

    if TEST_CONTENT in direct_context:
        print("[NG] direct inactive memory was included in MemoryContext")
        return 1

    print("[OK] inactive memory is excluded from MemoryContext")
    return 0


def check_restored_memory_returns_to_context(memory_id):
    set_memory_active(memory_id, True)
    restored_memory = get_memory_by_id(memory_id, include_inactive=True)

    if restored_memory is None:
        print("[NG] restored memory was not found")
        return 1

    if restored_memory.is_active is not True and restored_memory.is_active != 1:
        print(f"[NG] memory was not restored -> {restored_memory.is_active}")
        return 1

    memories, context = memory_context_from_active_memories()

    if not contains_test_memory(memories):
        print("[NG] restored memory was not returned by get_memories(active_only=True)")
        return 1

    if TEST_CONTENT not in context:
        print("[NG] restored memory was not included in MemoryContext")
        return 1

    print("[OK] restored memory returns to MemoryContext")
    return 0


def main():
    failures = 0

    failures += check_imports()
    cleanup_test_memories()

    try:
        test_memory = create_test_memory()

        if test_memory is None:
            print("[NG] test memory was not created")
            failures += 1
        else:
            print("[OK] test memory created")
            failures += check_active_memory_is_in_context(test_memory.id)
            failures += check_inactive_memory_is_excluded(test_memory.id)
            failures += check_restored_memory_returns_to_context(test_memory.id)
    finally:
        cleanup_test_memories()

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
