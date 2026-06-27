class Plan:
    """Plannerが作る行動計画を表すデータクラスです。"""

    def __init__(
        self,
        action="chat",
        reason="",
        required_capabilities=None,
        requires_permission=False,
        risk="low",
    ):
        self.action = action
        self.reason = reason

        # listを初期値に直接書くと共有されるため、Noneのときに新しく作ります。
        if required_capabilities is None:
            required_capabilities = []

        self.required_capabilities = list(required_capabilities)
        self.requires_permission = requires_permission
        self.risk = risk

    def to_dict(self):
        """従来のdict形式でPlanの内容を返します。"""
        return {
            "action": self.action,
            "reason": self.reason,
            "required_capabilities": self.required_capabilities.copy(),
            "requires_permission": self.requires_permission,
            "risk": self.risk,
        }

    def __repr__(self):
        """デバッグ時に中身が分かりやすい表示にします。"""
        return (
            "Plan("
            f"action={self.action!r}, "
            f"reason={self.reason!r}, "
            f"required_capabilities={self.required_capabilities!r}, "
            f"requires_permission={self.requires_permission!r}, "
            f"risk={self.risk!r}"
            ")"
        )
