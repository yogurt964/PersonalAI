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
    return check_true("check_ver2600 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2600.py").read_text(encoding="utf-8")
    forbidden_words = [
        "req" + "uests.get",
        "req" + "uests.post",
        "Base.metadata." + "create_all(bind=engine)",
        "create_" + "database(",
        "reset --" + "hard",
        "force " + "push",
        "re" + "base",
    ]
    found_words = [word for word in forbidden_words if word in source]

    if found_words:
        print(f"[NG] check_ver2600 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2600 has no forbidden words")
    return 0


def check_imports():
    try:
        from core.personal_ai import PersonalAI, NON_ESCALATABLE_QWEN_ACTIONS
    except Exception as error:
        print(f"[NG] imports failed -> {error}")
        return 1

    PersonalAI
    NON_ESCALATABLE_QWEN_ACTIONS

    print("[OK] imports")
    return 0


def check_is_qwen_free_form_answer_gate():
    """_is_qwen_free_form_answer()が、chat系actionだけをエスカレーション対象にすることを確認する。"""
    from core.personal_ai import PersonalAI

    ai = PersonalAI.__new__(PersonalAI)

    failures = 0

    failures += check_true(
        "chat action + qwen target is escalatable",
        ai._is_qwen_free_form_answer({"action": "chat"}, {"target": "qwen"}) is True,
    )
    failures += check_true(
        "recommend action + qwen target is escalatable",
        ai._is_qwen_free_form_answer({"action": "recommend"}, {"target": "qwen"}) is True,
    )
    failures += check_true(
        "answer_question action + qwen target is escalatable",
        ai._is_qwen_free_form_answer({"action": "answer_question"}, {"target": "qwen"}) is True,
    )
    failures += check_true(
        "ask_clarification action is NOT escalatable (fixed guidance text)",
        ai._is_qwen_free_form_answer({"action": "ask_clarification"}, {"target": "qwen"}) is False,
    )
    failures += check_true(
        "summarize_url action is NOT escalatable (fixed unimplemented notice)",
        ai._is_qwen_free_form_answer({"action": "summarize_url"}, {"target": "qwen"}) is False,
    )
    failures += check_true(
        "unsupported_file_creation action is NOT escalatable",
        ai._is_qwen_free_form_answer({"action": "unsupported_file_creation"}, {"target": "qwen"}) is False,
    )
    failures += check_true(
        "non-qwen target (openai_candidate) is NOT escalatable",
        ai._is_qwen_free_form_answer({"action": "chat"}, {"target": "openai_candidate"}) is False,
    )
    failures += check_true(
        "None plan/route does not crash and is NOT escalatable",
        ai._is_qwen_free_form_answer(None, None) is False,
    )

    return failures


def check_normal_conversation_escalation_flow():
    """本番DBには一切触れず、独立したin-memory SQLiteで通常会話のエスカレーション経路を検証する。

    handle_user_input()全体は組み立てずに、Ver2.60で追加した判定
    （_is_qwen_free_form_answer）と既存の自動エスカレーションロジック
    （_escalate_text_answer_if_low_confidence、Ver2.56で追加）を組み合わせて、
    実際にhandle_user_input()の最後で行われるのと同じ経路を検証する。
    実際のOpenAI API呼び出しは一切行わない。
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import os

    from database.models import Base
    import database.openai_usage as usage_module
    from core.personal_ai import PersonalAI

    temp_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=temp_engine)
    temp_session_factory = sessionmaker(autocommit=False, autoflush=False, bind=temp_engine)

    original_session_local = usage_module.SessionLocal
    usage_module.SessionLocal = temp_session_factory

    original_api_key = os.environ.get("OPENAI_API_KEY")
    os.environ["OPENAI_API_KEY"] = "sk-fake-test-key-not-real"

    failures = 0

    def fake_openai_client_factory(api_key, messages, model):
        return "OPENAI_CHAT_ESCALATED_ANSWER"

    try:
        ai = PersonalAI.__new__(PersonalAI)
        ai.openai_text_client_factory = fake_openai_client_factory

        plan = {"action": "chat"}
        route = {"target": "qwen"}
        messages = [{"role": "user", "content": "こんにちは、調子はどう？"}]

        executor_answer = "判断できません。"
        if ai._is_qwen_free_form_answer(plan, route):
            executor_answer = ai._escalate_text_answer_if_low_confidence(executor_answer, messages)

        failures += check_true(
            "low-confidence normal-chat answer auto-escalates to openai",
            "OPENAI_CHAT_ESCALATED_ANSWER" in executor_answer,
        )
        failures += check_true(
            "usage recorded for the escalated normal-chat call",
            usage_module.get_monthly_openai_usage_total() > 0,
        )

        clarification_plan = {"action": "ask_clarification"}
        clarification_answer = "その作業を進めるには、もう少し情報が必要です。判断できません。"
        usage_before = usage_module.get_monthly_openai_usage_total()

        def should_not_be_called(api_key, messages, model):
            raise AssertionError("ask_clarification must not be escalated")

        ai.openai_text_client_factory = should_not_be_called

        if ai._is_qwen_free_form_answer(clarification_plan, route):
            clarification_answer = ai._escalate_text_answer_if_low_confidence(
                clarification_answer, messages
            )

        failures += check_true(
            "ask_clarification fixed text is left unchanged (no escalation attempted)",
            clarification_answer == "その作業を進めるには、もう少し情報が必要です。判断できません。",
        )
        failures += check_true(
            "no additional usage recorded for the non-escalatable action",
            usage_module.get_monthly_openai_usage_total() == usage_before,
        )
    finally:
        usage_module.SessionLocal = original_session_local

        if original_api_key is None:
            del os.environ["OPENAI_API_KEY"]
        else:
            os.environ["OPENAI_API_KEY"] = original_api_key

    return failures


def check_handle_user_input_wires_the_gate():
    source = (PROJECT_ROOT / "core" / "personal_ai.py").read_text(encoding="utf-8")

    return check_true(
        "handle_user_input calls _is_qwen_free_form_answer before escalating",
        "_is_qwen_free_form_answer(plan, route)" in source,
    )


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"
    core = PROJECT_ROOT / "core"

    files = [
        ("personal_ai.py", core / "personal_ai.py"),
        ("check_ver2600.py", scripts / "check_ver2600.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_imports()
    failures += check_is_qwen_free_form_answer_gate()
    failures += check_normal_conversation_escalation_flow()
    failures += check_handle_user_input_wires_the_gate()

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
            "check_ver2600.py",
        ],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        [
            "## Version 2.60",
            "scripts/check_ver2600.py",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        [
            "現在バージョン:",
            "Ver2.60:",
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
