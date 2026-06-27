class Route:
    """Routerが作る処理先情報を表すデータクラスです。"""

    def __init__(
        self,
        target="qwen",
        reason="",
        model="qwen3:8b",
        tool=None,
        requires_permission=False,
        risk="low",
    ):
        self.target = target
        self.reason = reason
        self.model = model
        self.tool = tool
        self.requires_permission = requires_permission
        self.risk = risk

    def to_dict(self):
        """従来のdict形式でRouteの内容を返します。"""
        return {
            "target": self.target,
            "reason": self.reason,
            "model": self.model,
            "tool": self.tool,
            "requires_permission": self.requires_permission,
            "risk": self.risk,
        }

    def __repr__(self):
        """デバッグ時に中身が分かりやすい表示にします。"""
        return (
            "Route("
            f"target={self.target!r}, "
            f"reason={self.reason!r}, "
            f"model={self.model!r}, "
            f"tool={self.tool!r}, "
            f"requires_permission={self.requires_permission!r}, "
            f"risk={self.risk!r}"
            ")"
        )
