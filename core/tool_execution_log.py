from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4


@dataclass
class ToolExecutionRecord:
    """Tool実行、dry-run、未実装Tool確認を記録するための1件分のログです。"""

    record_id: str = field(default_factory=lambda: str(uuid4()))
    tool_name: str = ""
    action: str = ""
    risk_level: str = "unknown"
    requires_permission: bool = False
    permission_needed: bool = False
    permission_allowed: bool = False
    adapter_available: bool = False
    attempted: bool = False
    executed: bool = False
    success: bool = False
    message: str = ""
    error: Optional[str] = None
    original_input: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    data: Optional[dict] = None

    def to_dict(self):
        """将来DB保存やデバッグ表示をしやすいdict形式にします。"""
        return {
            "record_id": self.record_id,
            "tool_name": self.tool_name,
            "action": self.action,
            "risk_level": self.risk_level,
            "requires_permission": self.requires_permission,
            "permission_needed": self.permission_needed,
            "permission_allowed": self.permission_allowed,
            "adapter_available": self.adapter_available,
            "attempted": self.attempted,
            "executed": self.executed,
            "success": self.success,
            "message": self.message,
            "error": self.error,
            "original_input": self.original_input,
            "created_at": self.created_at,
            "data": self.data,
        }


class ToolExecutionLogger:
    """ToolExecutionRecordをインメモリで一時的に保持する軽量ロガーです。"""

    def __init__(self):
        self._records = []

    def add(self, record):
        """recordを追加し、追加したrecordを返します。"""
        self._records.append(record)
        return record

    def list_records(self):
        """記録済みrecordをlistで返します。"""
        return list(self._records)

    def latest(self):
        """最後に追加されたrecordを返します。空ならNoneです。"""
        if not self._records:
            return None

        return self._records[-1]

    def clear(self):
        """インメモリのrecordをすべて消します。DBやMemoryには触りません。"""
        self._records.clear()

    def count(self):
        """記録済みrecord数を返します。"""
        return len(self._records)


def build_tool_execution_record(
    request,
    permission_decision=None,
    result=None,
    adapter_available=False,
    original_input=None,
    attempted=False,
):
    """ToolRequest、Permission判定、ToolResultを1つのログrecordにまとめます。

    resultがない場合は、Toolは未実行として recorded します。
    Ver1.7ではDB保存も外部Tool実行も行いません。
    """
    permission_needed = _get_value(permission_decision, "needs_user_confirmation", False)
    permission_allowed = _get_value(permission_decision, "allowed", False)
    risk_level = _get_value(permission_decision, "risk_level", _get_value(request, "risk_level", "unknown"))

    if result is None:
        success = False
        executed = False
        message = "未実行: Toolは実行していません。"
        error = None
        data = None
    else:
        success = bool(_get_value(result, "success", False))
        executed = bool(_get_value(result, "executed", False))
        message = _get_value(result, "message", "")
        error = _get_value(result, "error")
        data = _get_value(result, "data")

        if not executed and not message:
            message = "未実行: Toolは実行していません。"

    if original_input is None:
        input_data = _get_value(request, "input_data", {}) or {}
        original_input = input_data.get("original_input")

    return ToolExecutionRecord(
        tool_name=_get_value(request, "tool_name", "unknown_tool"),
        action=_get_value(request, "action", "unknown_action"),
        risk_level=risk_level,
        requires_permission=bool(_get_value(request, "requires_permission", True)),
        permission_needed=bool(permission_needed),
        permission_allowed=bool(permission_allowed),
        adapter_available=bool(adapter_available),
        attempted=bool(attempted),
        executed=executed,
        success=success,
        message=message,
        error=error,
        original_input=original_input,
        data=data,
    )


def _get_value(obj, key, default=None):
    """dataclass風オブジェクトとdictの両方から値を取り出します。"""
    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(key, default)

    return getattr(obj, key, default)
