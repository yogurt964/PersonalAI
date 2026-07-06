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
    return check_true("check_ver2550 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2550.py").read_text(encoding="utf-8")
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
        print(f"[NG] check_ver2550 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2550 has no forbidden words")
    return 0


def check_imports():
    try:
        from core.vision_router import should_escalate_after_local_result
        from core.image_reader_adapter import ImageReaderAdapter
    except Exception as error:
        print(f"[NG] imports failed -> {error}")
        return 1

    should_escalate_after_local_result
    ImageReaderAdapter

    print("[OK] imports")
    return 0


def check_escalation_judgement():
    from core.vision_router import should_escalate_after_local_result

    failures = 0
    failures += check_true(
        "low confidence result escalates",
        should_escalate_after_local_result("この画像の内容はよくわかりません。判断できません。") is True,
    )
    failures += check_true(
        "confident result does not escalate",
        should_escalate_after_local_result("これは赤い正方形と青い円です。") is False,
    )
    failures += check_true(
        "empty result does not crash",
        should_escalate_after_local_result("") is False,
    )

    return failures


def _build_fake_png(tmp_path):
    path = tmp_path / "photo.png"
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\nIDATx\x9cc\xf8\xcf\xc0"
        b"\x00\x00\x03\x01\x01\x00\x18\xdd\x8d\xb0\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    return path


def check_auto_escalation_end_to_end(tmp_path):
    """実際のOpenAI API呼び出しは一切行わず、fakeのclient_factoryと独立したin-memory
    SQLiteで、自動エスカレーションのフロー全体を検証する。
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

    def fake_openai_factory(api_key, image_path, prompt, model):
        return "REAL_PATH_OPENAI_RESULT"

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
                return "よくわかりません。判断できません。"

        low_confidence_adapter = LowConfidenceAdapter(openai_client_factory=fake_openai_factory)
        escalated_result = low_confidence_adapter.execute(request)

        failures += check_true(
            "low-confidence local result auto-escalates to openai",
            escalated_result.data.get("backend") == "openai",
        )
        failures += check_true(
            "escalated result contains openai response",
            "REAL_PATH_OPENAI_RESULT" in escalated_result.data.get("text", ""),
        )
        failures += check_true(
            "usage recorded for the escalated call",
            usage_module.get_monthly_openai_usage_total() > 0,
        )

        class ConfidentAdapter(ImageReaderAdapter):
            def _call_local_vision(self, path, prompt):
                return "これは赤い正方形と青い円です。"

        confident_adapter = ConfidentAdapter(openai_client_factory=fake_openai_factory)
        usage_before_confident_call = usage_module.get_monthly_openai_usage_total()
        confident_result = confident_adapter.execute(request)

        failures += check_true(
            "confident local result stays local (no escalation)",
            confident_result.data.get("backend") == "local",
        )
        failures += check_true(
            "no additional usage recorded for confident result",
            usage_module.get_monthly_openai_usage_total() == usage_before_confident_call,
        )

        # 予算超過時は、エスカレーションを試みず、ローカルの結果をそのまま正直に返す。
        usage_module.record_openai_usage("image_reader_vision", "gpt-4o-mini", 6.0)

        def should_not_be_called(api_key, image_path, prompt, model):
            raise AssertionError("budget guard should have blocked this escalation")

        blocked_adapter = LowConfidenceAdapter(openai_client_factory=should_not_be_called)
        blocked_result = blocked_adapter.execute(request)

        failures += check_true(
            "budget-exceeded escalation falls back to honest local result",
            blocked_result.success is True and blocked_result.data.get("backend") == "local",
        )
        failures += check_true(
            "budget-exceeded fallback text is the honest low-confidence local answer",
            "わかりません" in blocked_result.data.get("text", ""),
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

    files = [
        ("vision_router.py", core / "vision_router.py"),
        ("image_reader_adapter.py", core / "image_reader_adapter.py"),
        ("check_ver2550.py", scripts / "check_ver2550.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_imports()
    failures += check_escalation_judgement()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        failures += check_auto_escalation_end_to_end(tmp_path)

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
            "check_ver2550.py",
        ],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        [
            "## Version 2.55",
            "scripts/check_ver2550.py",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        [
            "現在バージョン:",
            "Ver2.55:",
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
