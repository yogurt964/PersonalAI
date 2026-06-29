class PermissionManager:
    """PlanやRouteを見て、許可が必要かを判断するクラスです。"""

    def __init__(self):
        # 現在実装済み、または未実装メッセージだけを返す安全なactionです。
        self.low_risk_actions = {
            "chat",
            "answer_question",
            "recommend",
            "memory_read",
            "memory_write",
            "ask_clarification",
            "summarize_youtube",
            "summarize_url",
            "create_document",
            "unsupported_external_reading",
            "unsupported_file_creation",
        }

        # 将来、ユーザー許可が必要になる中リスクactionです。
        self.medium_risk_actions = {
            "read_file",
            "create_file",
            "edit_file",
            "read_url",
            "read_web",
            "read_youtube",
            "read_pdf",
            "read_image",
            "create_word",
            "create_excel",
            "create_pdf",
            "create_slide",
            "run_test",
        }

        # 将来、特に慎重な許可確認が必要になる高リスクactionです。
        self.high_risk_actions = {
            "delete_file",
            "overwrite_file",
            "send_external",
            "send_email",
            "git_commit",
            "git_push",
            "run_command",
            "pc_control",
            "screen_read",
            "use_external_api",
            "handle_personal_info",
            "payment_or_billing",
        }

    def evaluate(self, plan=None, route=None, action=None):
        """許可が必要かどうかをdictで返します。

        現時点では、許可が必要な操作は再開処理がないためblocked=Trueにします。
        """
        action = action or self._get_value(plan, "action")

        if action in self.low_risk_actions:
            return {
                "requires_permission": False,
                "risk": "low",
                "reason": "現在の実装では安全に処理できるactionです",
                "blocked": False,
            }

        if action in self.medium_risk_actions:
            return {
                "requires_permission": True,
                "risk": "medium",
                "reason": f"{action} は中リスク操作のため、ユーザー許可が必要です",
                "blocked": True,
            }

        if action in self.high_risk_actions:
            return {
                "requires_permission": True,
                "risk": "high",
                "reason": f"{action} は高リスク操作のため、ユーザー許可が必要です",
                "blocked": True,
            }

        return {
            "requires_permission": True,
            "risk": "medium",
            "reason": "未分類のactionのため、ユーザー許可が必要です",
            "blocked": True,
        }

    def _get_value(self, obj, key, default=None):
        """Plan/Routeインスタンスとdict形式の両方から値を取り出します。"""
        if obj is None:
            return default

        if isinstance(obj, dict):
            return obj.get(key, default)

        return getattr(obj, key, default)
