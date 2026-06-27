class Router:
    """Plannerのplanを見て、使う処理系を選ぶ簡易Routerです。"""

    def route(self, plan):
        """planからrouteを作ります。

        routeは「どのモデルやツールに渡すか」を表すdictです。
        現時点では実際のツール実行は行いません。
        """
        target = self._detect_target(plan)
        return self._build_route(target, plan)

    def _detect_target(self, plan):
        """planの内容を見て、処理を渡すtargetを決めます。"""
        if plan is None:
            return "qwen"

        risk = plan.get("risk")

        # 高リスクな処理は、将来OpenAIに任せる候補として扱います。
        # まだOpenAIを実行するわけではありません。
        if risk == "high":
            return "openai_candidate"

        action = plan.get("action")

        # 現時点では、基本的な行動はQwenで対応します。
        qwen_actions = [
            "chat",
            "memory_read",
            "memory_write",
            "unknown",
        ]

        if action in qwen_actions:
            return "qwen"

        return "qwen"

    def _build_route(self, target, plan):
        """targetとplanから、後続処理に渡しやすいrouteを作ります。"""
        if plan is None:
            plan = {}

        risk = plan.get("risk", "low")
        requires_permission = plan.get("requires_permission", False)

        routes = {
            "qwen": {
                "target": "qwen",
                "reason": self._build_qwen_reason(plan),
                "model": "qwen3:8b",
                "tool": None,
                "requires_permission": requires_permission,
                "risk": risk,
            },
            "openai_candidate": {
                "target": "openai_candidate",
                "reason": "高リスクな処理のため、将来的にOpenAIを候補にする必要があるため",
                "model": None,
                "tool": None,
                "requires_permission": requires_permission,
                "risk": risk,
            },
        }

        return routes.get(target, routes["qwen"]).copy()

    def _build_qwen_reason(self, plan):
        """Qwenを選ぶ理由をactionごとに分かりやすく返します。"""
        action = plan.get("action")

        reasons = {
            "chat": "通常の会話はQwenで対応できるため",
            "memory_read": "長期記憶を使った回答はQwenで対応できるため",
            "memory_write": "記憶抽出や記憶に関する処理はQwenで対応できるため",
        }

        return reasons.get(action, "現時点ではQwenを標準の処理系として使うため")
