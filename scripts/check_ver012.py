import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.input_analyzer import InputAnalyzer
from core.models import Plan
from core.permission_manager import PermissionManager
from core.planner import Planner
from core.router import Router


def build_plan(text):
    analyzer = InputAnalyzer()
    planner = Planner()
    input_analysis = analyzer.analyze(text)
    return planner.create_plan(text, context=input_analysis)


def build_permission_decision(text):
    plan = build_plan(text)
    route = Router().route(plan)
    decision = PermissionManager().evaluate(plan, route)
    return plan, decision


def check_flow(label, text, expected_action, expected_blocked):
    plan, decision = build_permission_decision(text)

    if plan.action != expected_action:
        print(f"[NG] {label} action -> expected {expected_action}, got {plan.action}")
        return 1

    if decision["blocked"] != expected_blocked:
        print(
            f"[NG] {label} blocked -> expected {expected_blocked}, "
            f"got {decision['blocked']}"
        )
        return 1

    print(f"[OK] {label} -> {expected_action}, blocked={expected_blocked}")
    return 0


def check_permission(label, action, expected_risk):
    decision = PermissionManager().evaluate(Plan(action=action))

    if not decision["requires_permission"]:
        print(f"[NG] {label} requires_permission -> expected True, got False")
        return 1

    if decision["risk"] != expected_risk:
        print(f"[NG] {label} risk -> expected {expected_risk}, got {decision['risk']}")
        return 1

    if not decision["blocked"]:
        print(f"[NG] {label} blocked -> expected True, got False")
        return 1

    print(f"[OK] {label} -> risk={expected_risk}, blocked=True")
    return 0


def main():
    failures = 0

    # Ver0.10 / Ver0.11 behavior should remain unblocked.
    flow_cases = [
        (
            "YouTube URL summarize",
            "https://youtube.com/watch?v=abc をまとめて",
            "summarize_youtube",
            False,
        ),
        (
            "URL summarize",
            "https://example.com を要約して",
            "summarize_url",
            False,
        ),
        (
            "Create document",
            "この内容をレポートにして",
            "create_document",
            False,
        ),
        (
            "Recommend",
            "おすすめの候補を提案して",
            "recommend",
            False,
        ),
        (
            "Question",
            "Pythonはどうすれば勉強できますか？",
            "answer_question",
            False,
        ),
        (
            "Memory read",
            "私の名前は？",
            "memory_read",
            False,
        ),
        (
            "Memory write",
            "私の好きな食べ物はカレーです。覚えて",
            "memory_write",
            False,
        ),
        (
            "Clarification",
            "YouTubeをまとめて",
            "ask_clarification",
            False,
        ),
    ]

    for label, text, expected_action, expected_blocked in flow_cases:
        failures += check_flow(label, text, expected_action, expected_blocked)

    medium_risk_actions = [
        "read_file",
        "create_file",
        "edit_file",
        "read_web",
        "create_pdf",
        "run_test",
    ]

    for action in medium_risk_actions:
        failures += check_permission(action, action, "medium")

    high_risk_actions = [
        "delete_file",
        "overwrite_file",
        "send_external",
        "git_push",
        "run_command",
        "pc_control",
        "handle_personal_info",
    ]

    for action in high_risk_actions:
        failures += check_permission(action, action, "high")

    failures += check_permission(
        "unknown_future_action",
        "unknown_future_action",
        "medium",
    )

    from core.personal_ai import PersonalAI

    PersonalAI
    print("[OK] PersonalAI import")

    if failures:
        print(f"{failures} checks failed.")
        raise SystemExit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()
