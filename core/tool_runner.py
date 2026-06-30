from dataclasses import dataclass

from core.tool_adapter import ToolResult
from core.tool_execution_log import build_tool_execution_record
from core.tool_permission import build_permission_message, evaluate_tool_permission
from core.tool_registry import ToolRegistry


@dataclass
class ToolRunResult:
    """ToolRequestを実行または未実行にした結果をまとめる入れ物です。"""

    request: object
    permission_decision: object
    result: ToolResult
    execution_record: object


def run_tool_request(
    request,
    registry=None,
    permission_manager=None,
    user_confirmed=False,
    logger=None,
):
    """Permissionを確認してからToolRequestを実行します。

    medium以上のToolは、user_confirmed=True がない限り実行しません。
    """
    registry = registry or ToolRegistry()
    permission_decision = evaluate_tool_permission(
        request,
        permission_manager=permission_manager,
    )
    adapter = registry.get(getattr(request, "tool_name", "unknown_tool"))
    adapter_available = bool(adapter.is_available())
    attempted = False

    if permission_decision.needs_user_confirmation and not user_confirmed:
        result = ToolResult(
            success=False,
            message=(
                build_permission_message(permission_decision, request)
                + " 確認が必要なため、未許可なら実行しない方針で停止しました。"
            ),
            data=None,
            error="permission_required",
            executed=False,
        )
    elif not permission_decision.allowed:
        result = ToolResult(
            success=False,
            message="Permission判定で許可されなかったため、Toolは実行していません。",
            data=None,
            error="permission_denied",
            executed=False,
        )
    elif not adapter_available:
        result = ToolResult(
            success=False,
            message="Adapterが未実装または利用不可のため、Toolは実行していません。",
            data=None,
            error="adapter_unavailable",
            executed=False,
        )
    else:
        attempted = True
        try:
            result = adapter.execute(request)
        except Exception as error:
            result = ToolResult(
                success=False,
                message="Tool実行中にエラーが発生しました。できたふりはしません。",
                data=None,
                error=str(error),
                executed=False,
            )

    execution_record = build_tool_execution_record(
        request,
        permission_decision=permission_decision,
        result=result,
        adapter_available=adapter_available,
        attempted=attempted,
    )

    if logger is not None:
        logger.add(execution_record)

    return ToolRunResult(
        request=request,
        permission_decision=permission_decision,
        result=result,
        execution_record=execution_record,
    )
