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
    return check_true("check_ver2740 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2740.py").read_text(encoding="utf-8")
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
        print(f"[NG] check_ver2740 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2740 has no forbidden words")
    return 0


def check_imports():
    try:
        from core.web_search_intent import needs_web_search
        from core.personal_ai import PersonalAI
    except Exception as error:
        print(f"[NG] imports failed -> {error}")
        return 1

    needs_web_search
    PersonalAI

    print("[OK] imports")
    return 0


def check_conversation_context_fetched_once_after_input_analysis():
    """会話文脈の取得が、handle_user_input()内で解釈（input_analysis）の直後に
    1回だけ行われ、build_web_search_response_if_needed()には引数として渡される
    （関数内で個別に再取得しない）ことをソースコードで確認する。
    """
    source = (PROJECT_ROOT / "core" / "personal_ai.py").read_text(encoding="utf-8")

    failures = 0
    failures += check_true(
        "handle_user_input computes conversation_context once, right after input_analysis",
        "input_analysis = self.input_analyzer.analyze(user_input)" in source
        and "conversation_context = self._build_recent_conversation_context()" in source,
    )
    failures += check_true(
        "build_web_search_response_if_needed receives conversation_context as a parameter",
        "def build_web_search_response_if_needed(self, user_input, conversation_context=None):" in source,
    )
    failures += check_true(
        "the call site passes the shared conversation_context through",
        "self.build_web_search_response_if_needed(user_input, conversation_context)" in source,
    )

    return failures


def check_needs_web_search_prefers_llm_over_keywords():
    """needs_web_search()が、ask_llm_funcが使える場合はキーワード一致より
    LLM判定（文脈込み）を優先することを確認する（Ver2.74）。
    """
    from core.web_search_intent import needs_web_search

    failures = 0

    # ask_llm_funcがない場合は、従来通りキーワードのみで決定論的に判定する。
    failures += check_true(
        "without ask_llm_func, an obvious keyword still matches (legacy behavior preserved)",
        needs_web_search("今日の天気を教えて") is True,
    )
    failures += check_true(
        "without ask_llm_func, a non-matching casual message returns False",
        needs_web_search("こんにちは") is False,
    )

    # ask_llm_funcがある場合は、キーワードに一致する入力でも必ずLLMに判定させる。
    calls = []

    def fake_ask_llm_func(messages):
        calls.append(messages[0]["content"])
        return "yes"

    result = needs_web_search("今日の天気を教えて", ask_llm_func=fake_ask_llm_func)
    failures += check_true(
        "with ask_llm_func available, even an obvious keyword-matched input reaches the LLM",
        len(calls) == 1 and result is True,
    )

    # 文脈があれば、キーワードに一致する語（例:「予算」）が入っていても、
    # LLMが文脈を踏まえてno（検索不要）と判定できる。
    def fake_context_aware(messages):
        prompt = messages[0]["content"]
        if "直前の会話" in prompt:
            return "no"
        return "yes"

    result_with_context = needs_web_search(
        "予算はどれくらいでしたっけ？",
        ask_llm_func=fake_context_aware,
        conversation_context="ユーザー: 前に話した旅行の計画について\nAI: 説明...",
    )
    failures += check_true(
        "keyword-matched text ('予算') can still be judged as not needing search "
        "when conversation context indicates it's a follow-up",
        result_with_context is False,
    )

    return failures


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"
    core = PROJECT_ROOT / "core"

    files = [
        ("web_search_intent.py", core / "web_search_intent.py"),
        ("personal_ai.py", core / "personal_ai.py"),
        ("check_ver2740.py", scripts / "check_ver2740.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_imports()
    failures += check_conversation_context_fetched_once_after_input_analysis()
    failures += check_needs_web_search_prefers_llm_over_keywords()

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        ["check_ver2740.py"],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        ["## Version 2.74", "scripts/check_ver2740.py"],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        ["現在バージョン:", "Ver2.74:"],
    )

    failures += check_check_script_has_no_forbidden_words()
    failures += check_db_unchanged(db_timestamp_before)

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
