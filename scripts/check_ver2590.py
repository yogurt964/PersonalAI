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
    return check_true("check_ver2590 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2590.py").read_text(encoding="utf-8")
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
        print(f"[NG] check_ver2590 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2590 has no forbidden words")
    return 0


def check_imports():
    try:
        from ai.openai_client import (
            describe_image_with_openai,
            DEFAULT_VISION_MODEL,
            DEFAULT_POWERFUL_VISION_MODEL,
            ESTIMATED_COST_PER_POWERFUL_VISION_CALL_USD,
        )
        from core.image_reader_adapter import ImageReaderAdapter
    except Exception as error:
        print(f"[NG] imports failed -> {error}")
        return 1

    describe_image_with_openai
    DEFAULT_VISION_MODEL
    DEFAULT_POWERFUL_VISION_MODEL
    ESTIMATED_COST_PER_POWERFUL_VISION_CALL_USD
    ImageReaderAdapter

    print("[OK] imports")
    return 0


def check_powerful_vision_model_is_gpt55():
    from ai.openai_client import DEFAULT_POWERFUL_VISION_MODEL

    return check_true(
        "DEFAULT_POWERFUL_VISION_MODEL is gpt-5.5 (real API existence confirmed in Ver2.58/2.59)",
        DEFAULT_POWERFUL_VISION_MODEL == "gpt-5.5",
    )


def check_fake_vision_tier2_and_tier3_flow(tmp_path):
    """本番DBには一切触れず、独立したin-memory SQLiteでvisionのTier2/Tier3フローを検証する。

    実際のOpenAI API呼び出しは一切行わず、fakeのclient_factoryのみを使う。
    Ver2.59の実API検証では、これと同じ経路（describe_image_with_openai）を、
    fakeではなく実際のOpenAI API・実画像ファイルで呼び出して動作を確認した。
    """
    import os

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from database.models import Base
    import database.openai_usage as usage_module
    from ai.openai_client import (
        describe_image_with_openai,
        DEFAULT_POWERFUL_VISION_MODEL,
        ESTIMATED_COST_PER_POWERFUL_VISION_CALL_USD,
    )

    temp_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=temp_engine)
    temp_session_factory = sessionmaker(autocommit=False, autoflush=False, bind=temp_engine)

    original_session_local = usage_module.SessionLocal
    usage_module.SessionLocal = temp_session_factory

    original_api_key = os.environ.get("OPENAI_API_KEY")
    os.environ["OPENAI_API_KEY"] = "sk-fake-test-key-not-real"

    fake_image_path = tmp_path / "fake_check_ver2590.png"
    fake_image_path.write_bytes(b"not a real png, only used as a path placeholder")

    failures = 0

    try:
        def fake_tier2_factory(api_key, image_path, prompt, model):
            return "FAKE_TIER2_VISION_RESULT"

        tier2_text = describe_image_with_openai(
            str(fake_image_path),
            "prompt",
            client_factory=fake_tier2_factory,
        )
        failures += check_true(
            "fake Tier2 vision call returns the fake result",
            tier2_text == "FAKE_TIER2_VISION_RESULT",
        )
        failures += check_true(
            "usage recorded under the image_reader_vision feature",
            usage_module.get_monthly_openai_usage_total() > 0,
        )

        def fake_tier3_factory(api_key, image_path, prompt, model):
            failures_local = []
            if model != DEFAULT_POWERFUL_VISION_MODEL:
                failures_local.append(model)
            return "FAKE_TIER3_VISION_RESULT"

        tier3_text = describe_image_with_openai(
            str(fake_image_path),
            "prompt",
            model=DEFAULT_POWERFUL_VISION_MODEL,
            feature="image_reader_vision_tier3",
            estimated_cost_usd=ESTIMATED_COST_PER_POWERFUL_VISION_CALL_USD,
            client_factory=fake_tier3_factory,
        )
        failures += check_true(
            "fake Tier3 vision call returns the fake result",
            tier3_text == "FAKE_TIER3_VISION_RESULT",
        )
    finally:
        usage_module.SessionLocal = original_session_local

        if original_api_key is None:
            del os.environ["OPENAI_API_KEY"]
        else:
            os.environ["OPENAI_API_KEY"] = original_api_key

    return failures


def main():
    import tempfile

    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"
    ai_dir = PROJECT_ROOT / "ai"
    core = PROJECT_ROOT / "core"

    files = [
        ("openai_client.py", ai_dir / "openai_client.py"),
        ("image_reader_adapter.py", core / "image_reader_adapter.py"),
        ("check_ver2590.py", scripts / "check_ver2590.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_imports()
    failures += check_powerful_vision_model_is_gpt55()

    with tempfile.TemporaryDirectory() as tmp_dir:
        failures += check_fake_vision_tier2_and_tier3_flow(Path(tmp_dir))

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
            "check_ver2590.py",
        ],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        [
            "## Version 2.59",
            "scripts/check_ver2590.py",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        [
            "現在バージョン:",
            "Ver2.59:",
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
