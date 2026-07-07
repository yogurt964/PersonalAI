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
    return check_true("check_ver2630 does not write DB", before == after)


def check_check_script_has_no_forbidden_words():
    source = (PROJECT_ROOT / "scripts" / "check_ver2630.py").read_text(encoding="utf-8")
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
        print(f"[NG] check_ver2630 has forbidden words -> {found_words}")
        return 1

    print("[OK] check_ver2630 has no forbidden words")
    return 0


def check_imports():
    try:
        from core.web_search_intent import needs_web_search, PRODUCT_AND_PRICING_MARKERS
        from ai.llm import SYSTEM_PROMPT
    except Exception as error:
        print(f"[NG] imports failed -> {error}")
        return 1

    needs_web_search
    PRODUCT_AND_PRICING_MARKERS
    SYSTEM_PROMPT

    print("[OK] imports")
    return 0


def check_system_prompt_confidence_guardrail():
    from ai.llm import SYSTEM_PROMPT

    failures = 0
    failures += check_true(
        "SYSTEM_PROMPT forbids fabricating specific product/price/URL facts",
        "断定的に作り出さない" in SYSTEM_PROMPT,
    )
    failures += check_true(
        "SYSTEM_PROMPT asks to distinguish confidence levels",
        "現在情報の確認が必要なこと" in SYSTEM_PROMPT,
    )

    return failures


def check_product_pricing_queries_now_need_web_search():
    """実機テストで見つかった、商品・価格・実在リンクを伴う相談がWeb検索対象外だった
    問題が解消されていることを確認する（Qwenが実在しない価格・商品を断定していた事象）。
    """
    from core.web_search_intent import needs_web_search

    failures = 0

    # 実機で実際にハルシネーションが起きた入力そのもの。
    failures += check_true(
        "budget-bearing PC request now needs web search",
        needs_web_search("AIを自作しているのでそれができるPCが欲しいです。デスクトップで予算は２０万ほどです")
        is True,
    )
    failures += check_true(
        "explicit real-product request now needs web search",
        needs_web_search("具体的な構成例とすでに組んである実際の商品を教えてください") is True,
    )
    failures += check_true(
        "price comparison request needs web search",
        needs_web_search("この2つの製品の価格を比較して") is True,
    )
    failures += check_true(
        "ranking request needs web search",
        needs_web_search("おすすめのイヤホンランキングを教えて") is True,
    )
    failures += check_true(
        "sale/stock request needs web search",
        needs_web_search("このモデルの在庫とセール情報を教えて") is True,
    )

    # 既存の判定（Ver2.58）は壊れていない。
    failures += check_true(
        "existing current-info marker still works",
        needs_web_search("今日の東京の天気を教えて") is True,
    )
    failures += check_true(
        "existing explicit search phrase still works",
        needs_web_search("最近のAIニュースを調べて") is True,
    )

    # 単なる雑談・一般知識・目的未確定の最初の相談は、引き続きWeb検索対象外
    # （用途・予算などのヒアリングをQwenに任せる、既存の良い挙動を壊さない）。
    failures += check_true(
        "casual chat is still not detected",
        needs_web_search("こんにちは、元気ですか") is False,
    )
    failures += check_true(
        "general knowledge question is still not detected",
        needs_web_search("フェルマーの最終定理について解説して") is False,
    )
    failures += check_true(
        "vague first-ask recommendation request is still not detected (clarification first)",
        needs_web_search("AI開発用に20万円でおすすめのデスクトップPCを教えて") is False,
    )

    return failures


def main():
    failures = 0
    db_timestamp_before = get_db_timestamp()

    docs = PROJECT_ROOT / "docs"
    scripts = PROJECT_ROOT / "scripts"
    core = PROJECT_ROOT / "core"
    ai_dir = PROJECT_ROOT / "ai"

    files = [
        ("web_search_intent.py", core / "web_search_intent.py"),
        ("llm.py", ai_dir / "llm.py"),
        ("check_ver2630.py", scripts / "check_ver2630.py"),
        ("run_ver2_checks.py", scripts / "run_ver2_checks.py"),
        ("changelog.md", docs / "changelog.md"),
        ("project_handoff.md", docs / "project_handoff.md"),
    ]

    for label, path in files:
        failures += check_file_exists(label, path)

    failures += check_imports()
    failures += check_system_prompt_confidence_guardrail()
    failures += check_product_pricing_queries_now_need_web_search()

    failures += check_words(
        "run_ver2_checks.py",
        scripts / "run_ver2_checks.py",
        [
            "check_ver2630.py",
        ],
    )

    failures += check_words(
        "changelog.md",
        docs / "changelog.md",
        [
            "## Version 2.63",
            "scripts/check_ver2630.py",
        ],
    )

    failures += check_words(
        "project_handoff.md",
        docs / "project_handoff.md",
        [
            "現在バージョン:",
            "Ver2.63:",
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
