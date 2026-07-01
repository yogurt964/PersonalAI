import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.capability_manager import CapabilityManager
from core.input_analyzer import InputAnalyzer
from core.personal_ai import PersonalAI


def analyze(text):
    analyzer = InputAnalyzer()
    manager = CapabilityManager()
    input_analysis = analyzer.analyze(text)
    return manager.analyze(text, input_analysis)


def check_imports():
    CapabilityManager
    PersonalAI
    print("[OK] imports")
    return 0


def check_capability(label, text, expected_can_handle, expected_primary):
    result = analyze(text)

    if result["can_handle_now"] != expected_can_handle:
        print(
            f"[NG] {label} can_handle_now -> "
            f"expected {expected_can_handle}, got {result['can_handle_now']}"
        )
        return 1

    if result["primary_capability"] != expected_primary:
        print(
            f"[NG] {label} primary_capability -> "
            f"expected {expected_primary}, got {result['primary_capability']}"
        )
        return 1

    print(f"[OK] {label} -> {expected_primary}")
    return 0


def check_includes(label, text, key, expected_values):
    result = analyze(text)
    values = result.get(key, [])
    missing_values = [
        expected_value
        for expected_value in expected_values
        if expected_value not in values
    ]

    if missing_values:
        print(f"[NG] {label} {key} missing -> {missing_values}")
        print(result)
        return 1

    print(f"[OK] {label} {key}")
    return 0


def check_risk(label, text, expected_risk):
    result = analyze(text)

    if result["risk_level"] != expected_risk:
        print(f"[NG] {label} risk_level -> expected {expected_risk}, got {result['risk_level']}")
        return 1

    print(f"[OK] {label} risk -> {expected_risk}")
    return 0


def check_personal_ai_url_confirmation_dry_run():
    ai = PersonalAI()
    ai.save_user_message = lambda _message: None
    ai.save_assistant_message = lambda _message: None

    response = ai.handle_user_input("https://example.com を要約して")

    if "Web Readerで読み取ってもよいですか" not in response:
        print(f"[NG] PersonalAI URL response -> {response}")
        return 1

    if "https://example.com" not in response:
        print(f"[NG] PersonalAI URL response missing URL -> {response}")
        return 1

    if "外部Webへアクセス" not in response or "確認が必要" not in response:
        print(f"[NG] PersonalAI URL response missing confirmation wording -> {response}")
        return 1

    if ai.last_web_reader_confirmation is None:
        print("[NG] PersonalAI last_web_reader_confirmation was not set")
        return 1

    if not ai.pending_web_reader_confirmation:
        print("[NG] PersonalAI pending_web_reader_confirmation was not set")
        return 1

    print("[OK] PersonalAI returns Web Reader confirmation dry-run")
    return 0


def main():
    failures = 0

    failures += check_imports()
    failures += check_capability(
        "normal conversation",
        "こんにちは",
        True,
        "local_conversation",
    )
    failures += check_capability(
        "preference memory",
        "私はラーメンが好きです。覚えて",
        True,
        "memory_write",
    )
    failures += check_includes(
        "preference memory",
        "私はラーメンが好きです。覚えて",
        "required_capabilities",
        ["memory_write", "preference_memory"],
    )
    failures += check_capability(
        "URL summarize",
        "https://example.com を要約して",
        False,
        "web_read_required",
    )
    failures += check_includes(
        "URL summarize",
        "https://example.com を要約して",
        "missing_capabilities",
        ["web_reader"],
    )
    failures += check_capability(
        "YouTube summarize",
        "https://youtube.com/watch?v=xxxx を要約して",
        False,
        "youtube_read_required",
    )
    failures += check_includes(
        "YouTube summarize",
        "https://youtube.com/watch?v=xxxx を要約して",
        "missing_capabilities",
        ["youtube_reader"],
    )
    failures += check_capability(
        "PDF read",
        "このPDFを読んで要約して",
        False,
        "pdf_read_required",
    )
    failures += check_includes(
        "PDF read",
        "このPDFを読んで要約して",
        "missing_capabilities",
        ["pdf_reader"],
    )
    failures += check_capability(
        "image read",
        "この画像を見て説明して",
        False,
        "image_read_required",
    )
    failures += check_includes(
        "image read",
        "この画像を見て説明して",
        "missing_capabilities",
        ["image_reader"],
    )

    for label, text in [
        ("Word creation", "Wordでまとめて"),
        ("Excel creation", "Excel表を作って"),
        ("PDF creation", "PDFにして"),
    ]:
        failures += check_capability(label, text, False, "document_creation_required")
        failures += check_includes(label, text, "missing_capabilities", ["document_creator"])

    for label, text in [
        ("VS Code operation", "VS Codeを開いて"),
        ("PowerShell operation", "PowerShellで実行して"),
        ("Browser operation", "ブラウザを操作して"),
    ]:
        failures += check_capability(label, text, False, "pc_operation_required")
        failures += check_includes(label, text, "missing_capabilities", ["pc_operator"])
        failures += check_risk(label, text, "high")

    for label, text in [
        ("medical accuracy", "医学的に安全か正確に判断して"),
        ("legal accuracy", "法律的に問題ないか判断して"),
        ("paper accuracy", "論文レベルで厳密に比較して"),
    ]:
        failures += check_capability(label, text, False, "openai_required")
        failures += check_includes(label, text, "missing_capabilities", ["openai"])

    failures += check_personal_ai_url_confirmation_dry_run()

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
