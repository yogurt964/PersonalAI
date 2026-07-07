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


def check_capability_manager_hybrid_fallback():
    from core.capability_manager import CapabilityManager

    cm = CapabilityManager()
    failures = 0

    def fake_web_read(messages):
        return "web_read_required"

    result = cm.analyze("あのウェブサイトの中身教えて", ask_llm_func=fake_web_read)
    failures += check_true(
        "LLM fallback can flag a missing capability keywords missed",
        result["can_handle_now"] is False and result["primary_capability"] == "web_read_required",
    )

    def fake_none(messages):
        return "none"

    result_none = cm.analyze("今日は疲れました", ask_llm_func=fake_none)
    failures += check_true(
        "LLM fallback saying 'none' falls through to local_conversation",
        result_none["can_handle_now"] is True and result_none["primary_capability"] == "local_conversation",
    )

    def fake_unrecognized(messages):
        return "something_unexpected_the_model_made_up"

    result_unrecognized = cm.analyze("今日は疲れました", ask_llm_func=fake_unrecognized)
    failures += check_true(
        "unrecognized LLM label fails safe to local_conversation",
        result_unrecognized["can_handle_now"] is True
        and result_unrecognized["primary_capability"] == "local_conversation",
    )

    def fake_raises(messages):
        raise RuntimeError("boom")

    result_failed = cm.analyze("今日は疲れました", ask_llm_func=fake_raises)
    failures += check_true(
        "LLM call failure fails safe to local_conversation",
        result_failed["can_handle_now"] is True and result_failed["primary_capability"] == "local_conversation",
    )

    result_no_func = cm.analyze("今日は疲れました")
    failures += check_true(
        "no ask_llm_func (legacy callers) preserves old keyword-only behavior",
        result_no_func["can_handle_now"] is True and result_no_func["primary_capability"] == "local_conversation",
    )

    # 既存のキーワード一致経路は、ask_llm_funcを渡してもLLMを呼ばず今まで通り動く。
    def should_not_be_called(messages):
        raise AssertionError("keyword-matched input must not call the LLM fallback")

    keyword_result = cm.analyze("このPDFの内容を教えて", ask_llm_func=should_not_be_called)
    failures += check_true(
        "keyword-matched capability short-circuits before the LLM fallback",
        keyword_result["can_handle_now"] is False and keyword_result["primary_capability"] == "pdf_read_required",
    )

    return failures


def check_needs_web_search_hybrid_fallback():
    from core.web_search_intent import needs_web_search

    failures = 0

    def fake_yes(messages):
        return "yes"

    failures += check_true(
        "LLM fallback can flag a search-needing question keywords missed",
        needs_web_search("私の街で今開催中の変わったイベントある？", ask_llm_func=fake_yes) is True,
    )

    def fake_no(messages):
        return "no"

    failures += check_true(
        "LLM fallback saying 'no' returns False",
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

    def should_not_be_called(messages):
        raise AssertionError("keyword-matched input must not call the LLM fallback")

    failures += check_true(
        "keyword-matched search need short-circuits before the LLM fallback",
        needs_web_search("今日の天気を教えて", ask_llm_func=should_not_be_called) is True,
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
        'needs_web_search(user_input, ask_llm_func=getattr(self, "ask_llm_func", None))' in source,
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
