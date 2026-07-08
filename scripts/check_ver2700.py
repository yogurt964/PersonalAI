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
    return check_true("check_ver2700 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2700.py").read_text(encoding="utf-8")
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
        print(f"[NG] check_ver2700 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2700 has no forbidden words")
    return 0


def check_imports():
    try:
        from core.execution_claim_check import contains_unverified_action_claim
        from core.personal_ai import PersonalAI
    except Exception as error:
        print(f"[NG] imports failed -> {error}")
        return 1

    contains_unverified_action_claim
    PersonalAI

    print("[OK] imports")
    return 0


def check_contains_unverified_action_claim():
    from core.execution_claim_check import contains_unverified_action_claim

    failures = 0

    failures += check_true(
        "detects the real Ver2.62 hallucination phrasing",
        contains_unverified_action_claim("記憶番号6（ユーザーの好きな食べ物は焼き肉）を削除しました。") is True,
    )
    failures += check_true(
        "detects a memory edit completion claim",
        contains_unverified_action_claim("記憶を編集しました。内容を更新しました。") is True,
    )
    failures += check_true(
        "does not flag unrelated casual chat",
        contains_unverified_action_claim("こんにちは、今日は良い天気ですね。") is False,
    )
    failures += check_true(
        "does not flag a completion claim unrelated to memory (e.g. saving a file)",
        contains_unverified_action_claim("ファイルを保存しました。") is False,
    )
    failures += check_true(
        "does not flag a plain memory mention with no completion claim",
        contains_unverified_action_claim("あなたの記憶には好きな食べ物が登録されています。") is False,
    )
    failures += check_true(
        "empty text does not crash",
        contains_unverified_action_claim("") is False,
    )

    return failures


def check_personal_ai_annotates_free_form_answers():
    from core.personal_ai import PersonalAI

    ai = PersonalAI.__new__(PersonalAI)

    failures = 0

    annotated = ai._annotate_unverified_action_claim("記憶番号6を削除しました。")
    failures += check_true(
        "hallucinated deletion claim gets an honest annotation appended",
        "念のため" in annotated and "動いていません" in annotated,
    )
    failures += check_true(
        "the original (fabricated) text is preserved, not silently discarded",
        "記憶番号6を削除しました。" in annotated,
    )

    unchanged = ai._annotate_unverified_action_claim("こんにちは、元気ですか？")
    failures += check_true(
        "ordinary answers are returned unchanged",
        unchanged == "こんにちは、元気ですか？",
    )

    return failures


def check_handle_user_input_wires_the_annotation():
    source = (PROJECT_ROOT / "core" / "personal_ai.py").read_text(encoding="utf-8")

    return check_true(
        "handle_user_input calls _annotate_unverified_action_claim after escalation, "
        "inside the free-form-answer branch",
        "_annotate_unverified_action_claim(ai_response)" in source,
    )


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"
    core = PROJECT_ROOT / "core"

    files = [
        ("execution_claim_check.py", core / "execution_claim_check.py"),
        ("personal_ai.py", core / "personal_ai.py"),
        ("check_ver2700.py", scripts / "check_ver2700.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_imports()
    failures += check_contains_unverified_action_claim()
    failures += check_personal_ai_annotates_free_form_answers()
    failures += check_handle_user_input_wires_the_annotation()

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        ["check_ver2700.py"],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        ["## Version 2.70", "scripts/check_ver2700.py"],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        ["現在バージョン:", "Ver2.70:"],
    )

    failures += check_check_script_has_no_forbidden_words()
    failures += check_db_unchanged(db_timestamp_before)

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
