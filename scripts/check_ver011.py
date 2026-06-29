import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.executor import Executor
from core.input_analyzer import InputAnalyzer
from core.planner import Planner
from core.router import Router


def build_plan(text):
    analyzer = InputAnalyzer()
    planner = Planner()
    input_analysis = analyzer.analyze(text)
    return planner.create_plan(text, context=input_analysis)


def check_action(label, text, expected_action):
    plan = build_plan(text)

    if plan.action == expected_action:
        print(f"[OK] {label} -> {expected_action}")
        return 0

    print(f"[NG] {label} -> expected {expected_action}, got {plan.action}")
    return 1


def check_route(label, text, expected_target):
    plan = build_plan(text)
    route = Router().route(plan)

    if route.target == expected_target:
        print(f"[OK] {label} route -> {expected_target}")
        return 0

    print(f"[NG] {label} route -> expected {expected_target}, got {route.target}")
    return 1


def check_executor(label, text, expected_text):
    plan = build_plan(text)
    route = Router().route(plan)
    response = Executor().execute(plan, route, [])

    if expected_text in response:
        print(f"[OK] {label} executor response")
        return 0

    print(f"[NG] {label} executor response did not contain: {expected_text}")
    print(response)
    return 1


def main():
    failures = 0

    # Ver0.10 behavior should stay the same.
    failures += check_action(
        "YouTube URL summarize",
        "https://youtube.com/watch?v=abc をまとめて",
        "summarize_youtube",
    )
    failures += check_action(
        "URL summarize",
        "https://example.com を要約して",
        "summarize_url",
    )
    failures += check_action(
        "Create document",
        "この内容をレポートにして",
        "create_document",
    )
    failures += check_action(
        "Recommend",
        "おすすめの候補を提案して",
        "recommend",
    )
    failures += check_action(
        "Question",
        "Pythonはどうすれば勉強できますか？",
        "answer_question",
    )
    failures += check_action(
        "Memory read",
        "私の名前は？",
        "memory_read",
    )
    failures += check_action(
        "Memory write",
        "私の好きな食べ物はカレーです。覚えて",
        "memory_write",
    )

    # Ver0.11 clarification checks.
    failures += check_action(
        "Missing YouTube URL",
        "YouTubeをまとめて",
        "ask_clarification",
    )
    failures += check_action(
        "Missing video URL",
        "この動画を要約して",
        "ask_clarification",
    )
    failures += check_action(
        "Missing Web URL",
        "このサイトを要約して",
        "ask_clarification",
    )
    failures += check_action(
        "Missing Web page URL",
        "Webページの内容を教えて",
        "ask_clarification",
    )
    failures += check_action(
        "Missing PDF target",
        "PDFを要約して",
        "ask_clarification",
    )
    failures += check_action(
        "Missing image target",
        "この画像について説明して",
        "ask_clarification",
    )

    failures += check_route(
        "Clarification",
        "YouTubeをまとめて",
        "qwen",
    )

    failures += check_executor(
        "Missing YouTube URL",
        "YouTubeをまとめて",
        "動画のURLを送ってください",
    )
    failures += check_executor(
        "Missing Web URL",
        "このサイトを要約して",
        "要約したいページのURLを送ってください",
    )
    failures += check_executor(
        "Missing PDF target",
        "PDFを要約して",
        "読み取りたいファイルやURLを送ってください",
    )

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
