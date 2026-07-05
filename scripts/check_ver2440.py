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
    return check_true("check_ver2440 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2440.py").read_text(encoding="utf-8")
    forbidden_words = [
        "req" + "uests.get",
        "req" + "uests.post",
        "url" + "lib.request",
        "url" + "open(",
        "Base.metadata." + "create_all",
        "create_" + "database(",
        "reset --" + "hard",
        "force " + "push",
        "re" + "base",
    ]
    found_words = [word for word in forbidden_words if word in source]

    if found_words:
        print(f"[NG] check_ver2440 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2440 has no forbidden words")
    return 0


def check_imports():
    try:
        from core.confirmation_intent import resolve_confirmation_intent
        from core.personal_ai import PersonalAI
    except Exception as error:
        print(f"[NG] imports failed -> {error}")
        return 1

    resolve_confirmation_intent
    PersonalAI

    print("[OK] imports")
    return 0


def _fake_llm(status):
    calls = []

    def fn(messages):
        calls.append(messages)
        return status

    fn.calls = calls
    return fn


def _raising_llm(messages):
    raise RuntimeError("qwen unavailable")


def check_fixed_words_still_fast_path():
    from core.confirmation_intent import resolve_confirmation_intent

    failures = 0
    llm = _fake_llm("rejected")  # 逆の答えを返すfakeで、固定語彙が優先されることを検証する

    confirmed = resolve_confirmation_intent("はい", context_type="web_reader", ask_llm_func=llm)
    failures += check_true("fixed confirmed word wins over llm", confirmed["status"] == "confirmed")
    failures += check_true("fixed confirmed word does not call llm", len(llm.calls) == 0)

    llm2 = _fake_llm("confirmed")
    rejected = resolve_confirmation_intent("キャンセル", context_type="web_reader", ask_llm_func=llm2)
    failures += check_true("fixed rejected word wins over llm", rejected["status"] == "rejected")
    failures += check_true("fixed rejected word does not call llm", len(llm2.calls) == 0)

    return failures


def check_llm_fallback_for_ambiguous_input():
    from core.confirmation_intent import resolve_confirmation_intent

    failures = 0

    llm_confirmed = _fake_llm("confirmed")
    result_confirmed = resolve_confirmation_intent(
        "うん、それで頼むよ",
        context_type="web_reader",
        ask_llm_func=llm_confirmed,
    )
    failures += check_true("ambiguous input triggers llm", len(llm_confirmed.calls) == 1)
    failures += check_true("llm confirmed is honored", result_confirmed["status"] == "confirmed")
    failures += check_true("llm-derived confirmed has medium confidence", result_confirmed["confidence"] == "medium")

    llm_rejected = _fake_llm("rejected")
    result_rejected = resolve_confirmation_intent(
        "うーん、今回はやめとくよ",
        context_type="web_reader",
        ask_llm_func=llm_rejected,
    )
    failures += check_true("llm rejected is honored", result_rejected["status"] == "rejected")

    return failures


def check_fail_safe_behavior():
    from core.confirmation_intent import resolve_confirmation_intent

    failures = 0

    garbage_llm = _fake_llm("confirmed and rejected, not sure")
    garbage_result = resolve_confirmation_intent(
        "うーん",
        context_type="web_reader",
        ask_llm_func=garbage_llm,
    )
    failures += check_true("ambiguous llm output falls back to unclear", garbage_result["status"] == "unclear")

    exception_result = resolve_confirmation_intent(
        "うーん",
        context_type="web_reader",
        ask_llm_func=_raising_llm,
    )
    failures += check_true("llm exception falls back to unclear", exception_result["status"] == "unclear")

    empty_llm = _fake_llm("")
    empty_result = resolve_confirmation_intent(
        "",
        context_type="web_reader",
        ask_llm_func=empty_llm,
    )
    failures += check_true("empty input does not call llm", len(empty_llm.calls) == 0)
    failures += check_true("empty input is unclear", empty_result["status"] == "unclear")

    return failures


def check_no_ask_llm_func_does_not_call_real_llm():
    from core.confirmation_intent import resolve_confirmation_intent

    # ask_llm_funcを渡さない呼び出し元（古いcheckスクリプトのtest doubleなど）では、
    # 暗黙に実際のQwenを呼び出さず、これまで通りunclearのままにする。
    result = resolve_confirmation_intent("うーん、よくわからないなあ", context_type="web_reader")

    return check_true(
        "omitting ask_llm_func stays unclear without a real llm call",
        result["status"] == "unclear",
    )


def check_no_external_content_in_llm_prompt():
    from core.confirmation_intent import resolve_confirmation_intent

    llm = _fake_llm("confirmed")
    resolve_confirmation_intent(
        "たぶん大丈夫だと思う",
        context_type="pdf_reader",
        ask_llm_func=llm,
    )

    failures = 0
    failures += check_true("llm was called", len(llm.calls) == 1)

    prompt_messages = llm.calls[0]
    prompt_text = " ".join(message["content"] for message in prompt_messages)

    failures += check_true(
        "prompt contains the user's reply text",
        "たぶん大丈夫だと思う" in prompt_text,
    )
    failures += check_true(
        "prompt does not contain unrelated document markers",
        "PPTX_FAKE_MARKER" not in prompt_text and "自動集計" not in prompt_text,
    )
    failures += check_true(
        "prompt stays short (no external document content mixed in)",
        len(prompt_text) < 400,
    )

    return failures


def check_all_seven_readers_thread_ask_llm_func():
    import inspect

    from core import (
        excel_reader_confirmation,
        file_reader_confirmation,
        pdf_reader_confirmation,
        pptx_reader_confirmation,
        web_reader_confirmation,
        word_reader_confirmation,
        youtube_reader_confirmation,
    )

    modules_and_functions = [
        (web_reader_confirmation, "resolve_web_reader_confirmation_response"),
        (file_reader_confirmation, "resolve_file_reader_confirmation_response"),
        (pdf_reader_confirmation, "resolve_pdf_reader_confirmation_response"),
        (word_reader_confirmation, "resolve_word_reader_confirmation_response"),
        (excel_reader_confirmation, "resolve_excel_reader_confirmation_response"),
        (pptx_reader_confirmation, "resolve_pptx_reader_confirmation_response"),
        (youtube_reader_confirmation, "resolve_youtube_reader_confirmation_response"),
    ]

    failures = 0

    for module, function_name in modules_and_functions:
        function = getattr(module, function_name)
        signature = inspect.signature(function)
        failures += check_true(
            f"{function_name} accepts ask_llm_func",
            "ask_llm_func" in signature.parameters,
        )

    return failures


def check_personal_ai_passes_ask_llm_func():
    import inspect

    from core.personal_ai import PersonalAI

    method_names = [
        "handle_pending_web_reader_confirmation",
        "handle_pending_file_reader_confirmation",
        "handle_pending_pdf_reader_confirmation",
        "handle_pending_word_reader_confirmation",
        "handle_pending_excel_reader_confirmation",
        "handle_pending_pptx_reader_confirmation",
        "handle_pending_youtube_reader_confirmation",
    ]

    failures = 0

    for method_name in method_names:
        source = inspect.getsource(getattr(PersonalAI, method_name))
        failures += check_true(
            f"{method_name} forwards ask_llm_func",
            "ask_llm_func=getattr(self, \"ask_llm_func\", None)" in source,
        )

    return failures


def check_legacy_test_doubles_without_ask_llm_func_still_work():
    # check_ver240.pyなど過去のcheckが作るtest doubleは ask_llm_func 属性を持たない。
    # getattr(..., None)で安全にNoneへフォールバックし、暗黙のLLM呼び出しをしないことを確認する。
    from core.capability_manager import CapabilityManager
    from core.input_analyzer import InputAnalyzer
    from core.personal_ai import PersonalAI
    from core.tool_execution_log import ToolExecutionLogger
    from core.web_reader_confirmation import build_web_reader_confirmation

    ai = PersonalAI.__new__(PersonalAI)
    ai.input_analyzer = InputAnalyzer()
    ai.capability_manager = CapabilityManager()
    ai.web_reader_fetcher = None
    ai.tool_registry = ai.build_tool_registry(None)
    ai.tool_execution_logger = ToolExecutionLogger()
    # 意図的にask_llm_funcを設定しない（古いtest doubleの再現）。
    ai.save_user_message = lambda _message: None
    ai.save_assistant_message = lambda _message: None

    confirmation = build_web_reader_confirmation("https://example.com を読んで")
    ai.pending_web_reader_confirmation = confirmation.to_dict()
    ai.pending_web_reader_confirmation["original_input"] = "https://example.com を読んで"
    ai.last_web_reader_confirmation = confirmation
    ai.last_web_reader_confirmation_result = None
    ai.last_web_reader_tool_request_candidate = None
    ai.last_web_reader_tool_run_result = None
    ai.last_web_reader_tool_result = None

    try:
        response = ai.handle_pending_web_reader_confirmation("うーん、よくわからない")
    except AttributeError as error:
        print(f"[NG] legacy test double without ask_llm_func raised AttributeError -> {error}")
        return 1

    return check_true(
        "legacy test double without ask_llm_func stays unclear (asks again)",
        response is not None and "確認中です" in response,
    )


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"
    core = PROJECT_ROOT / "core"

    files = [
        ("confirmation_intent.py", core / "confirmation_intent.py"),
        ("personal_ai.py", core / "personal_ai.py"),
        ("check_ver2440.py", scripts / "check_ver2440.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_imports()
    failures += check_fixed_words_still_fast_path()
    failures += check_llm_fallback_for_ambiguous_input()
    failures += check_fail_safe_behavior()
    failures += check_no_ask_llm_func_does_not_call_real_llm()
    failures += check_no_external_content_in_llm_prompt()
    failures += check_all_seven_readers_thread_ask_llm_func()
    failures += check_personal_ai_passes_ask_llm_func()
    failures += check_legacy_test_doubles_without_ask_llm_func_still_work()

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
            "check_ver2440.py",
        ],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        [
            "## Version 2.44",
            "ハイブリッド",
            "scripts/check_ver2440.py",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        [
            "現在バージョン:",
            "Ver2.44:",
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
