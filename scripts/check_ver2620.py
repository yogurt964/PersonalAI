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
    return check_true("check_ver2620 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2620.py").read_text(encoding="utf-8")
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
        print(f"[NG] check_ver2620 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2620 has no forbidden words")
    return 0


def check_imports():
    try:
        from core.capability_manager import CapabilityManager
        from database.memory_manager import save_memory
        from ai.llm import SYSTEM_PROMPT
    except Exception as error:
        print(f"[NG] imports failed -> {error}")
        return 1

    CapabilityManager
    save_memory
    SYSTEM_PROMPT

    print("[OK] imports")
    return 0


def check_system_prompt_honesty_guardrail():
    from ai.llm import SYSTEM_PROMPT

    failures = 0
    failures += check_true(
        "SYSTEM_PROMPT forbids claiming unexecuted actions",
        "実行したかのように答えない" in SYSTEM_PROMPT,
    )
    failures += check_true(
        "SYSTEM_PROMPT tells the model to guide the recognized phrasing instead",
        "認識される言い方" in SYSTEM_PROMPT,
    )

    return failures


def check_capability_manager_false_positive_fix():
    """実機テストで見つかった、削除・編集依頼が誤ってReader未実装応答に
    ルーティングされてしまう不具合が解消されていることを確認する。
    """
    from core.capability_manager import CapabilityManager

    cm = CapabilityManager()
    failures = 0

    # 修正前は「このファイル」の素の言及だけで即座にfile_read_requiredと判定していた。
    failures += check_true(
        "file-deletion request no longer misroutes to file_read_required",
        cm._requires_file_reading("このファイル情報を削除してください") is False,
    )
    failures += check_true(
        "file-edit request no longer misroutes to file_read_required",
        cm._requires_file_reading("このファイルを編集してください") is False,
    )
    failures += check_true(
        "image-deletion request no longer misroutes to image_read_required",
        cm._requires_image_reading("この画像を削除して") is False,
    )
    failures += check_true(
        "pdf-edit request no longer misroutes to pdf_read_required",
        cm._requires_pdf_reading("このPDFを編集して") is False,
    )
    failures += check_true(
        "youtube-deletion request no longer misroutes to youtube_read_required",
        cm._requires_youtube_reading("この動画を消して", "この動画を消して", "text") is False,
    )
    failures += check_true(
        "web-edit request no longer misroutes to web_read_required",
        cm._requires_web_reading("このサイトを書き換えて", "このサイトを書き換えて", "text") is False,
    )

    # 既存の正常系（実際に読み取りたい場合）は壊れていないことを確認する。
    failures += check_true(
        "legit file-read request still triggers file_read_required",
        cm._requires_file_reading("このファイルを読んで") is True,
    )
    failures += check_true(
        "legit image-read request still triggers image_read_required",
        cm._requires_image_reading("この画像を見て") is True,
    )
    failures += check_true(
        "legit pdf-read request still triggers pdf_read_required",
        cm._requires_pdf_reading("このPDFの内容を教えて") is True,
    )
    failures += check_true(
        "legit youtube-read request still triggers youtube_read_required",
        cm._requires_youtube_reading("この動画を要約して", "この動画を要約して", "text") is True,
    )
    failures += check_true(
        "legit web-read request still triggers web_read_required",
        cm._requires_web_reading("このサイトを要約して", "このサイトを要約して", "text") is True,
    )

    return failures


def check_save_memory_no_longer_duplicates_legacy_records():
    """本番DBには一切触れず、独立したin-memory SQLiteで実際のSQL動作を検証する。

    実機テストで見つかった、memory_keyなしで保存された過去のレコードと、
    memory_keyつきの新しい保存経路が同じcategoryで重複作成されてしまう不具合を再現し、
    修正後は1件に統合されることを確認する。
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from database.models import Base
    import database.memory_manager as memory_manager_module

    temp_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=temp_engine)
    temp_session_factory = sessionmaker(autocommit=False, autoflush=False, bind=temp_engine)

    original_session_local = memory_manager_module.SessionLocal
    memory_manager_module.SessionLocal = temp_session_factory

    failures = 0

    try:
        # memory_keyなしで保存された古いレコード（Ver2.62より前の保存経路を再現）。
        memory_manager_module.save_memory(
            "ユーザーの好きな食べ物はカレー",
            "user_profile",
            "favorite_food",
            8,
            "user",
        )

        # memory_keyつきの新しい保存経路（ai/preference_memory.py相当）で同じcategoryを更新する。
        result = memory_manager_module.save_memory(
            "ユーザーの好きな食べ物は焼き肉",
            "user_profile",
            "favorite_food",
            8,
            "user",
            memory_key="favorite_food",
        )
        failures += check_true("second save (with memory_key) succeeds", result is True)

        memories = memory_manager_module.get_memories(limit=20)
        favorite_food_memories = [m for m in memories if m.category == "favorite_food"]
        failures += check_true(
            "no duplicate favorite_food memory is created",
            len(favorite_food_memories) == 1,
        )
        failures += check_true(
            "the single remaining memory reflects the newest content",
            favorite_food_memories[0].content == "ユーザーの好きな食べ物は焼き肉",
        )

        # MULTI_MEMORY_CATEGORIES（例: project）は引き続き複数件許可されることを確認する。
        memory_manager_module.save_memory(
            "プロジェクトAの進捗メモ", "project", "project", 7, "user", memory_key="project_a"
        )
        memory_manager_module.save_memory(
            "プロジェクトBの進捗メモ", "project", "project", 7, "user", memory_key="project_b"
        )
        project_memories = [m for m in memory_manager_module.get_memories(limit=20) if m.category == "project"]
        failures += check_true(
            "multi-memory categories still allow multiple entries",
            len(project_memories) == 2,
        )
    finally:
        memory_manager_module.SessionLocal = original_session_local

    failures += check_true(
        "production SessionLocal restored (isolation cleanup verified)",
        memory_manager_module.SessionLocal is original_session_local,
    )

    return failures


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"
    core = PROJECT_ROOT / "core"
    ai_dir = PROJECT_ROOT / "ai"
    database_dir = PROJECT_ROOT / "database"

    files = [
        ("capability_manager.py", core / "capability_manager.py"),
        ("memory_manager.py", database_dir / "memory_manager.py"),
        ("llm.py", ai_dir / "llm.py"),
        ("check_ver2620.py", scripts / "check_ver2620.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_imports()
    failures += check_system_prompt_honesty_guardrail()
    failures += check_capability_manager_false_positive_fix()
    failures += check_save_memory_no_longer_duplicates_legacy_records()

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
            "check_ver2620.py",
        ],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        [
            "## Version 2.62",
            "scripts/check_ver2620.py",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        [
            "現在バージョン:",
            "Ver2.62:",
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
