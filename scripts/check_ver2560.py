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
    return check_true("check_ver2560 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2560.py").read_text(encoding="utf-8")
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
        print(f"[NG] check_ver2560 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2560 has no forbidden words")
    return 0


def check_imports():
    try:
        from core.confidence_check import seems_low_confidence, LOW_CONFIDENCE_MARKERS
        from core.vision_router import should_escalate_after_local_result
        from ai.openai_client import ask_openai_text
        from core.personal_ai import PersonalAI
    except Exception as error:
        print(f"[NG] imports failed -> {error}")
        return 1

    seems_low_confidence
    LOW_CONFIDENCE_MARKERS
    should_escalate_after_local_result
    ask_openai_text
    PersonalAI

    print("[OK] imports")
    return 0


def check_shared_confidence_check_module():
    from core.confidence_check import seems_low_confidence
    from core.vision_router import should_escalate_after_local_result

    failures = 0
    failures += check_true(
        "seems_low_confidence detects uncertainty",
        seems_low_confidence("判断できません。") is True,
    )
    failures += check_true(
        "seems_low_confidence passes confident text",
        seems_low_confidence("これは赤い正方形です。") is False,
    )
    failures += check_true(
        "vision_router reuses the same shared judgement (identical results)",
        should_escalate_after_local_result("判断できません。") == seems_low_confidence("判断できません。"),
    )

    return failures


def check_ask_openai_text_guards():
    """本番DBには一切触れず、独立したin-memory SQLiteでask_openai_textのガードを検証する。

    実際のOpenAI API呼び出しは一切行わず、fakeのclient_factoryのみを使う。
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import os

    from database.models import Base
    import database.openai_usage as usage_module
    import ai.openai_client as client_module

    temp_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=temp_engine)
    temp_session_factory = sessionmaker(autocommit=False, autoflush=False, bind=temp_engine)

    original_session_local = usage_module.SessionLocal
    usage_module.SessionLocal = temp_session_factory

    original_api_key = os.environ.get("OPENAI_API_KEY")
    os.environ["OPENAI_API_KEY"] = "sk-fake-test-key-not-real"

    failures = 0

    def fake_client_factory(api_key, messages, model):
        return f"FAKE_TEXT_RESPONSE with model={model}"

    try:
        result = client_module.ask_openai_text(
            [{"role": "user", "content": "テスト質問"}],
            client_factory=fake_client_factory,
            usage_total_func=usage_module.get_monthly_openai_usage_total,
            usage_recorder=usage_module.record_openai_usage,
        )
        failures += check_true("fake call returns fake response", "FAKE_TEXT_RESPONSE" in result)
        failures += check_true(
            "usage recorded after successful call",
            abs(usage_module.get_monthly_openai_usage_total() - client_module.ESTIMATED_COST_PER_TEXT_CALL_USD) < 1e-9,
        )

        try:
            client_module.ask_openai_text(
                [{"role": "user", "content": "テスト質問2"}],
                monthly_cap_usd=0.001,
                client_factory=fake_client_factory,
                usage_total_func=usage_module.get_monthly_openai_usage_total,
                usage_recorder=usage_module.record_openai_usage,
            )
            print("[NG] budget guard did not raise")
            failures += 1
        except client_module.OpenAIBudgetExceededError:
            print("[OK] budget guard blocks text escalation when cap exceeded")
    finally:
        usage_module.SessionLocal = original_session_local

        if original_api_key is None:
            del os.environ["OPENAI_API_KEY"]
        else:
            os.environ["OPENAI_API_KEY"] = original_api_key

    return failures


def check_document_task_response_escalation():
    """本番DBには一切触れず、独立したin-memory SQLiteでbuild_document_task_response_if_requested()の
    自動エスカレーションを検証する。実際のOpenAI API呼び出しは一切行わない。
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import os

    from database.models import Base
    import database.openai_usage as usage_module
    from core.personal_ai import PersonalAI
    from core.input_analyzer import InputAnalyzer

    temp_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=temp_engine)
    temp_session_factory = sessionmaker(autocommit=False, autoflush=False, bind=temp_engine)

    original_session_local = usage_module.SessionLocal
    usage_module.SessionLocal = temp_session_factory

    original_api_key = os.environ.get("OPENAI_API_KEY")
    os.environ["OPENAI_API_KEY"] = "sk-fake-test-key-not-real"

    failures = 0

    def fake_openai_client_factory(api_key, messages, model):
        return "OPENAI_TEXT_ESCALATED_ANSWER: 合計は199840円です。"

    try:
        ai = PersonalAI.__new__(PersonalAI)
        ai.input_analyzer = InputAnalyzer()

        ai.ask_llm_func = lambda messages: "合計金額については判断できません。データからは特定できません。"
        ai.openai_text_client_factory = fake_openai_client_factory

        escalated_response = ai.build_document_task_response_if_requested(
            "売上合計はいくらですか？", "ダミーの本文データ", "sales.xlsx"
        )
        failures += check_true(
            "low-confidence qwen answer auto-escalates to openai",
            "OPENAI_TEXT_ESCALATED_ANSWER" in escalated_response,
        )
        failures += check_true(
            "usage recorded for the escalated call",
            usage_module.get_monthly_openai_usage_total() > 0,
        )

        usage_before_confident_call = usage_module.get_monthly_openai_usage_total()
        ai.ask_llm_func = lambda messages: "合計は199840円です。"
        confident_response = ai.build_document_task_response_if_requested(
            "売上合計はいくらですか？", "ダミーの本文データ", "sales.xlsx"
        )
        failures += check_true(
            "confident qwen answer is returned unchanged (no escalation)",
            confident_response == "合計は199840円です。",
        )
        failures += check_true(
            "no additional usage recorded for confident answer",
            usage_module.get_monthly_openai_usage_total() == usage_before_confident_call,
        )

        usage_module.record_openai_usage("text_escalation", "gpt-4o-mini", 6.0)

        def should_not_be_called(api_key, messages, model):
            raise AssertionError("budget guard should have blocked this escalation")

        ai.ask_llm_func = lambda messages: "判断できません。"
        ai.openai_text_client_factory = should_not_be_called
        blocked_response = ai.build_document_task_response_if_requested(
            "これは何ですか？", "ダミー本文", "test.txt"
        )
        failures += check_true(
            "budget-exceeded escalation falls back to the honest qwen answer",
            blocked_response == "判断できません。",
        )
    finally:
        usage_module.SessionLocal = original_session_local

        if original_api_key is None:
            del os.environ["OPENAI_API_KEY"]
        else:
            os.environ["OPENAI_API_KEY"] = original_api_key

    return failures


def check_legacy_test_double_without_openai_text_client_factory():
    """openai_text_client_factory属性を持たない（Ver2.56以前の）test doubleでも
    例外を起こさないことを確認する（低信頼判定に一致しない通常応答のケース）。
    """
    from core.personal_ai import PersonalAI
    from core.input_analyzer import InputAnalyzer

    ai = PersonalAI.__new__(PersonalAI)
    ai.input_analyzer = InputAnalyzer()
    ai.ask_llm_func = lambda messages: "こんにちは、これはテスト応答です。"
    # 意図的にopenai_text_client_factoryを設定しない。

    try:
        response = ai.build_document_task_response_if_requested("要約して", "ダミー本文", "test.txt")
    except AttributeError as error:
        print(f"[NG] legacy test double without openai_text_client_factory raised AttributeError -> {error}")
        return 1

    return check_true(
        "legacy test double without openai_text_client_factory still works for confident answers",
        response == "こんにちは、これはテスト応答です。",
    )


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"
    core = PROJECT_ROOT / "core"
    ai_dir = PROJECT_ROOT / "ai"

    files = [
        ("confidence_check.py", core / "confidence_check.py"),
        ("vision_router.py", core / "vision_router.py"),
        ("openai_client.py", ai_dir / "openai_client.py"),
        ("personal_ai.py", core / "personal_ai.py"),
        ("check_ver2560.py", scripts / "check_ver2560.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_imports()
    failures += check_shared_confidence_check_module()
    failures += check_ask_openai_text_guards()
    failures += check_document_task_response_escalation()
    failures += check_legacy_test_double_without_openai_text_client_factory()

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
            "check_ver2560.py",
        ],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        [
            "## Version 2.56",
            "scripts/check_ver2560.py",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        [
            "現在バージョン:",
            "Ver2.56:",
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
