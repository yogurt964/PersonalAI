import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


def check_file_exists(label, path):
    if path.exists():
        print(f"[OK] {label} exists")
        return 0

    print(f"[NG] {label} missing -> {path}")
    return 1


def check_true(label, condition):
    if condition:
        print(f"[OK] {label}")
        return 0

    print(f"[NG] {label}")
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


def get_db_timestamp():
    db_path = PROJECT_ROOT / "data" / "personal_ai.db"
    return db_path.stat().st_mtime_ns if db_path.exists() else None


def check_db_unchanged(before):
    after = get_db_timestamp()
    return check_true("check_ver2530 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2530.py").read_text(encoding="utf-8")
    forbidden_words = [
        "req" + "uests.get",
        "req" + "uests.post",
        "ask_" + "llm(",
        "Base.metadata." + "create_all(bind=engine)",
        "create_" + "database(",
        "reset --" + "hard",
        "force " + "push",
        "re" + "base",
    ]
    found_words = [word for word in forbidden_words if word in source]

    if found_words:
        print(f"[NG] check_ver2530 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2530 has no forbidden words")
    return 0


def check_imports():
    try:
        from core.memory_management import (
            build_memory_delete_confirmation,
            build_memory_delete_result_response,
            build_memory_list_response,
            resolve_memory_delete_confirmation_response,
        )
        from core.memory_management_intent import (
            detect_memory_delete_request,
            detect_memory_list_request,
        )
        from core.personal_ai import PersonalAI
    except Exception as error:
        print(f"[NG] imports failed -> {error}")
        return 1

    build_memory_delete_confirmation
    build_memory_delete_result_response
    build_memory_list_response
    resolve_memory_delete_confirmation_response
    detect_memory_delete_request
    detect_memory_list_request
    PersonalAI

    print("[OK] imports")
    return 0


def check_intent_detection():
    from core.memory_management_intent import detect_memory_delete_request, detect_memory_list_request

    failures = 0
    failures += check_true("list intent detected", detect_memory_list_request("覚えていることを見せて") is True)
    failures += check_true("list intent detected (alt phrase)", detect_memory_list_request("記憶一覧") is True)
    failures += check_true("non-list input not detected", detect_memory_list_request("こんにちは") is False)

    delete_with_id = detect_memory_delete_request("3番の記憶を削除して")
    failures += check_true("delete intent detected with id", delete_with_id["is_delete_request"] is True)
    failures += check_true("delete id extracted correctly", delete_with_id["memory_id"] == 3)

    delete_no_id = detect_memory_delete_request("この記憶を削除して")
    failures += check_true("delete intent detected without id", delete_no_id["is_delete_request"] is True)
    failures += check_true("delete id is None when absent", delete_no_id["memory_id"] is None)

    unrelated_delete = detect_memory_delete_request("このファイルを削除して")
    failures += check_true(
        "unrelated delete request (no memory reference) does not trigger",
        unrelated_delete["is_delete_request"] is False,
    )

    return failures


def check_persistence_against_isolated_db():
    """本番DBには一切触れず、独立したin-memory SQLiteで実際のMemory管理のSQL動作を検証する。"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from database.models import Base
    import database.memory_manager as memory_manager_module

    temp_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=temp_engine)
    temp_session_factory = sessionmaker(autocommit=False, autoflush=False, bind=temp_engine)

    original_session_local = memory_manager_module.SessionLocal
    memory_manager_module.SessionLocal = temp_session_factory

    failures = 0

    try:
        memory_manager_module.save_memory(
            "好きな食べ物はカレーです",
            "preference",
            "favorite_food",
            6,
            "test",
            memory_key="favorite_food",
        )
        memory_manager_module.save_memory(
            "プロジェクトXの進捗メモ",
            "project",
            "project",
            7,
            "test",
        )

        memories = memory_manager_module.get_memories(limit=20)
        failures += check_true("isolated db has 2 memories", len(memories) == 2)

        from core.memory_management import build_memory_list_response

        list_text = build_memory_list_response(memories)
        failures += check_true("list response includes both contents", "好きな食べ物" in list_text and "プロジェクトX" in list_text)
        failures += check_true("list response includes ids", f"[{memories[0].id}]" in list_text)

        target_id = memories[0].id
        fetched = memory_manager_module.get_memory_by_id(target_id)
        failures += check_true("get_memory_by_id returns correct memory", fetched.id == target_id)

        deactivated = memory_manager_module.set_memory_active(target_id, False)
        failures += check_true("set_memory_active deactivates", deactivated.is_active is False)

        remaining_active = memory_manager_module.get_memories(limit=20, active_only=True)
        failures += check_true("deactivated memory excluded from active list", len(remaining_active) == 1)
    finally:
        memory_manager_module.SessionLocal = original_session_local

    failures += check_true(
        "production SessionLocal restored (isolation cleanup verified)",
        memory_manager_module.SessionLocal is original_session_local,
    )

    return failures


def _build_lightweight_personal_ai(fake_get_memories, fake_get_memory_by_id):
    from core.capability_manager import CapabilityManager
    from core.input_analyzer import InputAnalyzer
    import core.personal_ai as personal_ai_module
    from core.personal_ai import PersonalAI

    ai = PersonalAI.__new__(PersonalAI)
    ai.input_analyzer = InputAnalyzer()
    ai.capability_manager = CapabilityManager()
    ai.web_reader_fetcher = None
    ai.ask_llm_func = None
    ai.tool_registry = ai.build_tool_registry(None)
    ai.pending_memory_delete_confirmation = None

    for attr in [
        "pending_preference_confirmation",
        "pending_memory_candidate_confirmation",
        "pending_memory_candidate_edit",
        "pending_web_reader_confirmation",
        "pending_file_reader_confirmation",
        "pending_pdf_reader_confirmation",
        "pending_word_reader_confirmation",
        "pending_excel_reader_confirmation",
        "pending_pptx_reader_confirmation",
        "pending_youtube_reader_confirmation",
        "pending_image_reader_confirmation",
    ]:
        setattr(ai, attr, None)

    for prefix in [
        "web_reader",
        "file_reader",
        "pdf_reader",
        "word_reader",
        "excel_reader",
        "pptx_reader",
        "youtube_reader",
        "image_reader",
    ]:
        setattr(ai, f"last_{prefix}_confirmation", None)

    ai.last_read_document = None
    ai.last_tool_execution_record = None
    ai.last_memory_usage = "normal"
    ai.last_conversation_mode = "chat"
    ai.last_conversation_quality_guidance = None
    ai.last_input_analysis = None
    ai.last_response = None
    ai.save_user_message = lambda _message: None
    ai.save_assistant_message = lambda _message: None

    # personal_ai.py内で使われるget_memories/get_memory_by_idをfakeへ差し替える
    # （本番DBには一切触れない）。
    personal_ai_module.get_memories = fake_get_memories
    personal_ai_module.get_memory_by_id = fake_get_memory_by_id

    return ai


class _FakeMemory:
    def __init__(self, memory_id, content, category="favorite_food", importance=6):
        self.id = memory_id
        self.content = content
        self.category = category
        self.importance = importance
        self.is_active = True


def check_personal_ai_flow():
    fake_memories = [_FakeMemory(1, "好きな食べ物はカレーです")]

    def fake_get_memories(limit=20, **kwargs):
        return list(fake_memories)

    def fake_get_memory_by_id(memory_id, include_inactive=True):
        for memory in fake_memories:
            if memory.id == memory_id:
                return memory
        return None

    failures = 0

    ai_list = _build_lightweight_personal_ai(fake_get_memories, fake_get_memory_by_id)
    list_response = ai_list.handle_user_input("覚えていることを見せて")
    failures += check_true("list response shows memory content", "好きな食べ物" in list_response)
    failures += check_true("list response shows id", "[1]" in list_response)

    ai_delete = _build_lightweight_personal_ai(fake_get_memories, fake_get_memory_by_id)
    deactivate_calls = []
    ai_delete.memory_deactivator = lambda memory_id, is_active: deactivate_calls.append((memory_id, is_active)) or _FakeMemory(memory_id, "好きな食べ物はカレーです")
    confirmation_response = ai_delete.handle_user_input("1番の記憶を削除して")
    delete_response = ai_delete.handle_user_input("はい")
    failures += check_true("delete confirmation shown", "削除してもよいですか" in confirmation_response)
    failures += check_true("delete executed after confirm", deactivate_calls == [(1, False)])
    failures += check_true("delete result reported", "削除しました" in delete_response)
    failures += check_true("pending cleared after delete", ai_delete.pending_memory_delete_confirmation is None)

    ai_cancel = _build_lightweight_personal_ai(fake_get_memories, fake_get_memory_by_id)
    cancel_deactivate_calls = []
    ai_cancel.memory_deactivator = lambda memory_id, is_active: cancel_deactivate_calls.append((memory_id, is_active))
    ai_cancel.handle_user_input("1番の記憶を削除して")
    cancel_response = ai_cancel.handle_user_input("キャンセル")
    failures += check_true("cancel not executed", "削除しませんでした" in cancel_response)
    failures += check_true("cancel calls no deactivator", cancel_deactivate_calls == [])
    failures += check_true("cancel pending cleared", ai_cancel.pending_memory_delete_confirmation is None)

    ai_missing_id = _build_lightweight_personal_ai(fake_get_memories, fake_get_memory_by_id)
    missing_id_response = ai_missing_id.handle_user_input("この記憶を削除して")
    failures += check_true(
        "missing id asks for clarification and creates no pending",
        "番号が分かりませんでした" in missing_id_response
        and ai_missing_id.pending_memory_delete_confirmation is None,
    )

    ai_nonexistent = _build_lightweight_personal_ai(fake_get_memories, fake_get_memory_by_id)
    nonexistent_response = ai_nonexistent.handle_user_input("999番の記憶を削除して")
    failures += check_true("nonexistent id reports not found", "見つかりませんでした" in nonexistent_response)

    ai_unrelated = _build_lightweight_personal_ai(fake_get_memories, fake_get_memory_by_id)
    unrelated_response = ai_unrelated.handle_user_input("このファイルを削除して")
    failures += check_true(
        "unrelated file-delete request does not trigger memory deletion",
        ai_unrelated.pending_memory_delete_confirmation is None,
    )

    return failures


def check_legacy_test_double_without_memory_deactivator():
    """memory_deactivator属性を持たない（Ver2.53以前の）test doubleでも
    例外を起こさないことを確認する。
    """
    fake_memories = [_FakeMemory(1, "好きな食べ物はカレーです")]

    def fake_get_memories(limit=20, **kwargs):
        return list(fake_memories)

    def fake_get_memory_by_id(memory_id, include_inactive=True):
        for memory in fake_memories:
            if memory.id == memory_id:
                return memory
        return None

    ai = _build_lightweight_personal_ai(fake_get_memories, fake_get_memory_by_id)
    # 意図的にmemory_deactivatorを設定しない。

    ai.handle_user_input("1番の記憶を削除して")

    try:
        response = ai.handle_pending_memory_delete_confirmation("はい")
    except AttributeError as error:
        print(f"[NG] legacy test double without memory_deactivator raised AttributeError -> {error}")
        return 1

    return check_true(
        "legacy test double without memory_deactivator reports unavailable instead of crashing",
        response is not None and "実行できません" in response,
    )


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"
    core = PROJECT_ROOT / "core"

    files = [
        ("memory_management.py", core / "memory_management.py"),
        ("memory_management_intent.py", core / "memory_management_intent.py"),
        ("confirmation_intent.py", core / "confirmation_intent.py"),
        ("personal_ai.py", core / "personal_ai.py"),
        ("check_ver2530.py", scripts / "check_ver2530.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_imports()
    failures += check_intent_detection()
    failures += check_persistence_against_isolated_db()
    failures += check_personal_ai_flow()
    failures += check_legacy_test_double_without_memory_deactivator()

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
            "check_ver2530.py",
        ],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        [
            "## Version 2.53",
            "scripts/check_ver2530.py",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        [
            "現在バージョン:",
            "Ver2.53:",
        ],
    )

    failures += check_check_script_has_no_forbidden_words()
    failures += check_db_unchanged(db_timestamp_before)

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
