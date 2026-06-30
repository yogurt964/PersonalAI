from dataclasses import dataclass
from typing import Optional

from core.tool_permission import build_permission_message, evaluate_tool_permission
from core.tool_registry import ToolRegistry
from core.tool_request_builder import build_tool_request_decision


@dataclass
class ToolFlowPreview:
    """Tool実行前のdry-run結果です。実際のTool実行は含みません。"""

    requires_tool: bool
    tool_name: Optional[str]
    action: Optional[str]
    adapter_available: bool
    permission_needed: bool
    risk_level: str
    should_execute: bool = False
    executed: bool = False
    message: str = ""

    def to_dict(self):
        """確認スクリプトやデバッグで扱いやすいdictにします。"""
        return {
            "requires_tool": self.requires_tool,
            "tool_name": self.tool_name,
            "action": self.action,
            "adapter_available": self.adapter_available,
            "permission_needed": self.permission_needed,
            "risk_level": self.risk_level,
            "should_execute": self.should_execute,
            "executed": self.executed,
            "message": self.message,
        }


def build_tool_flow_preview(
    user_input,
    input_analysis=None,
    capability_result=None,
    registry=None,
    permission_manager=None,
):
    """入力からTool実行前のdry-run情報を作ります。

    ToolRegistryからAdapterは取得しますが、executeは絶対に呼びません。
    Ver1.6以降では、必要そうなToolと許可確認の必要性だけを確認します。
    Ver1.7で追加したToolExecutionRecordへ、将来このpreview結果を記録できます。
    """
    request_decision = build_tool_request_decision(
        user_input,
        input_analysis=input_analysis,
        capability_result=capability_result,
    )

    if not request_decision.requires_tool:
        return ToolFlowPreview(
            requires_tool=False,
            tool_name=None,
            action=None,
            adapter_available=False,
            permission_needed=False,
            risk_level="none",
            should_execute=False,
            executed=False,
            message=request_decision.reason,
        )

    tool_request = request_decision.tool_request
    registry = registry or ToolRegistry()
    adapter = registry.get(tool_request.tool_name)
    permission_decision = evaluate_tool_permission(
        tool_request,
        permission_manager=permission_manager,
    )

    return ToolFlowPreview(
        requires_tool=True,
        tool_name=tool_request.tool_name,
        action=tool_request.action,
        adapter_available=adapter.is_available(),
        permission_needed=permission_decision.needs_user_confirmation,
        risk_level=permission_decision.risk_level,
        should_execute=False,
        executed=False,
        message=build_permission_message(permission_decision, tool_request),
    )
