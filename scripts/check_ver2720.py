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
    return check_true("check_ver2720 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2720.py").read_text(encoding="utf-8")
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
        print(f"[NG] check_ver2720 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2720 has no forbidden words")
    return 0


def check_imports():
    try:
        from core.capability_manager import CapabilityManager, _LLM_CAPABILITY_LABELS
    except Exception as error:
        print(f"[NG] imports failed -> {error}")
        return 1

    CapabilityManager
    _LLM_CAPABILITY_LABELS

    print("[OK] imports")
    return 0


def check_ask_llm_for_capability_label_removed():
    """Qwenへの分類問い合わせ自体（_ask_llm_for_capability_label）が削除されたことを確認する。"""
    from core.capability_manager import CapabilityManager

    return check_true(
        "_ask_llm_for_capability_label no longer exists on CapabilityManager",
        not hasattr(CapabilityManager, "_ask_llm_for_capability_label"),
    )


def check_none_label_is_a_valid_parse_result():
    """"none"が分類失敗と区別され、有効な結果として認識されることを確認する
    （実装中に見つかった実バグの回帰テスト）。
    """
    from core.capability_manager import CapabilityManager

    cm = CapabilityManager()
    failures = 0

    failures += check_true(
        '"none" parses as the literal string "none", not a failure sentinel',
        cm._parse_capability_label("none") == "none",
    )
    failures += check_true(
        "a real capability label still parses correctly",
        cm._parse_capability_label("web_read_required") == "web_read_required",
    )
    failures += check_true(
        "garbled/unmatched text parses as None (genuine failure)",
        cm._parse_capability_label("I have no idea what you mean") is None,
    )

    return failures


def check_capability_classification_goes_straight_to_openai():
    """capability_manager.analyze()が、キーワード不一致時にQwenを経由せず
    直接OpenAIへ判定を依頼することを確認する（本番DBには一切触れない）。
    """
    import os

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from database.models import Base
    import database.openai_usage as usage_module
    from core.capability_manager import CapabilityManager

    temp_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=temp_engine)
    temp_session_factory = sessionmaker(autocommit=False, autoflush=False, bind=temp_engine)

    original_session_local = usage_module.SessionLocal
    usage_module.SessionLocal = temp_session_factory

    original_api_key = os.environ.get("OPENAI_API_KEY")
    os.environ["OPENAI_API_KEY"] = "sk-fake-test-key-not-real"

    failures = 0

    try:
        cm = CapabilityManager()

        def fake_ask_llm_func(messages):
            raise AssertionError("Qwen (ask_llm_func) must never be called for capability classification")

        def fake_openai_web_read(api_key, messages, model):
            return "web_read_required"

        result = cm.analyze(
            "あのウェブサイトの中身教えて",
            ask_llm_func=fake_ask_llm_func,
            openai_client_factory=fake_openai_web_read,
        )
        failures += check_true(
            "OpenAI classification is used directly, without ever calling Qwen",
            result["can_handle_now"] is False and result["primary_capability"] == "web_read_required",
        )

        def fake_openai_none(api_key, messages, model):
            return "none"

        result_none = cm.analyze(
            "今日は疲れました", ask_llm_func=fake_ask_llm_func, openai_client_factory=fake_openai_none
        )
        failures += check_true(
            "OpenAI answering 'none' correctly falls through to local_conversation",
            result_none["can_handle_now"] is True and result_none["primary_capability"] == "local_conversation",
        )
    finally:
        usage_module.SessionLocal = original_session_local

        if original_api_key is None:
            del os.environ["OPENAI_API_KEY"]
        else:
            os.environ["OPENAI_API_KEY"] = original_api_key

    return failures


def check_benchmark_script_exists_and_excluded_from_checks():
    scripts = PROJECT_ROOT / "scripts"
    benchmark_path = scripts / "benchmark_capability_classification.py"

    failures = 0
    failures += check_file_exists("benchmark_capability_classification.py", benchmark_path)

    run_ver2_checks_source = (scripts / "run_ver2_checks.py").read_text(encoding="utf-8")
    failures += check_true(
        "the real-Qwen benchmark script is not part of the automated check suite",
        "benchmark_capability_classification.py" not in run_ver2_checks_source,
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
        ("llm_intent_resolver_design.md", docs / "llm_intent_resolver_design.md"),
        ("check_ver2720.py", scripts / "check_ver2720.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_imports()
    failures += check_ask_llm_for_capability_label_removed()
    failures += check_none_label_is_a_valid_parse_result()
    failures += check_capability_classification_goes_straight_to_openai()
    failures += check_benchmark_script_exists_and_excluded_from_checks()

    failures += check_words(
        "llm_intent_resolver_design.md",
        docs / "llm_intent_resolver_design.md",
        [
            "Ver2.72",
            "83.3%",
            "benchmark_capability_classification.py",
        ],
    )

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        ["check_ver2720.py"],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        ["## Version 2.72", "scripts/check_ver2720.py"],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        ["現在バージョン:", "Ver2.72:"],
    )

    failures += check_check_script_has_no_forbidden_words()
    failures += check_db_unchanged(db_timestamp_before)

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
