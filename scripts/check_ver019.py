import sys
from pathlib import Path

from sqlalchemy import or_

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from ai.memory_context import build_memory_context
from ai.preference_memory import extract_preference_memories, save_preference_memories
from database.memory_manager import get_memories
from database.models import Memory, SessionLocal


TEST_MARK = "ver019_test"
RAMEN_KEY = "preference:food:ラーメン"
SUSHI_KEY = "preference:food:寿司"


def cleanup_test_memories():
    """Ver0.19確認用データだけを削除します。ユーザー記憶には触りません。"""
    db = SessionLocal()

    try:
        db.query(Memory).filter(
            or_(
                Memory.source == TEST_MARK,
                Memory.tags == TEST_MARK,
                Memory.tags.like(f"%{TEST_MARK}%"),
            )
        ).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


def check_imports():
    extract_preference_memories
    save_preference_memories
    get_memories
    build_memory_context
    print("[OK] imports")
    return 0


def check_extract(label, text, expected_target, expected_polarity):
    preferences = extract_preference_memories(text)

    if len(preferences) != 1:
        print(f"[NG] {label} extract count -> expected 1, got {len(preferences)}")
        return 1

    preference = preferences[0]

    if preference["target"] != expected_target:
        print(f"[NG] {label} target -> {preference['target']}")
        return 1

    if preference["polarity"] != expected_polarity:
        print(f"[NG] {label} polarity -> {preference['polarity']}")
        return 1

    print(f"[OK] {label} extract")
    return 0


def get_test_memory(memory_key):
    db = SessionLocal()

    try:
        memory = (
            db.query(Memory)
            .filter(Memory.memory_key == memory_key)
            .filter(Memory.source == TEST_MARK)
            .first()
        )

        if memory is None:
            return None

        db.expunge(memory)
        return memory
    finally:
        db.close()


def get_test_memories():
    db = SessionLocal()

    try:
        memories = (
            db.query(Memory)
            .filter(Memory.source == TEST_MARK)
            .order_by(Memory.memory_key.asc())
            .all()
        )

        for memory in memories:
            db.expunge(memory)

        return memories
    finally:
        db.close()


def has_user_memory_conflict():
    db = SessionLocal()

    try:
        memory = (
            db.query(Memory)
            .filter(Memory.memory_key.in_([RAMEN_KEY, SUSHI_KEY]))
            .filter(Memory.source != TEST_MARK)
            .first()
        )

        return memory is not None
    finally:
        db.close()


def check_save_multiple_likes():
    save_preference_memories(
        "ラーメンが好きです。覚えて",
        source=TEST_MARK,
        tags=TEST_MARK,
    )
    save_preference_memories(
        "寿司が好きです。覚えて",
        source=TEST_MARK,
        tags=TEST_MARK,
    )

    ramen_memory = get_test_memory(RAMEN_KEY)
    sushi_memory = get_test_memory(SUSHI_KEY)

    if ramen_memory is None or sushi_memory is None:
        print("[NG] multiple likes were not saved")
        return 1

    memories = get_test_memories()
    context = build_memory_context(memories)

    if "ユーザーはラーメンが好きです。" not in context:
        print("[NG] ramen like is missing from MemoryContext")
        return 1

    if "ユーザーは寿司が好きです。" not in context:
        print("[NG] sushi like is missing from MemoryContext")
        return 1

    print("[OK] multiple likes are saved and shown")
    return 0


def check_not_like_update():
    save_preference_memories(
        "ラーメンは好きじゃないです。覚えて",
        source=TEST_MARK,
        tags=TEST_MARK,
    )

    ramen_memory = get_test_memory(RAMEN_KEY)

    if ramen_memory is None:
        print("[NG] ramen memory was not found after not_like update")
        return 1

    if "好きではありません" not in ramen_memory.content:
        print(f"[NG] ramen content was not updated -> {ramen_memory.content}")
        return 1

    memories = get_test_memories()
    context = build_memory_context(memories)

    if "ユーザーはラーメンが好きです。" in context:
        print("[NG] old ramen like remains in MemoryContext")
        return 1

    if "ユーザーはラーメンが好きではありません。" not in context:
        print("[NG] ramen not_like is missing from MemoryContext")
        return 1

    print("[OK] not_like updates existing preference")
    return 0


def check_dislike_update():
    save_preference_memories(
        "寿司は嫌いです。覚えて",
        source=TEST_MARK,
        tags=TEST_MARK,
    )

    sushi_memory = get_test_memory(SUSHI_KEY)

    if sushi_memory is None:
        print("[NG] sushi memory was not found after dislike update")
        return 1

    if "嫌いです" not in sushi_memory.content:
        print(f"[NG] sushi content was not updated -> {sushi_memory.content}")
        return 1

    memories = get_test_memories()
    context = build_memory_context(memories)

    if "ユーザーは寿司が好きです。" in context:
        print("[NG] old sushi like remains in MemoryContext")
        return 1

    if "ユーザーは寿司が嫌いです。" not in context:
        print("[NG] sushi dislike is missing from MemoryContext")
        return 1

    print("[OK] dislike updates existing preference")
    return 0


def main():
    failures = 0

    failures += check_imports()
    failures += check_extract(
        "ramen like",
        "ラーメンが好きです。覚えて",
        "ラーメン",
        "like",
    )
    failures += check_extract(
        "sushi like",
        "寿司が好きです。覚えて",
        "寿司",
        "like",
    )
    failures += check_extract(
        "ramen not_like",
        "ラーメンは好きじゃないです。覚えて",
        "ラーメン",
        "not_like",
    )
    failures += check_extract(
        "sushi dislike",
        "寿司は嫌いです。覚えて",
        "寿司",
        "dislike",
    )

    cleanup_test_memories()

    try:
        if has_user_memory_conflict():
            print("[NG] existing user preference memory would conflict with test keys")
            failures += 1
        else:
            failures += check_save_multiple_likes()
            failures += check_not_like_update()
            failures += check_dislike_update()
    finally:
        cleanup_test_memories()

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
