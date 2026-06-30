from dataclasses import dataclass


@dataclass
class ToolPermissionDecision:
    """Toolを実行する前の安全判定結果です。"""

    allowed: bool
    needs_user_confirmation: bool
    risk_level: str
    reason: str
    executed: bool = False


def evaluate_tool_permission(request, permission_manager=None):
    """ToolRequestを見て、実行前に確認が必要かを判定します。

    Ver1.5では実際のTool実行は行いません。
    そのため、判定上allowed=Trueでも executed は常にFalseのままです。
    """
    risk_level = _normalize_risk_level(getattr(request, "risk_level", "unknown"))
    requires_permission = bool(getattr(request, "requires_permission", True))

    manager_reason = _get_permission_manager_reason(permission_manager, request)

    if risk_level == "none":
        return ToolPermissionDecision(
            allowed=True,
            needs_user_confirmation=False,
            risk_level=risk_level,
            reason=_join_reason("実行を伴わない説明のみのため、確認は不要です", manager_reason),
            executed=False,
        )

    if risk_level == "low" and not requires_permission:
        return ToolPermissionDecision(
            allowed=True,
            needs_user_confirmation=False,
            risk_level=risk_level,
            reason=_join_reason("低リスクで、明示的な許可を必要としない依頼です", manager_reason),
            executed=False,
        )

    if risk_level == "critical":
        return ToolPermissionDecision(
            allowed=False,
            needs_user_confirmation=True,
            risk_level=risk_level,
            reason=_join_reason("重大リスク操作のため、原則ブロックまたは強い確認が必要です", manager_reason),
            executed=False,
        )

    if risk_level in {"medium", "high"}:
        return ToolPermissionDecision(
            allowed=True,
            needs_user_confirmation=True,
            risk_level=risk_level,
            reason=_join_reason(f"{risk_level}リスク操作のため、実行前にユーザー確認が必要です", manager_reason),
            executed=False,
        )

    if risk_level == "low" and requires_permission:
        return ToolPermissionDecision(
            allowed=True,
            needs_user_confirmation=True,
            risk_level=risk_level,
            reason=_join_reason("低リスクですが、ToolRequestで許可確認が必要とされています", manager_reason),
            executed=False,
        )

    return ToolPermissionDecision(
        allowed=False,
        needs_user_confirmation=True,
        risk_level=risk_level,
        reason=_join_reason("未知のrisk_levelのため、安全側に倒して確認が必要です", manager_reason),
        executed=False,
    )


def build_permission_message(decision, request):
    """ユーザーにTool実行前確認を出すための短い説明文を作ります。"""
    tool_name = getattr(request, "tool_name", "unknown_tool")
    action = getattr(request, "action", "unknown_action")
    confirmation_text = "確認が必要です" if decision.needs_user_confirmation else "確認は不要です"
    allowed_text = "未許可なら実行しないため、許可されるまで実行しません" if decision.needs_user_confirmation else "この判定だけでは実行しません"

    if not decision.allowed:
        allowed_text = "未許可なら実行しないため、この段階では実行しません"

    return (
        f"Tool '{tool_name}' で action '{action}' を行おうとしています。"
        f"risk_level は {decision.risk_level} です。"
        f"{confirmation_text}。{allowed_text}。"
    )


def _normalize_risk_level(risk_level):
    """risk_levelを比較しやすい文字列に整えます。"""
    if risk_level is None:
        return "unknown"

    normalized = str(risk_level).strip().lower()

    if normalized in {"none", "low", "medium", "high", "critical"}:
        return normalized

    return "unknown"


def _get_permission_manager_reason(permission_manager, request):
    """既存PermissionManagerが渡された場合だけ、補足理由を取得します。"""
    if permission_manager is None or not hasattr(permission_manager, "evaluate"):
        return ""

    try:
        result = permission_manager.evaluate(action=getattr(request, "action", None))
    except Exception:
        return ""

    if not isinstance(result, dict):
        return ""

    return result.get("reason", "")


def _join_reason(primary_reason, extra_reason):
    """主理由に、既存PermissionManagerの補足があれば足します。"""
    if not extra_reason:
        return primary_reason

    return f"{primary_reason} / PermissionManager: {extra_reason}"
