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
    return check_true("check_ver2610 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2610.py").read_text(encoding="utf-8")
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
        print(f"[NG] check_ver2610 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2610 has no forbidden words")
    return 0


def check_imports():
    try:
        from core.memory_management import (
            build_memory_edit_confirmation,
            build_memory_edit_prompt,
            build_memory_edit_result_response,
            resolve_memory_edit_confirmation_response,
        )
        from core.memory_management_intent import detect_memory_edit_request
        from database.memory_manager import update_memory_content
        from core.personal_ai import PersonalAI
    except Exception as error:
        print(f"[NG] imports failed -> {error}")
        return 1

    build_memory_edit_confirmation
    build_memory_edit_prompt
    build_memory_edit_result_response
    resolve_memory_edit_confirmation_response
    detect_memory_edit_request
    update_memory_content
    PersonalAI

    print("[OK] imports")
    return 0


def check_intent_detection():
    from core.memory_management_intent import detect_memory_edit_request

    failures = 0

    edit_with_id = detect_memory_edit_request("3番の記憶を編集して")
    failures += check_true("edit intent detected with id", edit_with_id["is_edit_request"] is True)
    failures += check_true("edit id extracted correctly", edit_with_id["memory_id"] == 3)

    edit_no_id = detect_memory_edit_request("この記憶を書き換えて")
    failures += check_true("edit intent detected without id", edit_no_id["is_edit_request"] is True)
    failures += check_true("edit id is None when absent", edit_no_id["memory_id"] is None)

    unrelated_edit = detect_memory_edit_request("このファイルを編集して")
    failures += check_true(
        "unrelated edit request (no memory reference) does not trigger",
        unrelated_edit["is_edit_request"] is False,
    )

    return failures


def check_persistence_against_isolated_db():
    """本番DBには一切触れず、独立したin-memory SQLiteでupdate_memory_contentの実SQL動作を検証する。"""
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

        memories = memory_manager_module.get_memories(limit=20)
        target_id = memories[0].id

        updated = memory_manager_module.update_memory_content(target_id, "好きな食べ物はラーメンです")
        failures += check_true("update_memory_content returns updated memory", updated is not None)
        failures += check_true("update_memory_content changes content", updated.content == "好きな食べ物はラーメンです")

        refetched = memory_manager_module.get_memory_by_id(target_id)
        failures += check_true("content change is persisted", refetched.content == "好きな食べ物はラーメンです")

        missing_update = memory_manager_module.update_memory_content(999999, "存在しないはずの内容")
        failures += check_true("update_memory_content returns None for missing id", missing_update is None)
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
    from core.planner import Planner
    from core.router import Router
    from core.permission_manager import PermissionManager
    from core.executor import Executor
    import core.personal_ai as personal_ai_module
    from core.personal_ai import PersonalAI

    ai = PersonalAI.__new__(PersonalAI)
    ai.input_analyzer = InputAnalyzer()
    ai.capability_manager = CapabilityManager()
    # Ver2.62で「このファイルを編集して」のような非読み取り系の発言が
    # capability_managerのfile_read_required判定に誤ってひっかからなくなったため、
    # 通常会話の最後（Executor）まで到達できるよう最小限の実体を用意する
    # （check_personal_ai_edit_flow()側でcore.executor.ask_llmをfakeへ差し替えるため、
    # 実際のQwen呼び出しは発生しない）。
    ai.planner = Planner()
    ai.router = Router()
    ai.permission_manager = PermissionManager()
    ai.executor = Executor()
    ai.web_reader_fetcher = None
    ai.memory_search_func = None
    ai.ask_llm_func = None
    ai.tool_registry = ai.build_tool_registry(None)
    ai.pending_memory_delete_confirmation = None
    ai.pending_memory_edit_input = None
    ai.pending_memory_edit_confirmation = None
    ai.last_saved_memory_candidate_result = None
    ai.last_memory_search_intent = None
    ai.last_memory_search_result = None
    ai.last_capability_analysis = None
    ai.last_capabilities = None
    ai.last_plan = None
    ai.last_route = None
    ai.last_permission_decision = None
    ai.last_preference_confirmation = None
    ai.pending_preference_confirmation = None

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


def check_personal_ai_edit_flow():
    """Ver2.62で「このファイルを編集して」がcapability_manager側で早期には遮られなくなり、
    通常会話（Executor経由のQwen呼び出し）まで到達しうるようになったため、
    ここではcore.executor.ask_llmを一時的にfakeへ差し替え、実際のQwen呼び出しをしない。
    """
    import core.executor as executor_module

    original_ask_llm = executor_module.ask_llm
    executor_module.ask_llm = lambda messages: "FAKE_QWEN_CHAT_RESPONSE"

    try:
        return _check_personal_ai_edit_flow_body()
    finally:
        executor_module.ask_llm = original_ask_llm


def _check_personal_ai_edit_flow_body():
    fake_memories = [_FakeMemory(1, "好きな食べ物はカレーです")]

    def fake_get_memories(limit=20, **kwargs):
        return list(fake_memories)

    def fake_get_memory_by_id(memory_id, include_inactive=True):
        for memory in fake_memories:
            if memory.id == memory_id:
                return memory
        return None

    failures = 0

    # 正常系: 編集依頼 -> 新しい内容 -> 確認 -> 実行
    ai_edit = _build_lightweight_personal_ai(fake_get_memories, fake_get_memory_by_id)
    update_calls = []

    def fake_updater(memory_id, new_content):
        update_calls.append((memory_id, new_content))
        return _FakeMemory(memory_id, new_content)

    ai_edit.memory_content_updater = fake_updater

    prompt_response = ai_edit.handle_user_input("1番の記憶を編集して")
    failures += check_true("edit prompt asks for new content", "編集します" in prompt_response)
    failures += check_true(
        "pending_memory_edit_input is set",
        ai_edit.pending_memory_edit_input is not None
        and ai_edit.pending_memory_edit_input.get("memory_id") == 1,
    )

    confirmation_response = ai_edit.handle_user_input("好きな食べ物はラーメンです")
    failures += check_true("edit confirmation shown", "書き換えてもよいですか" in confirmation_response)
    failures += check_true(
        "pending_memory_edit_input cleared after receiving new content",
        ai_edit.pending_memory_edit_input is None,
    )
    failures += check_true(
        "pending_memory_edit_confirmation is set",
        ai_edit.pending_memory_edit_confirmation is not None,
    )

    edit_result_response = ai_edit.handle_user_input("はい")
    failures += check_true("edit executed after confirm", update_calls == [(1, "好きな食べ物はラーメンです")])
    failures += check_true("edit result reported", "編集しました" in edit_result_response)
    failures += check_true(
        "pending_memory_edit_confirmation cleared after edit",
        ai_edit.pending_memory_edit_confirmation is None,
    )

    # キャンセル系: 内容入力の時点でキャンセル
    ai_cancel_at_input = _build_lightweight_personal_ai(fake_get_memories, fake_get_memory_by_id)
    cancel_calls = []
    ai_cancel_at_input.memory_content_updater = lambda memory_id, new_content: cancel_calls.append(
        (memory_id, new_content)
    )
    ai_cancel_at_input.handle_user_input("1番の記憶を編集して")
    cancel_input_response = ai_cancel_at_input.handle_user_input("キャンセル")
    failures += check_true("cancel at content-input stage reported", "キャンセルしました" in cancel_input_response)
    failures += check_true("cancel at content-input stage calls no updater", cancel_calls == [])
    failures += check_true(
        "no pending confirmation created after cancel at input stage",
        ai_cancel_at_input.pending_memory_edit_confirmation is None,
    )

    # キャンセル系: 確認の時点でキャンセル（いいえ）
    ai_cancel_at_confirm = _build_lightweight_personal_ai(fake_get_memories, fake_get_memory_by_id)
    confirm_cancel_calls = []
    ai_cancel_at_confirm.memory_content_updater = lambda memory_id, new_content: confirm_cancel_calls.append(
        (memory_id, new_content)
    )
    ai_cancel_at_confirm.handle_user_input("1番の記憶を編集して")
    ai_cancel_at_confirm.handle_user_input("好きな食べ物はうどんです")
    confirm_cancel_response = ai_cancel_at_confirm.handle_user_input("いいえ")
    failures += check_true("cancel at confirmation stage reported", "キャンセルしました" in confirm_cancel_response)
    failures += check_true("cancel at confirmation stage calls no updater", confirm_cancel_calls == [])
    failures += check_true(
        "pending confirmation cleared after cancel at confirmation stage",
        ai_cancel_at_confirm.pending_memory_edit_confirmation is None,
    )

    # 番号なし・存在しないID
    ai_missing_id = _build_lightweight_personal_ai(fake_get_memories, fake_get_memory_by_id)
    missing_id_response = ai_missing_id.handle_user_input("この記憶を編集して")
    failures += check_true(
        "missing id asks for clarification and creates no pending",
        "番号が分かりませんでした" in missing_id_response
        and ai_missing_id.pending_memory_edit_input is None,
    )

    ai_nonexistent = _build_lightweight_personal_ai(fake_get_memories, fake_get_memory_by_id)
    nonexistent_response = ai_nonexistent.handle_user_input("999番の記憶を編集して")
    failures += check_true("nonexistent id reports not found", "見つかりませんでした" in nonexistent_response)

    # 無関係な編集依頼は反応しない
    ai_unrelated = _build_lightweight_personal_ai(fake_get_memories, fake_get_memory_by_id)
    ai_unrelated.handle_user_input("このファイルを編集して")
    failures += check_true(
        "unrelated file-edit request does not trigger memory edit",
        ai_unrelated.pending_memory_edit_input is None,
    )

    return failures


def check_legacy_test_double_without_memory_content_updater():
    """memory_content_updater属性を持たない（Ver2.60以前の）test doubleでも
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
    # 意図的にmemory_content_updaterを設定しない。

    ai.handle_user_input("1番の記憶を編集して")
    ai.handle_user_input("好きな食べ物はラーメンです")

    try:
        response = ai.handle_pending_memory_edit_confirmation("はい")
    except AttributeError as error:
        print(f"[NG] legacy test double without memory_content_updater raised AttributeError -> {error}")
        return 1

    return check_true(
        "legacy test double without memory_content_updater reports unavailable instead of crashing",
        response is not None and "実行できません" in response,
    )


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"
    core = PROJECT_ROOT / "core"
    database_dir = PROJECT_ROOT / "database"

    files = [
        ("memory_management.py", core / "memory_management.py"),
        ("memory_management_intent.py", core / "memory_management_intent.py"),
        ("confirmation_intent.py", core / "confirmation_intent.py"),
        ("memory_manager.py", database_dir / "memory_manager.py"),
        ("personal_ai.py", core / "personal_ai.py"),
        ("check_ver2610.py", scripts / "check_ver2610.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_imports()
    failures += check_intent_detection()
    failures += check_persistence_against_isolated_db()
    failures += check_personal_ai_edit_flow()
    failures += check_legacy_test_double_without_memory_content_updater()

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
            "check_ver2610.py",
        ],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        [
            "## Version 2.61",
            "scripts/check_ver2610.py",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        [
            "現在バージョン:",
            "Ver2.61:",
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
