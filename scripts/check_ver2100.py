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
    return check_true("check_ver2100 does not write DB", before == after)


def make_reader_result(text, title="Example Domain", url="https://example.com"):
    return {
        "data": {
            "title": title,
            "final_url": url,
            "text_preview": text,
            "text": text,
        }
    }


def check_candidate_basic_fields():
    from core.memory_candidate import build_memory_candidate_from_reader_result

    candidate = build_memory_candidate_from_reader_result(
        make_reader_result("Example Domain This is a short public page."),
        source_tool="web_reader",
    )

    failures = 0
    failures += check_true("candidate is dict", isinstance(candidate, dict))
    failures += check_true("source_tool", candidate["source_tool"] == "web_reader")
    failures += check_true("source_url", candidate["source_url"] == "https://example.com")
    failures += check_true("title", candidate["title"] == "Example Domain")
    failures += check_true("summary", "short public page" in candidate["summary"])
    failures += check_true("candidate_type exists", bool(candidate["candidate_type"]))
    failures += check_true("importance exists", bool(candidate["importance"]))
    failures += check_true("risk_level exists", bool(candidate["risk_level"]))
    failures += check_true("reasons list", isinstance(candidate["reasons"], list))
    failures += check_true("dry-run should_save False", candidate["should_save"] is False)

    return failures


def check_long_text_is_shortened():
    from core.memory_candidate import build_memory_candidate_from_reader_result

    long_text = " ".join([f"word{i}" for i in range(200)])
    candidate = build_memory_candidate_from_reader_result(make_reader_result(long_text))

    failures = 0
    failures += check_true("summary shortened", len(candidate["summary"]) < len(long_text))
    failures += check_true("summary has ellipsis", candidate["summary"].endswith("..."))
    failures += check_true("long text requires confirmation", candidate["requires_user_confirmation"] is True)

    return failures


def check_sensitive_content_requires_confirmation():
    from core.memory_candidate import build_memory_candidate_from_reader_result

    personal = build_memory_candidate_from_reader_result(
        make_reader_result("ユーザーの住所と電話番号が含まれます。")
    )
    secret = build_memory_candidate_from_reader_result(
        make_reader_result("api_key と password が含まれます。")
    )
    high_risk = build_memory_candidate_from_reader_result(
        make_reader_result("契約、法律、医療、金銭に関わる内容です。")
    )

    failures = 0
    failures += check_true("personal confirmation", personal["requires_user_confirmation"] is True)
    failures += check_true("personal risk medium", personal["risk_level"] in ["medium", "high"])
    failures += check_true("secret confirmation", secret["requires_user_confirmation"] is True)
    failures += check_true("secret risk high", secret["risk_level"] == "high")
    failures += check_true("high risk confirmation", high_risk["requires_user_confirmation"] is True)
    failures += check_true("high risk level", high_risk["risk_level"] == "high")

    return failures


def check_no_forbidden_execution_words():
    source_paths = [
        PROJECT_ROOT / "core" / "memory_candidate.py",
        PROJECT_ROOT / "scripts" / "check_ver2100.py",
    ]
    forbidden_words = [
        "url" + "lib",
        "req" + "uests",
        "url" + "open",
        "ask_" + "llm(",
        "core.tool_" + "runner",
        "run_tool" + "_request(",
        "WebReader" + "Adapter(",
        "fetch" + "(",
        "save_" + "memory(",
        "save_" + "message(",
        "create_" + "database(",
        "Base.metadata." + "create_all",
    ]
    failures = 0

    for path in source_paths:
        text = path.read_text(encoding="utf-8")
        found_words = [word for word in forbidden_words if word in text]
        failures += check_true(f"{path.name} has no forbidden execution words", not found_words)

        if found_words:
            print(f"[NG] found in {path.name}: {found_words}")

    return failures


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    core = PROJECT_ROOT / "core"
    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"

    files = [
        ("memory_candidate.py", core / "memory_candidate.py"),
        ("check_ver2100.py", scripts / "check_ver2100.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("check_workflow.md", docs / "check_workflow.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
        ("reader_memory_policy.md", docs / "reader_memory_policy.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_candidate_basic_fields()
    failures += check_long_text_is_shortened()
    failures += check_sensitive_content_requires_confirmation()

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
            "check_ver2100.py",
            "check_ver290.py",
            "check_ver280.py",
            "check_ver270.py",
            "check_ver260.py",
            "check_ver250.py",
            "check_ver240.py",
            "check_ver230.py",
            "check_ver220.py",
            "check_ver210.py",
            "check_ver200.py",
            "run_ver1_checks.py",
            "All Ver2 checks passed",
        ],
    )

    failures += check_words(
        "docs",
        docs / "changelog.md",
        [
            "## Version 2.10",
            "Memory Candidate生成のdry-run",
            "Reader結果から保存候補を作る土台",
            "まだMemory保存はしない",
            "Web Reader本体にはまだ自動接続しない",
            "scripts/check_ver2100.py",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        [
            "現在バージョン: Ver2.10",
            "Ver2.10: Memory Candidate生成のdry-run設計",
            "core/memory_candidate.py",
            "Reader結果から保存候補を作る土台を追加",
            "Web Reader本体にはまだ自動接続しない",
            "Ver2.11: Memory CandidateをWeb Reader結果にdry-run接続",
        ],
    )

    failures += check_words(
        "reader_memory_policy.md",
        docs / "reader_memory_policy.md",
        [
            "Ver2.10",
            "Memory Candidate生成のdry-run",
            "DBスキーマ変更はしない",
            "Web Reader本体にはまだ自動接続しない",
            "Memory保存はまだしない",
        ],
    )

    failures += check_no_forbidden_execution_words()
    failures += check_db_unchanged(db_timestamp_before)

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
