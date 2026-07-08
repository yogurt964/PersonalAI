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
    return check_true("check_ver2730 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2730.py").read_text(encoding="utf-8")
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
        print(f"[NG] check_ver2730 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2730 has no forbidden words")
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


class _FakeMessage:
    def __init__(self, role, content):
        self.role = role
        self.content = content


def check_build_recent_conversation_context():
    """_build_recent_conversation_context()が、直近の会話を正しく文脈テキストにし、
    今回すでに保存済みの最新発言（自分自身）は除外することを確認する。
    """
    import core.personal_ai as personal_ai_module
    from core.personal_ai import PersonalAI

    failures = 0

    history = [
        _FakeMessage("user", "スプラトゥーンの話でわかばシューターに合うギアについて教えてください"),
        _FakeMessage("assistant", "わかばシューターに合うギア構成の説明..."),
        _FakeMessage("user", "構成を教えてください"),
    ]

    original_get_recent_messages = personal_ai_module.get_recent_messages
    personal_ai_module.get_recent_messages = lambda limit: history[-limit:]

    try:
        ai = PersonalAI.__new__(PersonalAI)
        context = ai._build_recent_conversation_context()

        failures += check_true(
            "context excludes the just-saved current turn",
            "構成を教えてください" not in context,
        )
        failures += check_true(
            "context includes the prior user turn",
            "わかばシューター" in context and "ユーザー:" in context,
        )
        failures += check_true(
            "context includes the prior assistant turn",
            "AI:" in context,
        )

        empty_history_context = PersonalAI.__new__(PersonalAI)
        personal_ai_module.get_recent_messages = lambda limit: []
        failures += check_true(
            "no history returns an empty context string",
            empty_history_context._build_recent_conversation_context() == "",
        )

        long_message_history = [
            _FakeMessage("user", "あ" * 500),
            _FakeMessage("assistant", "い" * 500),
            _FakeMessage("user", "現在のターン"),
        ]
        personal_ai_module.get_recent_messages = lambda limit: long_message_history[-limit:]
        truncated_ai = PersonalAI.__new__(PersonalAI)
        truncated_context = truncated_ai._build_recent_conversation_context(max_chars_per_message=200)
        failures += check_true(
            "long messages are truncated so the prompt doesn't grow unbounded",
            len(truncated_context) < 500,
        )
    finally:
        personal_ai_module.get_recent_messages = original_get_recent_messages

    return failures


def check_build_context_aware_search_query():
    from core.personal_ai import PersonalAI

    ai = PersonalAI.__new__(PersonalAI)
    failures = 0

    no_context_query = ai._build_context_aware_search_query("構成を教えてください", "")
    failures += check_true(
        "no conversation context leaves the query unchanged",
        no_context_query == "構成を教えてください",
    )

    context_query = ai._build_context_aware_search_query(
        "構成を教えてください", "ユーザー: わかばシューターのギアについて\nAI: 説明..."
    )
    failures += check_true(
        "with conversation context, the query embeds the prior topic",
        "わかばシューター" in context_query and "構成を教えてください" in context_query,
    )

    return failures


def check_needs_web_search_uses_conversation_context():
    """needs_web_search()のLLMフォールバックに、会話文脈が実際に渡ることを確認する。

    ここでは文脈の有無をfakeのask_llm_funcが検知できるようにし、文脈ありの場合だけ
    「これは直前の話題の続きなのでWeb検索不要」と判定させる（実際のQwen/OpenAIの
    振る舞いを模したdry-run）。
    """
    from core.web_search_intent import needs_web_search

    failures = 0

    def fake_ask_llm_context_aware(messages):
        prompt = messages[0]["content"]
        if "直前の会話" in prompt and "わかばシューター" in prompt:
            return "no"
        return "yes"

    result_with_context = needs_web_search(
        "構成を教えてください",
        ask_llm_func=fake_ask_llm_context_aware,
        conversation_context="ユーザー: わかばシューターのギアについて\nAI: 説明...",
    )
    failures += check_true(
        "with conversation context, a follow-up question is judged as not needing search",
        result_with_context is False,
    )

    result_without_context = needs_web_search(
        "構成を教えてください",
        ask_llm_func=fake_ask_llm_context_aware,
        conversation_context=None,
    )
    failures += check_true(
        "without conversation context, the same fake LLM defaults to needing search "
        "(demonstrates why the Ver2.62/2.63-era behavior misfired on follow-ups)",
        result_without_context is True,
    )

    return failures


def check_personal_ai_wires_context_through():
    source = (PROJECT_ROOT / "core" / "personal_ai.py").read_text(encoding="utf-8")

    failures = 0
    failures += check_true(
        "build_web_search_response_if_needed builds and passes conversation_context",
        "conversation_context=conversation_context" in source
        and "_build_recent_conversation_context" in source,
    )
    failures += check_true(
        "the web search query itself is built with context awareness",
        "_build_context_aware_search_query" in source,
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
        ("check_ver2730.py", scripts / "check_ver2730.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_imports()
    failures += check_build_recent_conversation_context()
    failures += check_build_context_aware_search_query()
    failures += check_needs_web_search_uses_conversation_context()
    failures += check_personal_ai_wires_context_through()

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        ["check_ver2730.py"],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        ["## Version 2.73", "scripts/check_ver2730.py"],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        ["現在バージョン:", "Ver2.73:"],
    )

    failures += check_check_script_has_no_forbidden_words()
    failures += check_db_unchanged(db_timestamp_before)

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
