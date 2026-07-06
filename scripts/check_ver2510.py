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
    return check_true("check_ver2510 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2510.py").read_text(encoding="utf-8")
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
        print(f"[NG] check_ver2510 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2510 has no forbidden words")
    return 0


def check_model_and_functions_exist():
    try:
        from database.models import ReaderResult
        from database.reader_results import save_reader_result, get_recent_reader_results
    except Exception as error:
        print(f"[NG] imports failed -> {error}")
        return 1

    failures = 0
    column_names = {column.name for column in ReaderResult.__table__.columns}
    expected_columns = {"id", "created_at", "source_tool", "title", "location", "text", "truncated"}
    failures += check_true(
        "ReaderResult has expected columns",
        expected_columns.issubset(column_names),
    )
    failures += check_true(
        "ReaderResult table name is reader_results",
        ReaderResult.__tablename__ == "reader_results",
    )

    save_reader_result
    get_recent_reader_results

    return failures


def check_persistence_against_isolated_db():
    """本番DB（data/personal_ai.db）には一切触れず、独立したin-memory SQLiteで
    save_reader_result / get_recent_reader_results の実際のSQL動作を検証する。
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from database.models import Base
    import database.reader_results as reader_results_module

    temp_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=temp_engine)
    temp_session_factory = sessionmaker(autocommit=False, autoflush=False, bind=temp_engine)

    original_session_local = reader_results_module.SessionLocal
    reader_results_module.SessionLocal = temp_session_factory

    failures = 0

    try:
        reader_results_module.save_reader_result(
            source_tool="file_reader",
            title="note.txt",
            location="C:/tmp/note.txt",
            text="ISOLATED_DB_TEST_MARKER",
            truncated=False,
        )
        reader_results_module.save_reader_result(
            source_tool="pdf_reader",
            title="doc.pdf",
            location="C:/tmp/doc.pdf",
            text="SECOND_MARKER",
            truncated=True,
        )

        results = reader_results_module.get_recent_reader_results(limit=10)

        failures += check_true("isolated db has 2 saved results", len(results) == 2)
        failures += check_true(
            "results returned in chronological order",
            results[0].source_tool == "file_reader" and results[1].source_tool == "pdf_reader",
        )
        failures += check_true("first result text correct", results[0].text == "ISOLATED_DB_TEST_MARKER")
        failures += check_true("second result truncated flag correct", results[1].truncated is True)
    finally:
        reader_results_module.SessionLocal = original_session_local

    failures += check_true(
        "production SessionLocal restored (isolation cleanup verified)",
        reader_results_module.SessionLocal is original_session_local,
    )

    return failures


def check_remember_last_read_document_calls_saver_when_set():
    from core.personal_ai import PersonalAI

    ai = PersonalAI.__new__(PersonalAI)
    ai.last_read_document = None

    calls = []

    def fake_saver(source_tool, title, location, text):
        calls.append((source_tool, title, location, text))

    ai.reader_result_saver = fake_saver
    ai.remember_last_read_document("file_reader", "note.txt", "C:/tmp/note.txt", "HELLO WORLD")

    failures = 0
    failures += check_true("saver called exactly once", len(calls) == 1)
    failures += check_true(
        "saver called with correct arguments",
        calls[0] == ("file_reader", "note.txt", "C:/tmp/note.txt", "HELLO WORLD"),
    )
    failures += check_true("last_read_document still set", ai.last_read_document is not None)

    return failures


def check_remember_last_read_document_safe_without_saver():
    """reader_result_saver属性を持たない（Ver2.51以前の）test doubleでも
    例外を起こさず、暗黙にDBへ書き込まないことを確認する。
    """
    from core.personal_ai import PersonalAI

    ai = PersonalAI.__new__(PersonalAI)
    ai.last_read_document = None

    try:
        ai.remember_last_read_document("file_reader", "note2.txt", "C:/tmp/note2.txt", "NO SAVER HERE")
    except AttributeError as error:
        print(f"[NG] legacy test double without reader_result_saver raised AttributeError -> {error}")
        return 1

    return check_true(
        "legacy test double without reader_result_saver still works",
        ai.last_read_document is not None,
    )


def check_init_wires_reader_result_saver():
    from core.personal_ai import PersonalAI

    source = inspect.getsource(PersonalAI.__init__)

    return check_true(
        "PersonalAI.__init__ wires self.reader_result_saver to the real save_reader_result",
        "self.reader_result_saver = save_reader_result" in source,
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
        ("reader_results.py", database_dir / "reader_results.py"),
        ("personal_ai.py", core / "personal_ai.py"),
        ("reader_memory_policy.md", docs / "reader_memory_policy.md"),
        ("check_ver2510.py", scripts / "check_ver2510.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_model_and_functions_exist()
    failures += check_persistence_against_isolated_db()
    failures += check_remember_last_read_document_calls_saver_when_set()
    failures += check_remember_last_read_document_safe_without_saver()
    failures += check_init_wires_reader_result_saver()

    failures += check_words(
        "reader_memory_policy.md",
        docs / "reader_memory_policy.md",
        [
            "Reader結果全文のDB保存は、あくまで生ログ",
            "必要な情報に絞って要約・抽出する設計にする",
        ],
    )

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
            "check_ver2510.py",
        ],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        [
            "## Version 2.51",
            "scripts/check_ver2510.py",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        [
            "現在バージョン:",
            "Ver2.51:",
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
