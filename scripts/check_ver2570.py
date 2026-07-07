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
    return check_true("check_ver2570 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2570.py").read_text(encoding="utf-8")
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
        print(f"[NG] check_ver2570 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2570 has no forbidden words")
    return 0


def check_imports():
    try:
        from ai.openai_client import (
            DEFAULT_POWERFUL_VISION_MODEL,
            DEFAULT_POWERFUL_TEXT_MODEL,
            ESTIMATED_COST_PER_POWERFUL_VISION_CALL_USD,
            ESTIMATED_COST_PER_POWERFUL_TEXT_CALL_USD,
        )
        from core.image_reader_adapter import ImageReaderAdapter
        from core.personal_ai import PersonalAI
    except Exception as error:
        print(f"[NG] imports failed -> {error}")
        return 1

    DEFAULT_POWERFUL_VISION_MODEL
    DEFAULT_POWERFUL_TEXT_MODEL
    ESTIMATED_COST_PER_POWERFUL_VISION_CALL_USD
    ESTIMATED_COST_PER_POWERFUL_TEXT_CALL_USD
    ImageReaderAdapter
    PersonalAI

    print("[OK] imports")
    return 0


def _build_fake_png(tmp_path):
    path = tmp_path / "photo.png"
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\nIDATx\x9cc\xf8\xcf\xc0"
        b"\x00\x00\x03\x01\x01\x00\x18\xdd\x8d\xb0\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    return path


def check_image_tier3_escalation(tmp_path):
    """本番DBには一切触れず、独立したin-memory SQLiteで画像解析のTier3エスカレーションを検証する。

    実際のOpenAI API呼び出しは一切行わず、fakeのclient_factoryのみを使う。
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import os

    from database.models import Base
    import database.openai_usage as usage_module
    from core.image_reader_adapter import ImageReaderAdapter
    from core.tool_adapter import ToolRequest
    from ai.openai_client import DEFAULT_POWERFUL_VISION_MODEL as DEFAULT_POWERFUL_MODEL

    temp_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=temp_engine)
    temp_session_factory = sessionmaker(autocommit=False, autoflush=False, bind=temp_engine)

    original_session_local = usage_module.SessionLocal
    usage_module.SessionLocal = temp_session_factory

    original_api_key = os.environ.get("OPENAI_API_KEY")
    os.environ["OPENAI_API_KEY"] = "sk-fake-test-key-not-real"

    failures = 0
    image_path = _build_fake_png(tmp_path)

    def fake_factory_tier2_low_tier3_high(api_key, image_path, prompt, model):
        if model == DEFAULT_POWERFUL_MODEL:
            return "TIER3_VISION_RESULT"
        return "判断できません。"

    try:
        request = ToolRequest(
            tool_name="image_reader",
            action="read_image",
            input_data={"path": str(image_path), "original_input": ""},
            requires_permission=True,
            risk_level="medium",
        )

        class LowConfidenceAdapter(ImageReaderAdapter):
            def _call_local_vision(self, path, prompt):
                return "わかりません。"

        adapter = LowConfidenceAdapter(openai_client_factory=fake_factory_tier2_low_tier3_high)
        result = adapter.execute(request)

        failures += check_true(
            "tier2-also-low-confidence escalates all the way to tier3",
            "TIER3_VISION_RESULT" in result.data.get("text", ""),
        )
        failures += check_true(
            "backend recorded as openai for tier3 result",
            result.data.get("backend") == "openai",
        )
        failures += check_true(
            "usage recorded for both tier2 and tier3 calls",
            abs(usage_module.get_monthly_openai_usage_total() - 0.04) < 1e-9,
        )

        def fake_factory_tier3_fails(api_key, image_path, prompt, model):
            if model == DEFAULT_POWERFUL_MODEL:
                raise RuntimeError("simulated tier3 failure")
            return "判断できません。"

        usage_module.SessionLocal = temp_session_factory
        Base.metadata.drop_all(bind=temp_engine)
        Base.metadata.create_all(bind=temp_engine)

        fallback_adapter = LowConfidenceAdapter(openai_client_factory=fake_factory_tier3_fails)
        fallback_result = fallback_adapter.execute(request)

        failures += check_true(
            "tier3 failure falls back to tier2 result honestly",
            fallback_result.success is True
            and "判断できません" in fallback_result.data.get("text", ""),
        )
        failures += check_true(
            "fallback backend still recorded as openai (tier2 succeeded)",
            fallback_result.data.get("backend") == "openai",
        )
    finally:
        usage_module.SessionLocal = original_session_local

        if original_api_key is None:
            del os.environ["OPENAI_API_KEY"]
        else:
            os.environ["OPENAI_API_KEY"] = original_api_key

    return failures


def check_text_tier3_escalation():
    """本番DBには一切触れず、独立したin-memory SQLiteでテキスト応答のTier3エスカレーションを検証する。

    実際のOpenAI API呼び出しは一切行わない。
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import os

    from database.models import Base
    import database.openai_usage as usage_module
    from core.personal_ai import PersonalAI
    from core.input_analyzer import InputAnalyzer
    from ai.openai_client import DEFAULT_POWERFUL_TEXT_MODEL as DEFAULT_POWERFUL_MODEL

    temp_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=temp_engine)
    temp_session_factory = sessionmaker(autocommit=False, autoflush=False, bind=temp_engine)

    original_session_local = usage_module.SessionLocal
    usage_module.SessionLocal = temp_session_factory

    original_api_key = os.environ.get("OPENAI_API_KEY")
    os.environ["OPENAI_API_KEY"] = "sk-fake-test-key-not-real"

    failures = 0

    try:
        def fake_factory_tier2_low_tier3_high(api_key, messages, model):
            if model == DEFAULT_POWERFUL_MODEL:
                return "TIER3_TEXT_RESULT"
            return "判断できません。"

        ai = PersonalAI.__new__(PersonalAI)
        ai.input_analyzer = InputAnalyzer()
        ai.ask_llm_func = lambda messages: "判断できません。"
        ai.openai_text_client_factory = fake_factory_tier2_low_tier3_high

        response = ai.build_document_task_response_if_requested(
            "売上合計はいくらですか？", "ダミーの本文データ", "sales.xlsx"
        )
        failures += check_true(
            "tier2-also-low-confidence text answer escalates to tier3",
            "TIER3_TEXT_RESULT" in response,
        )
        failures += check_true(
            "usage recorded for both tier2 and tier3 text calls",
            abs(usage_module.get_monthly_openai_usage_total() - 0.025) < 1e-9,
        )

        def fake_factory_tier3_fails(api_key, messages, model):
            if model == DEFAULT_POWERFUL_MODEL:
                raise RuntimeError("simulated tier3 failure")
            return "判断できません。"

        ai.openai_text_client_factory = fake_factory_tier3_fails
        fallback_response = ai.build_document_task_response_if_requested(
            "売上合計はいくらですか？", "ダミーの本文データ", "sales.xlsx"
        )
        failures += check_true(
            "tier3 text failure falls back to tier2 result honestly",
            "判断できません" in fallback_response,
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
    core = PROJECT_ROOT / "core"
    ai_dir = PROJECT_ROOT / "ai"

    files = [
        ("openai_client.py", ai_dir / "openai_client.py"),
        ("image_reader_adapter.py", core / "image_reader_adapter.py"),
        ("personal_ai.py", core / "personal_ai.py"),
        ("check_ver2570.py", scripts / "check_ver2570.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_imports()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        failures += check_image_tier3_escalation(tmp_path)

    failures += check_text_tier3_escalation()

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
            "check_ver2570.py",
        ],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        [
            "## Version 2.57",
            "scripts/check_ver2570.py",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        [
            "現在バージョン:",
            "Ver2.57:",
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
