from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ToolRequest:
    """将来のTool / Adapterへ渡す依頼内容です。"""

    tool_name: str
    action: str
    input_data: Dict[str, Any] = field(default_factory=dict)
    # Ver1.5のTool Permission判定で、実行前確認が必要かを判断するために使います。
    requires_permission: bool = True
    # none / low / medium / high / critical などの危険度を入れます。
    risk_level: str = "low"


@dataclass
class ToolResult:
    """Tool / Adapterの実行結果を共通形式で表します。"""

    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    executed: bool = False


@dataclass
class ToolAdapter:
    """将来の各Adapterが合わせる共通インターフェースです。"""

    name: str
    description: str = ""

    def is_available(self):
        """実際に使えるAdapterかどうかを返します。"""
        return False

    def execute(self, request):
        """Tool実行の入口です。基底クラスでは実処理を行いません。"""
        return ToolResult(
            success=False,
            message=f"{self.name} はまだ実行処理が実装されていません。",
            error="not_implemented",
            executed=False,
        )


class UnimplementedToolAdapter(ToolAdapter):
    """未実装Toolを、実行したふりをせず安全に扱うAdapterです。"""

    def is_available(self):
        return False

    def execute(self, request):
        tool_name = getattr(request, "tool_name", self.name)

        return ToolResult(
            success=False,
            message=f"{tool_name} はまだ未実装です。このToolは実行していません。",
            data=None,
            error="unimplemented_tool",
            executed=False,
        )
