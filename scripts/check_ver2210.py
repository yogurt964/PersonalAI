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
    return check_true("check_ver2210 does not write DB", before == after)


def check_check_script_is_docs_only():
    source = (PROJECT_ROOT / "scripts" / "check_ver2210.py").read_text(encoding="utf-8")
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
        print(f"[NG] check_ver2210 has forbidden execution words -> {found_words}")
        return 1

    print("[OK] check_ver2210 is docs-only")
    return 0


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"

    migration = PROJECT_ROOT / "MIGRATION.md"
    agents = PROJECT_ROOT / "AGENTS.md"
    readme = PROJECT_ROOT / "README.md"
    development_workflow = docs / "development_workflow.md"
    project_handoff = docs / "project_handoff.md"
    changelog = docs / "changelog.md"
    check_workflow = docs / "check_workflow.md"
    check_ver2210 = scripts / "check_ver2210.py"
    run_ver2_checks = scripts / "run_ver2_checks.py"

    files = [
        ("MIGRATION.md", migration),
        ("AGENTS.md", agents),
        ("README.md", readme),
        ("development_workflow.md", development_workflow),
        ("project_handoff.md", project_handoff),
        ("changelog.md", changelog),
        ("check_workflow.md", check_workflow),
        ("check_ver2210.py", check_ver2210),
        ("run_ver2_checks.py", run_ver2_checks),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_words(
        "MIGRATION.md",
        migration,
        [
            "PersonalAI",
            "Claude Code",
            "Cursor",
            "Web Reader",
            "Memory Candidate",
            "PermissionManager",
            "ToolRunner",
            "長期記憶",
            "Memory検索",
            "MIGRATION.md",
            "data/personal_ai.db",
            "DBスキーマ変更",
            "Memory物理削除",
            "git status",
            "run_ver2_checks.py",
            "ポートフォリオ",
        ],
    )

    failures += check_words(
        "MIGRATION.md final scope",
        migration,
        [
            "最終利用スコープ",
            "アプリ開発",
            "ゲーム開発",
            "資料要約",
            "資料作成",
            "Web検索",
            "データ分析",
            "勉強",
            "雑談",
            "Live2D",
            "動画制作",
            "イラスト",
            "3Dモデリング",
            "音楽制作",
            "動画生成",
            "画像生成",
            "予定管理",
            "メール",
            "画像",
            "音声",
            "YouTube",
            "PDF",
            "Word",
            "Excel",
            "PowerPoint",
            "VS Code",
            "Unity",
            "CLIP STUDIO PAINT",
            "MediBang",
            "DaVinci Resolve",
            "Adobe",
            "R",
            "Office",
            "Obsidian",
            "Qwen",
            "OpenAI",
            "例",
            "固定ではない",
            "用途や開発段階に応じて選ぶ",
        ],
    )

    failures += check_words(
        "MIGRATION.md user adaptation and failure policy",
        migration,
        [
            "ユーザー適応仕様",
            "ユーザーが好む会話パターン",
            "先回り",
            "就活ポートフォリオ",
            "動作結果",
            "使いやすさ",
            "自然さ",
            "コード差分",
            "不可逆操作",
            "致命的リスク",
            "PCが使い物にならなくなる",
            "大量の費用",
            "重要データ",
            "実用面",
            "作業相棒",
            "個人秘書",
            "自律型AI",
            "未実装機能を完成済みのように書かない",
            "開発コスト方針",
            "無駄なAPI消費",
            "同じ失敗を何度も繰り返す",
            "ログを読む",
            "必要な課金は許容",
            "開発効率",
            "AI性能",
            "完成度",
            "安定性",
            "低コストの代替案",
            "失敗時の対応方針",
            "SQLite disk I/O error",
            "timeout",
            "DBを削除しない",
            "DBを初期化しない",
            "reset --" + "hard",
            "force " + "push",
            "安全チェック",
        ],
    )

    failures += check_words(
        "AGENTS.md user adaptation and cost policy",
        agents,
        [
            "User adaptation policy",
            "Cost and failure policy",
            "Safety priority",
            "Avoid wasting API usage",
            "blind retry loops",
            "Read logs before retrying",
            "paid tools",
            "stronger models",
            "cheaper alternative",
            "delete or initialize the DB",
            "reset --" + "hard",
            "force " + "push",
            "fatal risks",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        project_handoff,
        [
            "現在バージョン:",  # version-agnostic: avoid pinning an exact VerX.X that future bumps must chase
            "Ver2.21: Claude Code移行用MIGRATION.md",
            "MIGRATION.md",
            "Claude Code",
            "Cursor",
            "最終スコープ",
            "個人用総合AIアシスタント",
            "固定ではなく",
            "細かいコード差分",
            "先回り",
            "致命的リスク",
            "大量課金",
        ],
    )

    failures += check_words(
        "changelog.md",
        changelog,
        [
            "## Version 2.21",
            "MIGRATION.md",
            "Claude Code",
            "Cursor",
            "開発環境移行",
            "引継書",
            "scripts/check_ver2210.py",
            "最終利用スコープ",
            "将来スコープ",
            "用途や開発段階に応じて選ぶ",
            "ユーザー適応仕様",
            "開発コスト方針",
            "失敗時の対応方針",
            "無駄なAPI消費",
        ],
    )

    failures += check_words(
        "check_workflow.md",
        check_workflow,
        [
            "scripts/check_ver2210.py",
            "MIGRATION.md",
            "docs確認のみ",
        ],
    )

    failures += check_words(
        "development_workflow.md",
        development_workflow,
        [
            "MIGRATION.md",
            "Claude Code",
            "Cursor",
            "Ver2.21",
            "ユーザー確認の基本方針",
            "動く結果",
            "使い心地",
            "致命的リスク",
        ],
    )

    failures += check_words(
        "README.md",
        readme,
        [
            "MIGRATION.md",
            "開発環境移行",
            "docs/project_handoff.md",
            "将来的に扱いたい領域",
            "資料要約",
            "創作支援",
            "具体的なアプリは固定せず",
            "ポートフォリオとしての位置づけ",
            "AIエージェントを設計・実装・改善",
        ],
    )

    failures += check_words(
        "run_ver2_checks.py",
        run_ver2_checks,
        [
            "scripts/check_ver2210.py",
            "scripts/check_ver2200.py",
            "scripts/check_ver2190.py",
            "scripts/run_ver1_checks.py",
            "All Ver2 checks passed",
        ],
    )

    failures += check_check_script_is_docs_only()
    failures += check_db_unchanged(db_timestamp_before)

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
