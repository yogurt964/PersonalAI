import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import or_

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from database.memory_manager import save_memory, get_memory_by_id, set_memory_active
from database.models import Memory, SessionLocal


TEST_MARK = "ver017_test"
TEST_MEMORY_KEY = "ver017_test_memory_status"


def cleanup_test_memories():
    """Ver0.17確認用データだけを削除します。ユーザー記憶には触りません。"""
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
    print("[OK] imports")
    return 0


def check_manage_script_exists():
    script_path = PROJECT_ROOT / "scripts" / "manage_memory_status.py"

    if not script_path.exists():
        print("[NG] scripts/manage_memory_status.py does not exist")
        return 1

    print("[OK] manage_memory_status.py exists")
    return 0


def create_test_memory():
    save_memory(
        "Ver0.17 test memory",
        "test",
        "other",
        5,
        TEST_MARK,
        TEST_MARK,
        memory_key=TEST_MEMORY_KEY,
        scope="test",
        confidence=80,
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


def run_manage_memory_status(args):
    script_path = PROJECT_ROOT / "scripts" / "manage_memory_status.py"
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    return subprocess.run(
        [
            sys.executable,
            "-B",
            str(script_path),
            *args,
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )


def check_dry_run(memory_id):
    before_memory = get_memory_by_id(memory_id, include_inactive=True)
    result = run_manage_memory_status(
        ["--id", str(memory_id), "--deactivate"]
    )
    after_memory = get_memory_by_id(memory_id, include_inactive=True)

    if result.returncode != 0:
        print("[NG] dry-run command failed")
        print(result.stderr)
        return 1

    if "dry-run" not in result.stdout:
        print("[NG] dry-run output missing dry-run message")
        return 1

    if before_memory.is_active != after_memory.is_active:
        print("[NG] dry-run changed DB")
        return 1

    print("[OK] dry-run does not change DB")
    return 0


def check_deactivate_apply(memory_id):
    result = run_manage_memory_status(
        ["--id", str(memory_id), "--deactivate", "--apply"]
    )
    memory = get_memory_by_id(memory_id, include_inactive=True)

    if result.returncode != 0:
        print("[NG] deactivate apply command failed")
        print(result.stderr)
        return 1

    if memory.is_active is not False and memory.is_active != 0:
        print(f"[NG] deactivate apply is_active -> {memory.is_active}")
        return 1

    print("[OK] deactivate apply sets is_active=False")
    return 0


def check_restore_apply(memory_id):
    result = run_manage_memory_status(
        ["--id", str(memory_id), "--restore", "--apply"]
    )
    memory = get_memory_by_id(memory_id, include_inactive=True)

    if result.returncode != 0:
        print("[NG] restore apply command failed")
        print(result.stderr)
        return 1

    if memory.is_active is not True and memory.is_active != 1:
        print(f"[NG] restore apply is_active -> {memory.is_active}")
        return 1

    print("[OK] restore apply sets is_active=True")
    return 0


def main():
    failures = 0

    failures += check_imports()
    failures += check_manage_script_exists()

    cleanup_test_memories()

    try:
        test_memory = create_test_memory()

        if test_memory is None:
            print("[NG] test memory was not created")
            failures += 1
        else:
            print("[OK] test memory created")
            failures += check_dry_run(test_memory.id)
            failures += check_deactivate_apply(test_memory.id)
            failures += check_restore_apply(test_memory.id)
    finally:
        cleanup_test_memories()

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
