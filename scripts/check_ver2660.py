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
    return check_true("check_ver2660 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2660.py").read_text(encoding="utf-8")
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
        print(f"[NG] check_ver2660 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2660 has no forbidden words")
    return 0


def check_imports():
    try:
        from core.reading_keywords import (
            BASE_PC_OPERATION_KEYWORDS,
            BASE_READING_INTENT_KEYWORDS,
            EXCEL_DOCUMENT_KEYWORDS,
            PDF_TO_FILE_KEYWORDS,
            WORD_DOCUMENT_KEYWORDS,
        )
        from core.input_analyzer import InputAnalyzer
        from core.capability_manager import CapabilityManager
    except Exception as error:
        print(f"[NG] imports failed -> {error}")
        return 1

    BASE_PC_OPERATION_KEYWORDS
    BASE_READING_INTENT_KEYWORDS
    EXCEL_DOCUMENT_KEYWORDS
    PDF_TO_FILE_KEYWORDS
    WORD_DOCUMENT_KEYWORDS
    InputAnalyzer
    CapabilityManager

    print("[OK] imports")
    return 0


def check_three_files_use_shared_module():
    """重複していたキーワードリストが、実際に共有モジュールから読み込まれていることを確認する。

    Ver2.66時点ではinput_analyzer.py/capability_manager.py/tool_request_builder.pyの
    3ファイルが対象だったが、tool_request_builder.py（core/tool_flow.py経由）は
    現在の会話フローに一切接続されていない不使用コードだったことがVer2.69の監査で判明し、
    削除された。残る2ファイルについてこの確認を続ける。
    """
    core = PROJECT_ROOT / "core"

    failures = 0
    failures += check_words(
        "input_analyzer.py imports from reading_keywords",
        core / "input_analyzer.py",
        ["from core.reading_keywords import"],
    )
    failures += check_words(
        "capability_manager.py imports from reading_keywords",
        core / "capability_manager.py",
        ["from core.reading_keywords import"],
    )

    return failures


def check_behavior_unchanged_input_analyzer():
    from core.input_analyzer import InputAnalyzer

    analyzer = InputAnalyzer()
    failures = 0

    failures += check_true(
        "input_analyzer still detects Word document creation",
        analyzer.analyze("Wordで文書を作って")["task_type"] == "create_document",
    )
    failures += check_true(
        "input_analyzer still detects generic report/document keywords",
        analyzer.analyze("資料を教えて")["task_type"] == "create_document",
    )
    failures += check_true(
        "input_analyzer 'キーワード' does not false-positive as document creation (Ver2.30 regression guard)",
        analyzer.analyze("テストキーワードを教えて")["task_type"] != "create_document",
    )

    return failures


def check_behavior_unchanged_capability_manager():
    from core.capability_manager import CapabilityManager

    cm = CapabilityManager()
    failures = 0

    failures += check_true(
        "capability_manager still requires document creation for Word/Excel",
        cm._requires_document_creation("Excelで表を作って", False) is True,
    )
    failures += check_true(
        "capability_manager still requires document creation for Markdown",
        cm._requires_document_creation("Markdownファイルを作って", False) is True,
    )
    failures += check_true(
        "capability_manager still detects PC operation via PowerShell",
        cm._requires_pc_operation("PowerShellで実行して") is True,
    )
    failures += check_true(
        "capability_manager reading intent still includes 文字起こし",
        cm._has_reading_intent("文字起こしをお願いします") is True,
    )
    failures += check_true(
        "capability_manager file-deletion request still does not misroute (Ver2.62 regression guard)",
        cm._requires_file_reading("このファイル情報を削除してください") is False,
    )

    return failures


def check_exact_keyword_set_equivalence():
    """各ファイルの実効キーワード集合が、リファクタリング前と完全一致することを確認する。"""
    from core.reading_keywords import (
        BASE_PC_OPERATION_KEYWORDS,
        BASE_READING_INTENT_KEYWORDS,
        EXCEL_DOCUMENT_KEYWORDS,
        PDF_TO_FILE_KEYWORDS,
        WORD_DOCUMENT_KEYWORDS,
    )

    def union(*keyword_lists):
        merged = set()
        for keywords in keyword_lists:
            merged.update(keywords)
        return merged

    failures = 0

    original_input_analyzer_file_creation = {
        "Word file", "Word document", "word document", "in Word", "Wordで",
        "ワード文書", "ワードで", "ワードファイル", "文書", "レポート", "資料",
        "PDFにして", "pdfにして", "文章にして",
    }
    new_input_analyzer_file_creation = union(
        WORD_DOCUMENT_KEYWORDS, ["文書", "レポート", "資料"], PDF_TO_FILE_KEYWORDS, ["文章にして"]
    )
    failures += check_true(
        "input_analyzer file-creation keyword set is byte-for-byte unchanged",
        original_input_analyzer_file_creation == new_input_analyzer_file_creation,
    )

    original_capability_manager_doc_creation = {
        "Word file", "Word document", "word document", "in Word", "Wordで",
        "ワード文書", "ワードで", "ワードファイル", "Excel file", "Excel document",
        "excel document", "in Excel", "エクセル", "PDFにして", "pdfにして",
        "Markdownファイル", "mdファイル", "ファイルを作って", "表を作って",
    }
    new_capability_manager_doc_creation = union(
        WORD_DOCUMENT_KEYWORDS,
        EXCEL_DOCUMENT_KEYWORDS,
        PDF_TO_FILE_KEYWORDS,
        ["Markdownファイル", "mdファイル", "ファイルを作って", "表を作って"],
    )
    failures += check_true(
        "capability_manager document-creation keyword set is byte-for-byte unchanged",
        original_capability_manager_doc_creation == new_capability_manager_doc_creation,
    )

    original_capability_manager_pc = {
        "VS Codeを開", "vscodeを開", "PowerShellで実行", "powershellで実行",
        "ブラウザを操作", "アプリを開", "PCを操作", "パソコンを操作", "コマンドを実行",
    }
    new_capability_manager_pc = union(
        ["VS Codeを開", "vscodeを開"], BASE_PC_OPERATION_KEYWORDS, ["アプリを開"]
    )
    failures += check_true(
        "capability_manager pc-operation keyword set is byte-for-byte unchanged",
        original_capability_manager_pc == new_capability_manager_pc,
    )

    original_capability_manager_reading = {
        "読んで", "読み取", "要約", "まとめ", "内容", "見て", "説明して", "解析", "文字起こし",
    }
    new_capability_manager_reading = union(BASE_READING_INTENT_KEYWORDS, ["文字起こし"])
    failures += check_true(
        "capability_manager reading-intent keyword set is byte-for-byte unchanged",
        original_capability_manager_reading == new_capability_manager_reading,
    )

    return failures


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"
    core = PROJECT_ROOT / "core"

    files = [
        ("reading_keywords.py", core / "reading_keywords.py"),
        ("input_analyzer.py", core / "input_analyzer.py"),
        ("capability_manager.py", core / "capability_manager.py"),
        ("check_ver2660.py", scripts / "check_ver2660.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_imports()
    failures += check_three_files_use_shared_module()
    failures += check_behavior_unchanged_input_analyzer()
    failures += check_behavior_unchanged_capability_manager()
    failures += check_exact_keyword_set_equivalence()

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        ["check_ver2660.py"],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        ["## Version 2.66", "scripts/check_ver2660.py"],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        ["現在バージョン:", "Ver2.66:"],
    )

    failures += check_check_script_has_no_forbidden_words()
    failures += check_db_unchanged(db_timestamp_before)

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
