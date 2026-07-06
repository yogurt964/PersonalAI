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
    return check_true("check_ver2580 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2580.py").read_text(encoding="utf-8")
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
        print(f"[NG] check_ver2580 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2580 has no forbidden words")
    return 0


def check_imports():
    try:
        from core.web_search_intent import needs_web_search
        from ai.openai_client import ask_openai_with_web_search, DEFAULT_WEB_SEARCH_MODEL
        from core.personal_ai import PersonalAI
    except Exception as error:
        print(f"[NG] imports failed -> {error}")
        return 1

    needs_web_search
    ask_openai_with_web_search
    DEFAULT_WEB_SEARCH_MODEL
    PersonalAI

    print("[OK] imports")
    return 0


def check_needs_web_search_judgement():
    from core.web_search_intent import needs_web_search

    failures = 0
    failures += check_true(
        "explicit search phrase detected",
        needs_web_search("今日の天気を調べて") is True,
    )
    failures += check_true(
        "current-info marker detected",
        needs_web_search("最新のニュースを教えて") is True,
    )
    failures += check_true(
        "casual chat is not detected",
        needs_web_search("こんにちは、元気ですか") is False,
    )
    failures += check_true(
        "empty input does not crash",
        needs_web_search("") is False,
    )

    return failures


def check_web_search_response_flow():
    """本番DBには一切触れず、独立したin-memory SQLiteでWeb検索応答フローを検証する。

    実際のOpenAI API呼び出しは一切行わず、fakeのclient_factoryのみを使う。
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

    def fake_web_search_factory(api_key, query, model):
        return "FAKE_SEARCH_RESULT"

    try:
        ai = PersonalAI.__new__(PersonalAI)
        ai.input_analyzer = InputAnalyzer()
        ai.openai_web_search_client_factory = fake_web_search_factory

        response = ai.build_web_search_response_if_needed("今日の東京の天気を教えて")
        failures += check_true(
            "web-search-needed question returns a fake search result",
            "FAKE_SEARCH_RESULT" in (response or ""),
        )
        failures += check_true(
            "usage recorded under the web_search feature",
            usage_module.get_monthly_openai_usage_total() > 0,
        )

        non_search_response = ai.build_web_search_response_if_needed("こんにちは")
        failures += check_true(
            "non-search question returns None (falls through to normal chat)",
            non_search_response is None,
        )

        usage_module.record_openai_usage("web_search", "gpt-4o-mini", 6.0)

        def should_not_be_called(api_key, query, model):
            raise AssertionError("budget guard should have blocked this web search call")

        ai.openai_web_search_client_factory = should_not_be_called
        blocked_response = ai.build_web_search_response_if_needed("最新のニュースを教えて")
        failures += check_true(
            "budget-exceeded web search returns an honest cannot-search message",
            blocked_response is not None and "検索を実行できません" in blocked_response,
        )
    finally:
        usage_module.SessionLocal = original_session_local

        if original_api_key is None:
            del os.environ["OPENAI_API_KEY"]
        else:
            os.environ["OPENAI_API_KEY"] = original_api_key

    return failures


def check_legacy_test_double_without_web_search_client_factory():
    """openai_web_search_client_factory属性を持たない（Ver2.57以前の）test doubleでも
    例外を起こさないことを確認する（検索不要な通常入力のケース）。
    """
    from core.personal_ai import PersonalAI
    from core.input_analyzer import InputAnalyzer

    ai = PersonalAI.__new__(PersonalAI)
    ai.input_analyzer = InputAnalyzer()
    # 意図的にopenai_web_search_client_factoryを設定しない。

    try:
        response = ai.build_web_search_response_if_needed("こんにちは")
    except AttributeError as error:
        print(f"[NG] legacy test double without openai_web_search_client_factory raised AttributeError -> {error}")
        return 1

    return check_true(
        "legacy test double without openai_web_search_client_factory still works for non-search input",
        response is None,
    )


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"
    core = PROJECT_ROOT / "core"
    ai_dir = PROJECT_ROOT / "ai"

    files = [
        ("web_search_intent.py", core / "web_search_intent.py"),
        ("openai_client.py", ai_dir / "openai_client.py"),
        ("personal_ai.py", core / "personal_ai.py"),
        ("check_ver2580.py", scripts / "check_ver2580.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_imports()
    failures += check_needs_web_search_judgement()
    failures += check_web_search_response_flow()
    failures += check_legacy_test_double_without_web_search_client_factory()

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
            "check_ver2580.py",
        ],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        [
            "## Version 2.58",
            "scripts/check_ver2580.py",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        [
            "現在バージョン:",
            "Ver2.58:",
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
