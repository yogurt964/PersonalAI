import sys
from pathlib import Path

from sqlalchemy import or_, text

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.personal_ai import PersonalAI
from database.memory_manager import save_memory
from database.models import Memory, SessionLocal, create_database, engine


TEST_MARK = "ver013_test"


def cleanup_test_memories():
    """Ver0.13確認用データだけを削除し、ユーザーの記憶には触りません。"""
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


def check_personal_ai_import():
    PersonalAI
    print("[OK] PersonalAI import")


def check_memory_columns():
    required_columns = {
        "memory_key",
        "subcategory",
        "scope",
        "confidence",
        "updated_at",
        "expires_at",
        "is_active",
    }

    with engine.connect() as connection:
        existing_columns = {
            row[1]
            for row in connection.execute(text("PRAGMA table_info(memories)")).fetchall()
        }

    missing_columns = required_columns - existing_columns

    if missing_columns:
        print(f"[NG] missing columns -> {sorted(missing_columns)}")
        return 1

    print("[OK] memories table has Ver0.13 columns")
    return 0


def check_old_style_save_memory():
    content = "Ver0.13 test old style memory"

    saved = save_memory(
        content,
        "test",
        "other",
        5,
        TEST_MARK,
        TEST_MARK,
    )

    db = SessionLocal()

    try:
        memory = (
            db.query(Memory)
            .filter(Memory.content == content)
            .filter(Memory.source == TEST_MARK)
            .first()
        )
    finally:
        db.close()

    if not saved or memory is None:
        print("[NG] old style save_memory did not save test memory")
        return 1

    print("[OK] old style save_memory works")
    return 0


def check_memory_key_update():
    memory_key = "ver013_test_key"

    save_memory(
        "Ver0.13 memory key update A",
        "test",
        "preference",
        5,
        TEST_MARK,
        TEST_MARK,
        memory_key=memory_key,
        scope="global",
        confidence=70,
    )
    save_memory(
        "Ver0.13 memory key update B",
        "test",
        "preference",
        7,
        TEST_MARK,
        TEST_MARK,
        memory_key=memory_key,
        scope="global",
        confidence=90,
    )

    db = SessionLocal()

    try:
        memories = (
            db.query(Memory)
            .filter(Memory.memory_key == memory_key)
            .filter(Memory.scope == "global")
            .all()
        )
    finally:
        db.close()

    if len(memories) != 1:
        print(f"[NG] memory_key update count -> expected 1, got {len(memories)}")
        return 1

    memory = memories[0]

    if memory.content != "Ver0.13 memory key update B":
        print(f"[NG] memory_key update content -> {memory.content}")
        return 1

    if memory.confidence != 90:
        print(f"[NG] memory_key update confidence -> {memory.confidence}")
        return 1

    print("[OK] memory_key update keeps one record")
    return 0


def check_multi_category_without_memory_key():
    save_memory(
        "Ver0.13 project memory A",
        "test",
        "project",
        5,
        TEST_MARK,
        TEST_MARK,
    )
    save_memory(
        "Ver0.13 project memory B",
        "test",
        "project",
        5,
        TEST_MARK,
        TEST_MARK,
    )

    db = SessionLocal()

    try:
        memories = (
            db.query(Memory)
            .filter(Memory.memory_type == "test")
            .filter(Memory.category == "project")
            .filter(Memory.source == TEST_MARK)
            .all()
        )
    finally:
        db.close()

    if len(memories) != 2:
        print(f"[NG] project memories without key -> expected 2, got {len(memories)}")
        return 1

    print("[OK] project category keeps multiple records without memory_key")
    return 0


def main():
    failures = 0

    create_database()
    cleanup_test_memories()

    try:
        check_personal_ai_import()
        failures += check_memory_columns()
        failures += check_old_style_save_memory()
        failures += check_memory_key_update()
        failures += check_multi_category_without_memory_key()
    finally:
        cleanup_test_memories()

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
