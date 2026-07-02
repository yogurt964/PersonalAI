from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


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
    return check_true("check_ver270 does not write DB", before == after)


def check_check_script_is_docs_only():
    source = (PROJECT_ROOT / "scripts" / "check_ver270.py").read_text(encoding="utf-8")

    # 文字列を分け、チェック対象の単語がこのリスト自体に現れないようにする。
    forbidden_words = [
        "url" + "lib",
        "req" + "uests",
        "url" + "open",
        "Personal" + "AI(",
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

    found_words = [word for word in forbidden_words if word in source]

    if found_words:
        print(f"[NG] check_ver270 has forbidden execution words -> {found_words}")
        return 1

    print("[OK] check_ver270 is docs-only")
    return 0


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"

    final_vision = docs / "final_product_vision.md"
    conversation_policy = docs / "conversation_policy.md"
    project_handoff = docs / "project_handoff.md"
    changelog = docs / "changelog.md"
    check_workflow = docs / "check_workflow.md"
    check_ver270 = scripts / "check_ver270.py"
    run_ver2_checks = scripts / "run_ver2_checks.py"

    files = [
        ("final_product_vision.md", final_vision),
        ("conversation_policy.md", conversation_policy),
        ("project_handoff.md", project_handoff),
        ("changelog.md", changelog),
        ("check_workflow.md", check_workflow),
        ("check_ver270.py", check_ver270),
        ("run_ver2_checks.py", run_ver2_checks),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_words(
        "final_product_vision.md",
        final_vision,
        [
            "精度最優先",
            "高自律",
            "危険操作・機密情報・金銭操作の暴走防止",
            "自律レベル",
            "提案量",
            "重要記憶は基本忘却しない",
            "会話ログ上限で記憶が消えない設計",
            "ModelRouter / ToolRouter",
            "Qwen = ローカルLLMツール",
            "OpenAI = 高性能LLMツール",
            "Qwenに難しい判断を無理に任せない",
            "自律調査・情報収集",
            "自己アップデート方針",
            "LINE / Discord風UI",
            "KeyboardFirmwareHelper",
        ],
    )

    failures += check_words(
        "conversation_policy.md",
        conversation_policy,
        [
            "ユーザーの目的",
            "短く分かりやすく",
            "必要な確認",
            "仮決定",
            "作る",
            "試す",
            "直す",
            "テストプレイ",
            "フィードバック",
            "重要度の低い内容を無理に混ぜない",
            "できないことは代替案",
            "比較相談では結論",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        project_handoff,
        [
            "Ver2.7: 完成形ビジョンと自律・記憶・モデル選定方針整理",
            "Ver2.7で完成形ビジョンをdocs化",
            "docs/final_product_vision.md",
            "docs/conversation_policy.md",
            "高自律・記憶・ModelRouter/ToolRouter・自己アップデート・自律調査方針を整理",
            "Ver2.8: Web Reader結果の会話品質改善",
        ],
    )

    failures += check_words(
        "changelog.md",
        changelog,
        [
            "## Version 2.7",
            "完成形ビジョンをdocs化",
            "docs/final_product_vision.md",
            "docs/conversation_policy.md",
            "高自律・記憶・ModelRouter / ToolRouter・自己アップデート・自律調査方針を整理",
            "実装はまだ行わない方針を維持",
            "scripts/check_ver270.py",
        ],
    )

    failures += check_words(
        "check_workflow.md",
        check_workflow,
        [
            "scripts/check_ver270.py",
            "完成形ビジョン",
            "会話品質・返答方針",
            "実Webアクセス、DB書き込み、LLM実行、ToolRunner実行をしない",
        ],
    )

    failures += check_words(
        "run_ver2_checks.py",
        run_ver2_checks,
        [
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

    failures += check_db_unchanged(db_timestamp_before)
    failures += check_check_script_is_docs_only()

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
