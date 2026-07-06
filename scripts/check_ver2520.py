import inspect
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
    return check_true("check_ver2520 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2520.py").read_text(encoding="utf-8")
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
        print(f"[NG] check_ver2520 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2520 has no forbidden words")
    return 0


def check_model_and_functions_exist():
    try:
        from database.models import MemoryCandidateRecord
        from database.memory_candidates import (
            save_memory_candidate_record,
            get_recent_memory_candidate_records,
        )
    except Exception as error:
        print(f"[NG] imports failed -> {error}")
        return 1

    failures = 0
    column_names = {column.name for column in MemoryCandidateRecord.__table__.columns}
    expected_columns = {
        "id",
        "created_at",
        "source_tool",
        "source_url",
        "title",
        "summary",
        "candidate_type",
        "risk_level",
        "status",
        "saved_memory_id",
    }
    failures += check_true(
        "MemoryCandidateRecord has expected columns",
        expected_columns.issubset(column_names),
    )
    failures += check_true(
        "MemoryCandidateRecord table name is memory_candidates",
        MemoryCandidateRecord.__tablename__ == "memory_candidates",
    )

    save_memory_candidate_record
    get_recent_memory_candidate_records

    return failures


def check_persistence_against_isolated_db():
    """本番DBには一切触れず、独立したin-memory SQLiteで実際のSQL動作を検証する。"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from database.models import Base
    import database.memory_candidates as memory_candidates_module

    temp_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=temp_engine)
    temp_session_factory = sessionmaker(autocommit=False, autoflush=False, bind=temp_engine)

    original_session_local = memory_candidates_module.SessionLocal
    memory_candidates_module.SessionLocal = temp_session_factory

    failures = 0

    try:
        memory_candidates_module.save_memory_candidate_record(
            {
                "source_tool": "web_reader",
                "source_url": "https://example.com",
                "title": "T",
                "summary": "S",
                "candidate_type": "reader_summary",
                "risk_level": "low",
            },
            status="saved",
            saved_memory_id=42,
        )
        memory_candidates_module.save_memory_candidate_record(
            {
                "source_tool": "file_reader",
                "title": "T2",
                "summary": "S2",
                "candidate_type": "memory_candidate",
                "risk_level": "medium",
            },
            status="rejected",
        )

        records = memory_candidates_module.get_recent_memory_candidate_records(limit=10)

        failures += check_true("isolated db has 2 saved records", len(records) == 2)
        failures += check_true(
            "records returned in chronological order",
            records[0].source_tool == "web_reader" and records[1].source_tool == "file_reader",
        )
        failures += check_true("first record status correct", records[0].status == "saved")
        failures += check_true("first record saved_memory_id correct", records[0].saved_memory_id == 42)
        failures += check_true("second record status correct", records[1].status == "rejected")
        failures += check_true("second record saved_memory_id is None", records[1].saved_memory_id is None)
    finally:
        memory_candidates_module.SessionLocal = original_session_local

    failures += check_true(
        "production SessionLocal restored (isolation cleanup verified)",
        memory_candidates_module.SessionLocal is original_session_local,
    )

    return failures


def _build_pending_candidate():
    return {
        "title": "Test Title",
        "summary": "Test summary",
        "source_tool": "web_reader",
        "candidate_type": "reader_summary",
        "risk_level": "low",
        "source_url": "https://example.com",
    }


def check_confirmation_flow_records_saved_outcome():
    import core.personal_ai as personal_ai_module
    from core.personal_ai import PersonalAI

    ai = PersonalAI.__new__(PersonalAI)
    calls = []

    def fake_recorder(candidate, status):
        calls.append((candidate.get("title"), status))

    ai.memory_candidate_recorder = fake_recorder
    ai.pending_memory_candidate_confirmation = _build_pending_candidate()
    ai.pending_memory_candidate_edit = None
    ai.last_memory_candidate_confirmation_result = None
    ai.last_memory_candidate_save_result = None
    ai.last_saved_memory_candidate_result = None

    original_save_memory = personal_ai_module.save_memory
    personal_ai_module.save_memory = lambda *args, **kwargs: True

    try:
        response = ai.handle_pending_memory_candidate_confirmation("保存して")
    finally:
        personal_ai_module.save_memory = original_save_memory

    failures = 0
    failures += check_true("save response mentions saved", "保存しました" in response)
    failures += check_true("recorder called once", len(calls) == 1)
    failures += check_true("recorder recorded saved status", calls[0] == ("Test Title", "saved"))
    failures += check_true("pending cleared", ai.pending_memory_candidate_confirmation is None)

    return failures


def check_confirmation_flow_records_rejected_outcome():
    from core.personal_ai import PersonalAI

    ai = PersonalAI.__new__(PersonalAI)
    calls = []

    def fake_recorder(candidate, status):
        calls.append((candidate.get("title"), status))

    ai.memory_candidate_recorder = fake_recorder
    ai.pending_memory_candidate_confirmation = _build_pending_candidate()
    ai.pending_memory_candidate_edit = None
    ai.last_memory_candidate_confirmation_result = None
    ai.last_memory_candidate_save_result = None
    ai.last_saved_memory_candidate_result = None

    response = ai.handle_pending_memory_candidate_confirmation("保存しない")

    failures = 0
    failures += check_true("reject response correct", "保存しません" in response)
    failures += check_true("recorder called once with rejected", calls == [("Test Title", "rejected")])

    return failures


def check_confirmation_flow_safe_without_recorder():
    """memory_candidate_recorder属性を持たない（Ver2.52以前の）test doubleでも
    例外を起こさず、暗黙にDBへ書き込まないことを確認する。
    """
    from core.personal_ai import PersonalAI

    ai = PersonalAI.__new__(PersonalAI)
    ai.pending_memory_candidate_confirmation = _build_pending_candidate()
    ai.pending_memory_candidate_edit = None
    ai.last_memory_candidate_confirmation_result = None
    ai.last_memory_candidate_save_result = None
    ai.last_saved_memory_candidate_result = None

    try:
        response = ai.handle_pending_memory_candidate_confirmation("保存しない")
    except AttributeError as error:
        print(f"[NG] legacy test double without memory_candidate_recorder raised AttributeError -> {error}")
        return 1

    return check_true(
        "legacy test double without memory_candidate_recorder still works",
        "保存しません" in response,
    )


def check_init_wires_memory_candidate_recorder():
    from core.personal_ai import PersonalAI

    source = inspect.getsource(PersonalAI.__init__)

    return check_true(
        "PersonalAI.__init__ wires self.memory_candidate_recorder to the real save_memory_candidate_record",
        "self.memory_candidate_recorder = save_memory_candidate_record" in source,
    )


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"
    database_dir = PROJECT_ROOT / "database"
    core = PROJECT_ROOT / "core"

    files = [
        ("models.py", database_dir / "models.py"),
        ("memory_candidates.py", database_dir / "memory_candidates.py"),
        ("personal_ai.py", core / "personal_ai.py"),
        ("check_ver2520.py", scripts / "check_ver2520.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_model_and_functions_exist()
    failures += check_persistence_against_isolated_db()
    failures += check_confirmation_flow_records_saved_outcome()
    failures += check_confirmation_flow_records_rejected_outcome()
    failures += check_confirmation_flow_safe_without_recorder()
    failures += check_init_wires_memory_candidate_recorder()

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
            "check_ver2520.py",
        ],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        [
            "## Version 2.52",
            "scripts/check_ver2520.py",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        [
            "現在バージョン:",
            "Ver2.52:",
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
