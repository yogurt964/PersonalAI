import sys
from pathlib import Path

from sqlalchemy import or_

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from ai.preference_confirmation import (
    analyze_preference_confirmation,
    resolve_preference_confirmation_answer,
    save_resolved_preference_confirmation,
)
from core.personal_ai import PersonalAI
from database.models import Memory, SessionLocal


TEST_MARK = "ver022_test"
PRIMARY_KEY = "preference:food:primary"
YAKINIKU_KEY = "preference:food:焼き肉"
CURRY_KEY = "preference:food:カレー"
TEST_KEYS = [PRIMARY_KEY, YAKINIKU_KEY, CURRY_KEY]


def cleanup_test_memories():
    """Ver0.22確認用データだけを削除します。ユーザー記憶には触りません。"""
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


def has_user_memory_conflict():
    db = SessionLocal()

    try:
        memory = (
            db.query(Memory)
            .filter(Memory.memory_key.in_(TEST_KEYS))
            .filter(or_(Memory.source != TEST_MARK, Memory.source.is_(None)))
            .first()
        )
        return memory is not None
    finally:
        db.close()


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


def check_imports():
    analyze_preference_confirmation
    resolve_preference_confirmation_answer
    save_resolved_preference_confirmation
    PersonalAI
    print("[OK] imports")
    return 0


def check_resolution(label, pending, answer, expected_action, expected_clear):
    resolution = resolve_preference_confirmation_answer(answer, pending)

    if resolution["action"] != expected_action:
        print(f"[NG] {label} action -> expected {expected_action}, got {resolution['action']}")
        return 1

    if resolution["should_clear_pending"] != expected_clear:
        print(
            f"[NG] {label} should_clear_pending -> "
            f"expected {expected_clear}, got {resolution['should_clear_pending']}"
        )
        return 1

    print(f"[OK] {label}")
    return 0


def check_save_primary():
    pending = {
        "type": "preference_confirmation",
        "reason": "primary_preference_update",
        "target": "焼き肉",
        "domain": "food",
    }
    resolution = resolve_preference_confirmation_answer("一番好きとして記憶して", pending)
    save_resolved_preference_confirmation(pending, resolution, source=TEST_MARK, tags=TEST_MARK)
    memory = get_test_memory(PRIMARY_KEY)

    if memory is None:
        print("[NG] primary preference was not saved")
        return 1

    if "一番好きな食べ物" not in memory.content:
        print(f"[NG] primary content -> {memory.content}")
        return 1

    print("[OK] save_primary saves primary preference")
    return 0


def check_save_addition():
    pending = {
        "type": "preference_confirmation",
        "reason": "primary_preference_update",
        "target": "焼き肉",
        "domain": "food",
    }
    resolution = resolve_preference_confirmation_answer("好きなものの1つとして追加して", pending)
    save_resolved_preference_confirmation(pending, resolution, source=TEST_MARK, tags=TEST_MARK)
    memory = get_test_memory(YAKINIKU_KEY)

    if memory is None:
        print("[NG] addition preference was not saved")
        return 1

    if memory.content != "ユーザーは焼き肉が好きです。":
        print(f"[NG] addition content -> {memory.content}")
        return 1

    print("[OK] save_addition saves like preference")
    return 0


def check_save_change():
    pending = {
        "type": "preference_confirmation",
        "reason": "preference_change_request",
        "old_target": "カレー",
        "new_target": "焼き肉",
        "domain": "food",
    }
    resolution = resolve_preference_confirmation_answer("変更して", pending)
    save_resolved_preference_confirmation(pending, resolution, source=TEST_MARK, tags=TEST_MARK)
    new_memory = get_test_memory(YAKINIKU_KEY)
    old_memory = get_test_memory(CURRY_KEY)

    if new_memory is None:
        print("[NG] change new preference was not saved")
        return 1

    if "現在、焼き肉が好き" not in new_memory.content:
        print(f"[NG] change new content -> {new_memory.content}")
        return 1

    if old_memory is None:
        print("[NG] change old preference was not saved")
        return 1

    if "現在の好みとしては優先しません" not in old_memory.content:
        print(f"[NG] change old content -> {old_memory.content}")
        return 1

    print("[OK] save_change saves current and past preference")
    return 0


def check_personal_ai_pending_flow():
    ai = PersonalAI()
    ai.save_user_message = lambda _message: None
    ai.save_assistant_message = lambda _message: None

    first_response = ai.handle_user_input("一番好きな食べ物は焼き肉です。覚えて")

    if "一番好き" not in first_response:
        print(f"[NG] PersonalAI first response -> {first_response}")
        return 1

    if ai.pending_preference_confirmation is None:
        print("[NG] PersonalAI pending was not set")
        return 1

    ask_again_response = ai.handle_user_input("どっちでも")

    if "教えてください" not in ask_again_response:
        print(f"[NG] PersonalAI ask_again response -> {ask_again_response}")
        return 1

    if ai.pending_preference_confirmation is None:
        print("[NG] PersonalAI pending was cleared on ask_again")
        return 1

    cancel_response = ai.handle_user_input("やっぱり記憶しないで")

    if "保存しませんでした" not in cancel_response:
        print(f"[NG] PersonalAI cancel response -> {cancel_response}")
        return 1

    if ai.pending_preference_confirmation is not None:
        print("[NG] PersonalAI pending was not cleared on cancel")
        return 1

    print("[OK] PersonalAI pending flow")
    return 0


def main():
    failures = 0

    failures += check_imports()
    failures += check_resolution(
        "resolve save_primary",
        {
            "type": "preference_confirmation",
            "reason": "primary_preference_update",
            "target": "焼き肉",
            "domain": "food",
        },
        "一番好きとして記憶して",
        "save_primary",
        True,
    )
    failures += check_resolution(
        "resolve save_addition",
        {
            "type": "preference_confirmation",
            "reason": "primary_preference_update",
            "target": "焼き肉",
            "domain": "food",
        },
        "好きなものの1つとして追加して",
        "save_addition",
        True,
    )
    failures += check_resolution(
        "resolve cancel",
        {
            "type": "preference_confirmation",
            "reason": "primary_preference_update",
            "target": "焼き肉",
            "domain": "food",
        },
        "やっぱり記憶しないで",
        "cancel",
        True,
    )
    failures += check_resolution(
        "resolve ask_again",
        {
            "type": "preference_confirmation",
            "reason": "primary_preference_update",
            "target": "焼き肉",
            "domain": "food",
        },
        "どっちでも",
        "ask_again",
        False,
    )
    failures += check_resolution(
        "resolve save_change",
        {
            "type": "preference_confirmation",
            "reason": "preference_change_request",
            "old_target": "カレー",
            "new_target": "焼き肉",
            "domain": "food",
        },
        "変更して",
        "save_change",
        True,
    )

    cleanup_test_memories()

    try:
        if has_user_memory_conflict():
            print("[NG] existing user preference memory would conflict with test keys")
            failures += 1
        else:
            failures += check_save_primary()
            failures += check_save_addition()
            failures += check_save_change()

        failures += check_personal_ai_pending_flow()
    finally:
        cleanup_test_memories()

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
