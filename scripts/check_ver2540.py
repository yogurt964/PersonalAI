import sys
import tempfile
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
    return check_true("check_ver2540 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2540.py").read_text(encoding="utf-8")
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
        print(f"[NG] check_ver2540 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2540 has no forbidden words")
    return 0


def check_imports():
    try:
        from database.models import OpenAIUsageLog
        from database.openai_usage import record_openai_usage, get_monthly_openai_usage_total
        from ai.openai_client import (
            describe_image_with_openai,
            ensure_budget_available,
            get_api_key,
            OpenAIBudgetExceededError,
            OpenAIKeyMissingError,
        )
        from core.vision_router import (
            VISION_BACKEND_LOCAL,
            VISION_BACKEND_OPENAI,
            choose_vision_backend,
        )
        from core.image_reader_adapter import ImageReaderAdapter
    except Exception as error:
        print(f"[NG] imports failed -> {error}")
        return 1

    OpenAIUsageLog
    record_openai_usage
    get_monthly_openai_usage_total
    describe_image_with_openai
    ensure_budget_available
    get_api_key
    OpenAIBudgetExceededError
    OpenAIKeyMissingError
    VISION_BACKEND_LOCAL
    VISION_BACKEND_OPENAI
    choose_vision_backend
    ImageReaderAdapter

    print("[OK] imports")
    return 0


def check_vision_router_escalation():
    from core.vision_router import VISION_BACKEND_LOCAL, VISION_BACKEND_OPENAI, choose_vision_backend

    failures = 0
    failures += check_true(
        "default stays local",
        choose_vision_backend(user_request_text="これは何ですか？") == VISION_BACKEND_LOCAL,
    )
    failures += check_true(
        "explicit OpenAI request escalates",
        choose_vision_backend(user_request_text="OpenAIで解析して") == VISION_BACKEND_OPENAI,
    )
    failures += check_true(
        "explicit high-accuracy request escalates",
        choose_vision_backend(user_request_text="もっと正確に解析して") == VISION_BACKEND_OPENAI,
    )
    failures += check_true(
        "unrelated text stays local",
        choose_vision_backend(user_request_text="この画像を見て") == VISION_BACKEND_LOCAL,
    )

    return failures


def check_persistence_against_isolated_db():
    """本番DBには一切触れず、独立したin-memory SQLiteでopenai_usage_logの実際のSQL動作を検証する。"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from database.models import Base
    import database.openai_usage as usage_module

    temp_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=temp_engine)
    temp_session_factory = sessionmaker(autocommit=False, autoflush=False, bind=temp_engine)

    original_session_local = usage_module.SessionLocal
    usage_module.SessionLocal = temp_session_factory

    failures = 0

    try:
        usage_module.record_openai_usage("image_reader_vision", "gpt-4o-mini", 0.01)
        usage_module.record_openai_usage("image_reader_vision", "gpt-4o-mini", 0.02)

        total = usage_module.get_monthly_openai_usage_total()
        failures += check_true("isolated db usage total correct", abs(total - 0.03) < 1e-9)
    finally:
        usage_module.SessionLocal = original_session_local

    failures += check_true(
        "production SessionLocal restored (isolation cleanup verified)",
        usage_module.SessionLocal is original_session_local,
    )

    return failures


def check_openai_client_guards():
    """本番DBには一切触れず、独立したin-memory SQLiteでai/openai_client.pyのガードを検証する。

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

    def fake_client_factory(api_key, image_path, prompt, model):
        return f"FAKE_VISION_RESPONSE for {image_path} with model={model}"

    try:
        result = client_module.describe_image_with_openai(
            "C:/tmp/test.png",
            "この画像を説明して",
            client_factory=fake_client_factory,
            usage_total_func=usage_module.get_monthly_openai_usage_total,
            usage_recorder=usage_module.record_openai_usage,
        )
        failures += check_true("fake call returns fake response", "FAKE_VISION_RESPONSE" in result)
        failures += check_true(
            "usage recorded after successful call",
            abs(usage_module.get_monthly_openai_usage_total() - client_module.ESTIMATED_COST_PER_VISION_CALL_USD) < 1e-9,
        )

        try:
            client_module.describe_image_with_openai(
                "C:/tmp/test2.png",
                "prompt",
                monthly_cap_usd=0.005,
                client_factory=fake_client_factory,
                usage_total_func=usage_module.get_monthly_openai_usage_total,
                usage_recorder=usage_module.record_openai_usage,
            )
            print("[NG] budget guard did not raise")
            failures += 1
        except client_module.OpenAIBudgetExceededError:
            print("[OK] budget guard blocks call when cap exceeded")
    finally:
        usage_module.SessionLocal = original_session_local

        if original_api_key is None:
            del os.environ["OPENAI_API_KEY"]
        else:
            os.environ["OPENAI_API_KEY"] = original_api_key

    if original_api_key is None:
        try:
            client_module.get_api_key()
            print("[NG] key-missing guard did not raise")
            failures += 1
        except client_module.OpenAIKeyMissingError:
            print("[OK] key-missing guard raises when OPENAI_API_KEY is unset")

    return failures


def _build_fake_png(tmp_path):
    path = tmp_path / "photo.png"
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\nIDATx\x9cc\xf8\xcf\xc0"
        b"\x00\x00\x03\x01\x01\x00\x18\xdd\x8d\xb0\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    return path


def check_image_reader_openai_branch(tmp_path):
    """ImageReaderAdapterのOpenAI分岐を、fakeのopenai_client_factory経由で検証する。

    実際のOpenAI API呼び出しは一切行わない。
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import os

    from database.models import Base
    import database.openai_usage as usage_module
    from core.image_reader_adapter import ImageReaderAdapter
    from core.tool_adapter import ToolRequest

    temp_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=temp_engine)
    temp_session_factory = sessionmaker(autocommit=False, autoflush=False, bind=temp_engine)

    original_session_local = usage_module.SessionLocal
    usage_module.SessionLocal = temp_session_factory

    original_api_key = os.environ.get("OPENAI_API_KEY")
    os.environ["OPENAI_API_KEY"] = "sk-fake-test-key-not-real"

    failures = 0
    image_path = _build_fake_png(tmp_path)

    def fake_openai_client_factory(api_key, image_path, prompt, model):
        return f"FAKE_OPENAI_VISION_RESULT for {image_path}"

    try:
        adapter = ImageReaderAdapter(openai_client_factory=fake_openai_client_factory)
        request = ToolRequest(
            tool_name="image_reader",
            action="read_image",
            input_data={"path": str(image_path), "original_input": "OpenAIで解析して"},
            requires_permission=True,
            risk_level="medium",
        )
        result = adapter.execute(request)

        failures += check_true("openai branch selected", result.data.get("backend") == "openai")
        failures += check_true("openai branch succeeds", result.success is True)
        failures += check_true(
            "openai branch returns fake response text",
            "FAKE_OPENAI_VISION_RESULT" in result.data.get("text", ""),
        )

        # 予算超過時は、実際のcalled factoryを呼ばず正直に失敗を返すことを確認する。
        usage_module.record_openai_usage("image_reader_vision", "gpt-4o-mini", 6.0)

        def should_not_be_called(api_key, image_path, prompt, model):
            raise AssertionError("budget guard should have blocked this call")

        blocked_adapter = ImageReaderAdapter(openai_client_factory=should_not_be_called)
        blocked_result = blocked_adapter.execute(request)

        failures += check_true("budget-exceeded call fails honestly", blocked_result.success is False)
        failures += check_true(
            "budget-exceeded reason surfaced in error field",
            "上限" in (blocked_result.error or ""),
        )
    finally:
        usage_module.SessionLocal = original_session_local

        if original_api_key is None:
            del os.environ["OPENAI_API_KEY"]
        else:
            os.environ["OPENAI_API_KEY"] = original_api_key

    return failures


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"
    database_dir = PROJECT_ROOT / "database"
    core = PROJECT_ROOT / "core"
    ai_dir = PROJECT_ROOT / "ai"

    files = [
        ("models.py", database_dir / "models.py"),
        ("openai_usage.py", database_dir / "openai_usage.py"),
        ("openai_client.py", ai_dir / "openai_client.py"),
        ("vision_router.py", core / "vision_router.py"),
        ("image_reader_adapter.py", core / "image_reader_adapter.py"),
        ("requirements.txt", PROJECT_ROOT / "requirements.txt"),
        ("check_ver2540.py", scripts / "check_ver2540.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_imports()
    failures += check_vision_router_escalation()
    failures += check_persistence_against_isolated_db()
    failures += check_openai_client_guards()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        failures += check_image_reader_openai_branch(tmp_path)

    failures += check_words(
        "requirements.txt",
        PROJECT_ROOT / "requirements.txt",
        [
            "openai==",
        ],
    )

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
            "check_ver2540.py",
        ],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        [
            "## Version 2.54",
            "scripts/check_ver2540.py",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        [
            "現在バージョン:",
            "Ver2.54:",
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
