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
    return check_true("check_ver2680 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2680.py").read_text(encoding="utf-8")
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
        print(f"[NG] check_ver2680 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2680 has no forbidden words")
    return 0


def check_imports():
    try:
        from core.capability_manager import CapabilityManager
        from core.web_search_intent import needs_web_search
        from core.personal_ai import PersonalAI
    except Exception as error:
        print(f"[NG] imports failed -> {error}")
        return 1

    CapabilityManager
    needs_web_search
    PersonalAI

    print("[OK] imports")
    return 0


def _with_fake_openai_key(func):
    """本番DBには一切触れず、独立したin-memory SQLiteでOpenAIフォールバック段を検証する。

    ai/openai_client.pyのget_api_key()が環境変数を要求するため、テスト用の
    ダミー値を一時的に設定する（実際のOpenAI API呼び出しはclient_factoryが差し替える）。
    成功時にrecord_openai_usage()が呼ばれるため、SessionLocalも一時的にin-memory
    SQLiteへ差し替え、本番DBへの書き込みを防ぐ。
    """
    import os

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from database.models import Base
    import database.openai_usage as usage_module

    temp_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=temp_engine)
    temp_session_factory = sessionmaker(autocommit=False, autoflush=False, bind=temp_engine)

    original_session_local = usage_module.SessionLocal
    usage_module.SessionLocal = temp_session_factory

    original_api_key = os.environ.get("OPENAI_API_KEY")
    os.environ["OPENAI_API_KEY"] = "sk-fake-test-key-not-real"

    try:
        return func()
    finally:
        usage_module.SessionLocal = original_session_local

        if original_api_key is None:
            del os.environ["OPENAI_API_KEY"]
        else:
            os.environ["OPENAI_API_KEY"] = original_api_key


def check_capability_manager_hybrid_fallback():
    """capability_manager.analyze()のLLMフォールバックを検証する。

    Ver2.72: scripts/benchmark_capability_classification.pyでQwen単独の分類精度を
    実測した結果、キーワードで拾えないケースの正解率が83.3%にとどまり95%の基準を
    満たさなかったため、このタスクに限りQwenへの問い合わせを行わず、直接OpenAIに
    判定を依頼する設計に変更した。そのためask_llm_func自体は呼び出されず、
    openai_client_factory経由の応答で検証する。
    """
    return _with_fake_openai_key(_check_capability_manager_hybrid_fallback_body)


def _check_capability_manager_hybrid_fallback_body():
    from core.capability_manager import CapabilityManager

    cm = CapabilityManager()
    failures = 0

    def fake_ask_llm_func(messages):
        raise AssertionError("Ver2.72: capability classification must not call ask_llm_func (Qwen) directly")

    def fake_openai_web_read(api_key, messages, model):
        return "web_read_required"

    result = cm.analyze(
        "あのウェブサイトの中身教えて",
        ask_llm_func=fake_ask_llm_func,
        openai_client_factory=fake_openai_web_read,
    )
    failures += check_true(
        "LLM fallback (OpenAI) can flag a missing capability keywords missed",
        result["can_handle_now"] is False and result["primary_capability"] == "web_read_required",
    )

    def fake_openai_none(api_key, messages, model):
        return "none"

    result_none = cm.analyze(
        "今日は疲れました", ask_llm_func=fake_ask_llm_func, openai_client_factory=fake_openai_none
    )
    failures += check_true(
        "LLM fallback saying 'none' falls through to local_conversation",
        result_none["can_handle_now"] is True and result_none["primary_capability"] == "local_conversation",
    )

    def fake_openai_unrecognized(api_key, messages, model):
        return "something_unexpected_the_model_made_up"

    result_unrecognized = cm.analyze(
        "今日は疲れました", ask_llm_func=fake_ask_llm_func, openai_client_factory=fake_openai_unrecognized
    )
    failures += check_true(
        "unrecognized LLM label fails safe to local_conversation",
        result_unrecognized["can_handle_now"] is True
        and result_unrecognized["primary_capability"] == "local_conversation",
    )

    def fake_openai_raises(api_key, messages, model):
        raise RuntimeError("boom")

    result_failed = cm.analyze(
        "今日は疲れました", ask_llm_func=fake_ask_llm_func, openai_client_factory=fake_openai_raises
    )
    failures += check_true(
        "LLM call failure fails safe to local_conversation",
        result_failed["can_handle_now"] is True and result_failed["primary_capability"] == "local_conversation",
    )

    result_no_func = cm.analyze("今日は疲れました")
    failures += check_true(
        "no ask_llm_func (legacy callers) preserves old keyword-only behavior",
        result_no_func["can_handle_now"] is True and result_no_func["primary_capability"] == "local_conversation",
    )

    # 既存のキーワード一致経路は、ask_llm_func/openai_client_factoryを渡してもLLMを
    # 一切呼ばず今まで通り動く。
    def should_not_be_called(*args):
        raise AssertionError("keyword-matched input must not call the LLM fallback")

    keyword_result = cm.analyze(
        "このPDFの内容を教えて", ask_llm_func=should_not_be_called, openai_client_factory=should_not_be_called
    )
    failures += check_true(
        "keyword-matched capability short-circuits before the LLM fallback",
        keyword_result["can_handle_now"] is False and keyword_result["primary_capability"] == "pdf_read_required",
    )

    return failures


def check_needs_web_search_hybrid_fallback():
    """needs_web_search()のLLM判定を検証する。

    Ver2.74: LLM（Qwen）が使える場合はキーワード一致に頼らず、常にLLMの判定
    （文脈込み）を優先する設計に変更した（scripts/benchmark_capability_classification.pyの
    実測でQwen単独の精度が100%だったことと、会話の文脈を考慮した判定が必要だったため）。
    そのため、キーワードに一致する入力でもask_llm_funcが渡されていればLLMが呼ばれる。
    """
    from core.web_search_intent import needs_web_search

    failures = 0

    def fake_yes(messages):
        return "yes"

    failures += check_true(
        "LLM judgement can flag a search-needing question keywords missed",
        needs_web_search("私の街で今開催中の変わったイベントある？", ask_llm_func=fake_yes) is True,
    )

    def fake_no(messages):
        return "no"

    failures += check_true(
        "LLM judgement saying 'no' returns False",
        needs_web_search("こんにちは", ask_llm_func=fake_no) is False,
    )

    def fake_raises(messages):
        raise RuntimeError("boom")

    failures += check_true(
        "LLM call failure fails safe to False",
        needs_web_search("こんにちは", ask_llm_func=fake_raises) is False,
    )

    failures += check_true(
        "no ask_llm_func (legacy callers) preserves old keyword-only behavior",
        needs_web_search("こんにちは") is False,
    )

    failures += check_true(
        "no ask_llm_func still catches an obvious keyword-matched case",
        needs_web_search("今日の天気を教えて") is True,
    )

    def fake_yes_for_obvious_case(messages):
        return "yes"

    failures += check_true(
        "when ask_llm_func is available, even a keyword-matched case goes through the LLM "
        "(so conversation context can still override an out-of-context keyword match)",
        needs_web_search("今日の天気を教えて", ask_llm_func=fake_yes_for_obvious_case) is True,
    )

    return failures


def check_personal_ai_wires_ask_llm_func_through():
    source = (PROJECT_ROOT / "core" / "personal_ai.py").read_text(encoding="utf-8")

    failures = 0
    failures += check_true(
        "capability_manager.analyze() call passes ask_llm_func",
        "self.capability_manager.analyze(" in source
        and 'ask_llm_func=getattr(self, "ask_llm_func", None)' in source,
    )
    failures += check_true(
        "needs_web_search() call passes ask_llm_func",
        "needs_web_search(" in source and 'ask_llm_func=getattr(self, "ask_llm_func", None)' in source,
    )

    return failures


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"
    core = PROJECT_ROOT / "core"

    files = [
        ("capability_manager.py", core / "capability_manager.py"),
        ("web_search_intent.py", core / "web_search_intent.py"),
        ("personal_ai.py", core / "personal_ai.py"),
        ("check_ver2680.py", scripts / "check_ver2680.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_imports()
    failures += check_capability_manager_hybrid_fallback()
    failures += check_needs_web_search_hybrid_fallback()
    failures += check_personal_ai_wires_ask_llm_func_through()

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        ["check_ver2680.py"],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        ["## Version 2.68", "scripts/check_ver2680.py"],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        ["現在バージョン:", "Ver2.68:"],
    )

    failures += check_check_script_has_no_forbidden_words()
    failures += check_db_unchanged(db_timestamp_before)

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
