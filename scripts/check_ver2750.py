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
    return check_true("check_ver2750 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2750.py").read_text(encoding="utf-8")
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
        print(f"[NG] check_ver2750 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2750 has no forbidden words")
    return 0


def check_imports():
    try:
        from core.capability_manager import CapabilityManager
        from core.personal_ai import PersonalAI
        from ai.llm import SYSTEM_PROMPT
    except Exception as error:
        print(f"[NG] imports failed -> {error}")
        return 1

    CapabilityManager
    PersonalAI
    SYSTEM_PROMPT

    print("[OK] imports")
    return 0


def _with_fake_openai_key(func):
    """本番DBには一切触れず、独立したin-memory SQLiteでOpenAI分類フォールバックを検証する。

    実際のOpenAI API呼び出しは一切行わず、fakeのclient_factoryのみを使う。
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


def check_capability_manager_receives_conversation_context():
    """capability_manager.analyze()のOpenAI分類フォールバックに、会話文脈が実際に
    渡ることを確認する（実機で見つかった「Youtubeで配信しています」の誤分類の回帰テスト）。
    """
    from core.capability_manager import CapabilityManager

    def run():
        cm = CapabilityManager()
        failures = 0

        captured_prompts = []

        def fake_openai_context_aware(api_key, messages, model):
            prompt = messages[0]["content"]
            captured_prompts.append(prompt)
            if "直前の会話" in prompt and "エリモ・クドリャフカ" in prompt:
                return "none"
            return "youtube_read_required"

        result_with_context = cm.analyze(
            "Youtubeで配信しています",
            ask_llm_func=lambda messages: (_ for _ in ()).throw(
                AssertionError("Qwen must not be called for capability classification")
            ),
            openai_client_factory=fake_openai_context_aware,
            conversation_context="ユーザー: エリモ・クドリャフカについて教えて\nAI: わかりません",
        )
        failures += check_true(
            "with conversation context, a supplementary remark about the prior topic "
            "is not misclassified as a YouTube-reading request",
            result_with_context["can_handle_now"] is True
            and result_with_context["primary_capability"] == "local_conversation",
        )
        failures += check_true(
            "the context was actually included in the classification prompt",
            len(captured_prompts) == 1 and "直前の会話" in captured_prompts[0],
        )

        def fake_openai_no_context_info(api_key, messages, model):
            return "youtube_read_required"

        result_without_context = cm.analyze(
            "Youtubeで配信しています",
            ask_llm_func=lambda messages: (_ for _ in ()).throw(
                AssertionError("Qwen must not be called for capability classification")
            ),
            openai_client_factory=fake_openai_no_context_info,
            conversation_context=None,
        )
        failures += check_true(
            "without conversation context, the same input can still be (mis)classified "
            "as needing YouTube reading (demonstrates why context threading matters)",
            result_without_context["can_handle_now"] is False
            and result_without_context["primary_capability"] == "youtube_read_required",
        )

        return failures

    return _with_fake_openai_key(run)


def check_document_creation_prompt_distinguishes_content_generation():
    """document_creation_requiredの判定プロンプトに、実ファイル作成と
    チャット内で完結するコンテンツ生成（クイズ問題等）を区別する注意書きが
    含まれていることを確認する（実機で見つかった「問題作成」の誤分類対策）。
    """
    from core.capability_manager import CapabilityManager

    cm = CapabilityManager()

    def run():
        captured_prompts = []

        def fake_openai(api_key, messages, model):
            captured_prompts.append(messages[0]["content"])
            return "none"

        cm._ask_openai_for_capability_label("テスト問題を作ってください", fake_openai, None)

        failures = 0
        failures += check_true(
            "the classification prompt clarifies that content generation "
            "(e.g. quiz questions) should not be classified as document_creation_required",
            len(captured_prompts) == 1
            and "チャットの中でそのまま" in captured_prompts[0]
            and "document_creation_required" in captured_prompts[0],
        )
        failures += check_true(
            "the classification prompt also clarifies that reading-related labels "
            "should not be used for supplementary remarks about the ongoing topic",
            "補足説明" in captured_prompts[0],
        )

        return failures

    return _with_fake_openai_key(run)


def check_personal_ai_wires_conversation_context_to_capability_manager():
    source = (PROJECT_ROOT / "core" / "personal_ai.py").read_text(encoding="utf-8")

    return check_true(
        "the capability_manager.analyze() call site passes conversation_context",
        "self.capability_manager.analyze(" in source and "conversation_context=conversation_context" in source,
    )


def check_system_prompt_discourages_guess_listing():
    from ai.llm import SYSTEM_PROMPT

    failures = 0
    failures += check_true(
        "SYSTEM_PROMPT discourages listing multiple speculative guesses for unknown entities",
        "複数の推測を長々と並べる" in SYSTEM_PROMPT,
    )
    failures += check_true(
        "SYSTEM_PROMPT tells the model to ask one concrete clarifying question instead",
        "1つ具体的に尋ねる" in SYSTEM_PROMPT,
    )
    failures += check_true(
        "SYSTEM_PROMPT warns against misreading a supplementary remark as an unrelated new request",
        "無関係な新しい依頼と誤解しない" in SYSTEM_PROMPT,
    )

    return failures


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"
    core = PROJECT_ROOT / "core"
    ai_dir = PROJECT_ROOT / "ai"

    files = [
        ("capability_manager.py", core / "capability_manager.py"),
        ("personal_ai.py", core / "personal_ai.py"),
        ("llm.py", ai_dir / "llm.py"),
        ("check_ver2750.py", scripts / "check_ver2750.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_imports()
    failures += check_capability_manager_receives_conversation_context()
    failures += check_document_creation_prompt_distinguishes_content_generation()
    failures += check_personal_ai_wires_conversation_context_to_capability_manager()
    failures += check_system_prompt_discourages_guess_listing()

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        ["check_ver2750.py"],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        ["## Version 2.75", "scripts/check_ver2750.py"],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        ["現在バージョン:", "Ver2.75:"],
    )

    failures += check_check_script_has_no_forbidden_words()
    failures += check_db_unchanged(db_timestamp_before)

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
