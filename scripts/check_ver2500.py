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
    return check_true("check_ver2500 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2500.py").read_text(encoding="utf-8")
    forbidden_words = [
        "req" + "uests.get",
        "req" + "uests.post",
        "ask_" + "llm(",
        "reset --" + "hard",
        "force " + "push",
        "re" + "base",
    ]
    found_words = [word for word in forbidden_words if word in source]

    if found_words:
        print(f"[NG] check_ver2500 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2500 has no forbidden words")
    return 0


# 各Readerの単一ファイル時の挙動が、Ver2.50以前と完全に同じであることを確認する。
def check_single_file_confirmations_unchanged():
    from core.pdf_reader_confirmation import build_pdf_reader_confirmation
    from core.word_reader_confirmation import build_word_reader_confirmation
    from core.excel_reader_confirmation import build_excel_reader_confirmation
    from core.pptx_reader_confirmation import build_pptx_reader_confirmation
    from core.image_reader_confirmation import build_image_reader_confirmation

    failures = 0

    cases = [
        (build_pdf_reader_confirmation, "report.pdf", "read_pdf", "PDF"),
        (build_word_reader_confirmation, "note.docx", "read_word", "Word"),
        (build_excel_reader_confirmation, "data.xlsx", "read_excel", "Excel"),
        (build_pptx_reader_confirmation, "slide.pptx", "read_pptx", "PowerPoint"),
        (build_image_reader_confirmation, "photo.png", "read_image", "Image"),
    ]

    for builder, filename, expected_action, label in cases:
        confirmation = builder(f"このファイルを読んで {filename}")
        failures += check_true(f"{label} single-file action unchanged", confirmation.action == expected_action)
        failures += check_true(f"{label} single-file path set", confirmation.path == filename)
        failures += check_true(f"{label} single-file paths list has one entry", confirmation.paths == [filename])

    return failures


def check_multi_file_confirmations():
    from core.pdf_reader_confirmation import build_pdf_reader_confirmation
    from core.word_reader_confirmation import build_word_reader_confirmation
    from core.excel_reader_confirmation import build_excel_reader_confirmation
    from core.pptx_reader_confirmation import build_pptx_reader_confirmation
    from core.image_reader_confirmation import build_image_reader_confirmation

    failures = 0

    cases = [
        (build_pdf_reader_confirmation, ["a.pdf", "b.pdf"], "read_pdfs", "PDF"),
        (build_word_reader_confirmation, ["a.docx", "b.docx"], "read_words", "Word"),
        (build_excel_reader_confirmation, ["a.xlsx", "b.xlsx"], "read_excels", "Excel"),
        (build_pptx_reader_confirmation, ["a.pptx", "b.pptx"], "read_pptxs", "PowerPoint"),
        (build_image_reader_confirmation, ["a.png", "b.jpg"], "read_images", "Image"),
    ]

    for builder, filenames, expected_action, label in cases:
        text = " ".join(filenames) + " を読んで"
        confirmation = builder(text)
        failures += check_true(f"{label} multi-file needs_confirmation", confirmation.needs_confirmation is True)
        failures += check_true(f"{label} multi-file action is plural", confirmation.action == expected_action)
        failures += check_true(f"{label} multi-file paths captured", confirmation.paths == filenames)
        failures += check_true(
            f"{label} multi-file message lists all files",
            all(name in confirmation.message for name in filenames),
        )

    return failures


def _build_word_files(tmp_path):
    from docx import Document

    doc1 = Document()
    doc1.add_paragraph("WORD_MULTI_MARKER_ONE")
    path1 = tmp_path / "w1.docx"
    doc1.save(str(path1))

    doc2 = Document()
    doc2.add_paragraph("WORD_MULTI_MARKER_TWO")
    path2 = tmp_path / "w2.docx"
    doc2.save(str(path2))

    return path1, path2


def fake_llm_responder(messages):
    system_texts = [message["content"] for message in messages if message["role"] == "system"]
    both_markers = any(
        "WORD_MULTI_MARKER_ONE" in text and "WORD_MULTI_MARKER_TWO" in text for text in system_texts
    )
    return f"FAKE_LLM_ANSWER|both_markers_seen={both_markers}"


def build_lightweight_personal_ai():
    from core.capability_manager import CapabilityManager
    from core.input_analyzer import InputAnalyzer
    from core.personal_ai import PersonalAI
    from core.tool_execution_log import ToolExecutionLogger

    ai = PersonalAI.__new__(PersonalAI)
    ai.input_analyzer = InputAnalyzer()
    ai.capability_manager = CapabilityManager()
    ai.web_reader_fetcher = None
    ai.ask_llm_func = fake_llm_responder
    ai.tool_registry = ai.build_tool_registry(None)
    ai.tool_execution_logger = ToolExecutionLogger()
    ai.pending_preference_confirmation = None
    ai.pending_memory_candidate_confirmation = None
    ai.pending_memory_candidate_edit = None
    ai.pending_web_reader_confirmation = None
    ai.pending_file_reader_confirmation = None
    ai.pending_pdf_reader_confirmation = None
    ai.pending_word_reader_confirmation = None
    ai.pending_excel_reader_confirmation = None
    ai.pending_pptx_reader_confirmation = None
    ai.pending_youtube_reader_confirmation = None
    ai.pending_image_reader_confirmation = None
    for prefix in [
        "web_reader",
        "file_reader",
        "pdf_reader",
        "word_reader",
        "excel_reader",
        "pptx_reader",
        "youtube_reader",
        "image_reader",
    ]:
        setattr(ai, f"last_{prefix}_confirmation", None)
        setattr(ai, f"last_{prefix}_confirmation_result", None)
        setattr(ai, f"last_{prefix}_tool_request_candidate", None)
        setattr(ai, f"last_{prefix}_tool_run_result", None)
        setattr(ai, f"last_{prefix}_tool_result", None)
    ai.last_read_document = None
    ai.last_tool_execution_record = None
    ai.last_memory_candidate = None
    ai.last_memory_candidate_confirmation_result = None
    ai.last_memory_candidate_save_result = None
    ai.last_saved_memory_candidate_result = None
    ai.last_memory_usage = "normal"
    ai.last_conversation_mode = "chat"
    ai.last_conversation_quality_guidance = None
    ai.last_input_analysis = None
    ai.last_response = None
    ai.save_user_message = lambda _message: None
    ai.save_assistant_message = lambda _message: None
    return ai


def check_word_multi_file_end_to_end(tmp_path):
    path1, path2 = _build_word_files(tmp_path)
    failures = 0

    ai_read = build_lightweight_personal_ai()
    confirmation_response = ai_read.handle_user_input(f"{path1} {path2} を読んで")
    read_response = ai_read.handle_user_input("はい")
    failures += check_true(
        "word multi-file confirmation lists both files",
        str(path1) in confirmation_response and str(path2) in confirmation_response,
    )
    failures += check_true("word multi-file reports 2 files", "2件のファイルを読み取りました" in read_response)
    failures += check_true(
        "word multi-file combined preview includes both markers",
        "WORD_MULTI_MARKER_ONE" in read_response and "WORD_MULTI_MARKER_TWO" in read_response,
    )
    failures += check_true(
        "word multi-file last_read_document combines both names",
        ai_read.last_read_document is not None
        and "w1.docx" in ai_read.last_read_document.get("title", "")
        and "w2.docx" in ai_read.last_read_document.get("title", ""),
    )

    ai_summarize = build_lightweight_personal_ai()
    ai_summarize.handle_user_input(f"{path1} {path2} 内容を要約してください")
    summarize_response = ai_summarize.handle_user_input("はい")
    failures += check_true(
        "word multi-file combined summarize sees both files",
        "both_markers_seen=True" in summarize_response,
    )

    missing_path = tmp_path / "missing.docx"
    ai_partial = build_lightweight_personal_ai()
    ai_partial.handle_user_input(f"{path1} {missing_path} を読んで")
    partial_response = ai_partial.handle_user_input("はい")
    failures += check_true(
        "word partial failure reports 1 succeeded",
        "1件のファイルを読み取りました" in partial_response,
    )
    failures += check_true(
        "word partial failure lists missing file",
        "読み取れなかったファイル" in partial_response,
    )

    return failures


def check_image_multi_file_end_to_end(tmp_path):
    from core.tool_registry import ToolRegistry
    from core.image_reader_adapter import ImageReaderAdapter

    def fake_vision_describer(path, original_input, backend):
        return f"IMG_MARKER_{Path(path).name}"

    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\nIDATx\x9cc\xf8\xcf\xc0"
        b"\x00\x00\x03\x01\x01\x00\x18\xdd\x8d\xb0\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    path1 = tmp_path / "img1.png"
    path2 = tmp_path / "img2.png"
    path1.write_bytes(png_bytes)
    path2.write_bytes(png_bytes)

    ai = build_lightweight_personal_ai()
    registry = ToolRegistry()
    registry.register(ImageReaderAdapter(vision_describer=fake_vision_describer))
    ai.tool_registry = registry

    confirmation_response = ai.handle_user_input(f"{path1} {path2} を見て")
    read_response = ai.handle_user_input("はい")

    failures = 0
    failures += check_true(
        "image multi-file confirmation lists both files",
        str(path1) in confirmation_response and str(path2) in confirmation_response,
    )
    failures += check_true("image multi-file reports 2 images (解析)", "2件の画像を解析しました" in read_response)
    failures += check_true(
        "image multi-file combined description includes both markers",
        "IMG_MARKER_img1.png" in read_response and "IMG_MARKER_img2.png" in read_response,
    )
    failures += check_true("image multi-file uses 説明 label", "説明:" in read_response)

    return failures


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"
    core = PROJECT_ROOT / "core"

    files = [
        ("pdf_reader_confirmation.py", core / "pdf_reader_confirmation.py"),
        ("word_reader_confirmation.py", core / "word_reader_confirmation.py"),
        ("excel_reader_confirmation.py", core / "excel_reader_confirmation.py"),
        ("pptx_reader_confirmation.py", core / "pptx_reader_confirmation.py"),
        ("image_reader_confirmation.py", core / "image_reader_confirmation.py"),
        ("personal_ai.py", core / "personal_ai.py"),
        ("check_ver2500.py", scripts / "check_ver2500.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_single_file_confirmations_unchanged()
    failures += check_multi_file_confirmations()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        failures += check_word_multi_file_end_to_end(tmp_path)
        failures += check_image_multi_file_end_to_end(tmp_path)

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
            "check_ver2500.py",
        ],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        [
            "## Version 2.50",
            "scripts/check_ver2500.py",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        [
            "現在バージョン:",
            "Ver2.50:",
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
