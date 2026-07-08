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
    return check_true("check_ver2710 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2710.py").read_text(encoding="utf-8")
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
        print(f"[NG] check_ver2710 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2710 has no forbidden words")
    return 0


def check_imports():
    try:
        from core.capability_manager import CapabilityManager
        from core.web_search_intent import needs_web_search
    except Exception as error:
        print(f"[NG] imports failed -> {error}")
        return 1

    CapabilityManager
    needs_web_search

    print("[OK] imports")
    return 0


def _with_fake_openai_key(func):
    """本番DBには一切触れず、独立したin-memory SQLiteでOpenAIフォールバック段を検証する。

    実際のOpenAI API呼び出しは一切行わず、fakeのclient_factoryのみを使う。
    ai/openai_client.pyのget_api_key()が環境変数を要求するため、テスト用の
    ダミー値を一時的に設定する（実際のAPI呼び出しはclient_factoryが差し替える）。
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


def check_capability_manager_openai_fallback_tier():
    """capability_manager.analyze()のLLMフォールバックを検証する。

    Ver2.71時点ではQwen→OpenAIの2段構えだったが、Ver2.72で実測ベンチマークにより
    Qwen単独の分類精度が95%基準を満たさないと判明したため、capability_manager側は
    Qwenへの問い合わせを行わず直接OpenAIに判定を依頼する設計に変更された
    （scripts/check_ver2680.pyのcheck_capability_manager_hybrid_fallback()で、
    この新しい経路を詳しく検証している）。ここではask_llm_func（Qwen）が一切
    呼び出されないことも合わせて確認する。
    """
    from core.capability_manager import CapabilityManager

    def run():
        cm = CapabilityManager()
        failures = 0

        def fake_ask_llm_func(messages):
            raise AssertionError("Ver2.72: capability classification must not call ask_llm_func (Qwen)")

        def fake_openai_web_read(api_key, messages, model):
            return "web_read_required"

        result = cm.analyze(
            "あのウェブサイトの中身教えて",
            ask_llm_func=fake_ask_llm_func,
            openai_client_factory=fake_openai_web_read,
        )
        failures += check_true(
            "capability classification goes straight to OpenAI, never calling Qwen",
            result["can_handle_now"] is False and result["primary_capability"] == "web_read_required",
        )

        def fake_openai_also_garbled(api_key, messages, model):
            return "still not sure"

        result_unclear = cm.analyze(
            "あのウェブサイトの中身教えて",
            ask_llm_func=fake_ask_llm_func,
            openai_client_factory=fake_openai_also_garbled,
        )
        failures += check_true(
            "unclear OpenAI answer falls back to local_conversation",
            result_unclear["can_handle_now"] is True
            and result_unclear["primary_capability"] == "local_conversation",
        )

        def fake_openai_fails(api_key, messages, model):
            raise RuntimeError("boom")

        result_openai_fails = cm.analyze(
            "あのウェブサイトの中身教えて",
            ask_llm_func=fake_ask_llm_func,
            openai_client_factory=fake_openai_fails,
        )
        failures += check_true(
            "OpenAI call failure fails safe to local_conversation",
            result_openai_fails["can_handle_now"] is True
            and result_openai_fails["primary_capability"] == "local_conversation",
        )

        return failures

    return _with_fake_openai_key(run)


def check_parse_yes_no_word_boundary():
    """"no"が"not"/"know"のような無関係な単語に誤って部分一致しないことを確認する
    （実装中に見つかった実バグの回帰テスト）。
    """
    from core.web_search_intent import _parse_yes_no

    failures = 0
    failures += check_true("plain yes parses as True", _parse_yes_no("yes") is True)
    failures += check_true("plain no parses as False", _parse_yes_no("no") is False)
    failures += check_true(
        "'not certain' does not false-match 'no' as a substring of 'not'",
        _parse_yes_no("maybe? not certain") is None,
    )
    failures += check_true(
        "'I know the answer' does not false-match 'no' as a substring of 'know'",
        _parse_yes_no("I know the answer") is None,
    )
    failures += check_true("empty response is unclear", _parse_yes_no("") is None)

    return failures


def check_needs_web_search_openai_fallback_tier():
    from core.web_search_intent import needs_web_search

    def run():
        failures = 0

        def fake_qwen_garbled(messages):
            return "maybe? not certain"

        def fake_openai_yes(api_key, messages, model):
            return "yes"

        failures += check_true(
            "ambiguous Qwen answer falls through to the OpenAI classification tier",
            needs_web_search(
                "私の街で今開催中の変わったイベントある？",
                ask_llm_func=fake_qwen_garbled,
                openai_client_factory=fake_openai_yes,
            )
            is True,
        )

        def fake_openai_fails(api_key, messages, model):
            raise RuntimeError("boom")

        failures += check_true(
            "OpenAI call failure fails safe to False",
            needs_web_search(
                "私の街で今開催中の変わったイベントある？",
                ask_llm_func=fake_qwen_garbled,
                openai_client_factory=fake_openai_fails,
            )
            is False,
        )

        # Qwenが明確にyes/noを返せた場合は、OpenAIへは進まない。
        def fake_qwen_clean_no(messages):
            return "no"

        def should_not_be_called(api_key, messages, model):
            raise AssertionError("OpenAI fallback must not be reached when Qwen's answer is clean")

        failures += check_true(
            "a clean Qwen yes/no short-circuits before the OpenAI fallback tier",
            needs_web_search(
                "こんにちは",
                ask_llm_func=fake_qwen_clean_no,
                openai_client_factory=should_not_be_called,
            )
            is False,
        )

        return failures

    return _with_fake_openai_key(run)


def check_personal_ai_wires_openai_client_factory_through():
    source = (PROJECT_ROOT / "core" / "personal_ai.py").read_text(encoding="utf-8")

    failures = 0
    failures += check_true(
        "capability_manager.analyze() call passes openai_client_factory",
        'openai_client_factory=getattr(self, "openai_text_client_factory", None)' in source,
    )
    failures += check_true(
        "needs_web_search() call passes openai_client_factory",
        source.count('openai_client_factory=getattr(self, "openai_text_client_factory", None)') >= 2,
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
        ("check_ver2710.py", scripts / "check_ver2710.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_imports()
    failures += check_capability_manager_openai_fallback_tier()
    failures += check_parse_yes_no_word_boundary()
    failures += check_needs_web_search_openai_fallback_tier()
    failures += check_personal_ai_wires_openai_client_factory_through()

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        ["check_ver2710.py"],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        ["## Version 2.71", "scripts/check_ver2710.py"],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        ["現在バージョン:", "Ver2.71:"],
    )

    failures += check_check_script_has_no_forbidden_words()
    failures += check_db_unchanged(db_timestamp_before)

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
