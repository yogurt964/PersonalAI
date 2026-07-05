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
    return check_true("check_ver2300 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2300.py").read_text(encoding="utf-8")
    forbidden_words = [
        "req" + "uests",
        "url" + "lib",
        "url" + "open",
        "ask_" + "llm(",
        "Base.metadata." + "create_all",
        "create_" + "database(",
        "reset --" + "hard",
        "force " + "push",
        "re" + "base",
    ]
    found_words = [word for word in forbidden_words if word in source]

    if found_words:
        print(f"[NG] check_ver2300 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2300 has no forbidden words")
    return 0


def check_keyword_false_positive_fixed():
    from core.capability_manager import CapabilityManager
    from core.input_analyzer import InputAnalyzer
    from core.tool_request_builder import build_tool_request_decision

    ia = InputAnalyzer()
    cm = CapabilityManager()
    failures = 0

    keyword_sentences = [
        "このテキストファイルのテストキーワードを教えてください",
        "そのファイル内に書かれているテストキーワードは何ですか",
        "キーワード検索して",
    ]

    for text in keyword_sentences:
        analysis = ia.analyze(text)
        capability = cm.analyze(text, analysis)
        decision = build_tool_request_decision(text)

        failures += check_true(
            f"input_analyzer no false positive: {text}",
            analysis["requires_file_creation"] is False,
        )
        failures += check_true(
            f"capability_manager no false positive: {text}",
            capability["can_handle_now"] is True
            and capability["primary_capability"] != "document_creation_required",
        )
        failures += check_true(
            f"tool_request_builder no false positive: {text}",
            decision.requires_tool is False,
        )

    return failures


def check_real_word_cases_still_detected():
    from core.capability_manager import CapabilityManager
    from core.input_analyzer import InputAnalyzer

    ia = InputAnalyzer()
    cm = CapabilityManager()
    failures = 0

    real_cases = [
        "Wordで文書を作って",
        "ワード文書を作成して",
        "ワードファイルにして",
    ]

    for text in real_cases:
        analysis = ia.analyze(text)
        capability = cm.analyze(text, analysis)

        failures += check_true(
            f"input_analyzer still detects: {text}",
            analysis["requires_file_creation"] is True,
        )
        failures += check_true(
            f"capability_manager still blocks: {text}",
            capability["can_handle_now"] is False
            and capability["primary_capability"] == "document_creation_required",
        )

    return failures


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"
    core = PROJECT_ROOT / "core"

    files = [
        ("input_analyzer.py", core / "input_analyzer.py"),
        ("capability_manager.py", core / "capability_manager.py"),
        ("tool_request_builder.py", core / "tool_request_builder.py"),
        ("check_ver2300.py", scripts / "check_ver2300.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_keyword_false_positive_fixed()
    failures += check_real_word_cases_still_detected()

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
            "check_ver2300.py",
        ],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        [
            "## Version 2.30",
            "キーワード",
            "scripts/check_ver2300.py",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        [
            "現在バージョン:",
            "Ver2.30: 「ワード」/「キーワード」誤判定バグ修正",
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
