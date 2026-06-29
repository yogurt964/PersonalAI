from core.models.route import Route


class Router:
    """Plannerのplanを見て、使う処理系を選ぶ簡易Routerです。"""

    def route(self, plan):
        """planからrouteを作ります。

        routeは「どのモデルやツールに渡すか」を表すRouteです。
        現時点では実際のツール実行は行いません。
        """
        target = self._detect_target(plan)
        return self._build_route(target, plan)

    def _detect_target(self, plan):
        """planの内容を見て、処理を渡すtargetを決めます。"""
        if plan is None:
            return "qwen"

        risk = self._get_plan_value(plan, "risk")

        # 高リスクな処理は、将来OpenAIに任せる候補として扱います。
        # まだOpenAIを実行するわけではありません。
        if risk == "high":
            return "openai_candidate"

        action = self._get_plan_value(plan, "action")

        # 現時点では、基本的な行動はQwenで対応します。
        qwen_actions = [
            "chat",
            "memory_read",
            "memory_write",
            "summarize_youtube",
            "summarize_url",
            "create_document",
            "recommend",
            "answer_question",
            "unsupported_external_reading",
            "unsupported_file_creation",
            "unknown",
        ]

        if action in qwen_actions:
            return "qwen"

        return "qwen"

    def _build_route(self, target, plan):
        """targetとplanから、後続処理に渡しやすいRouteを作ります。"""
        risk = self._get_plan_value(plan, "risk", "low")
        requires_permission = self._get_plan_value(
            plan,
            "requires_permission",
            False,
        )

        routes = {
            "qwen": Route(
                target="qwen",
                reason=self._build_qwen_reason(plan),
                model="qwen3:8b",
                tool=None,
                requires_permission=requires_permission,
                risk=risk,
            ),
            "openai_candidate": Route(
                target="openai_candidate",
                reason="高リスクな処理のため、将来的にOpenAIを候補にする必要があるため",
                model=None,
                tool=None,
                requires_permission=requires_permission,
                risk=risk,
            ),
        }

        return routes.get(target, routes["qwen"])

    def _build_qwen_reason(self, plan):
        """Qwenを選ぶ理由をactionごとに分かりやすく返します。"""
        action = self._get_plan_value(plan, "action")

        reasons = {
            "chat": "通常の会話はQwenで対応できるため",
            "memory_read": "長期記憶を使った回答はQwenで対応できるため",
            "memory_write": "記憶抽出や記憶に関する処理はQwenで対応できるため",
            "summarize_youtube": "YouTube読み取りは未実装のため、Qwenで未対応説明を行うため",
            "summarize_url": "Web読み取りは未実装のため、Qwenで未対応説明を行うため",
            "create_document": "実ファイル作成は未実装のため、Qwenで文書案または未対応説明を行うため",
            "recommend": "おすすめ・提案依頼はQwenで対応できるため",
            "answer_question": "質問への回答はQwenで対応できるため",
            "unsupported_external_reading": "外部読み取りは未実装のため、Qwenで未対応説明を行うため",
            "unsupported_file_creation": "実ファイル作成は未実装のため、Qwenで未対応説明を行うため",
        }

        return reasons.get(action, "現時点ではQwenを標準の処理系として使うため")

    def _get_plan_value(self, plan, key, default=None):
        """Planインスタンスと従来のdict形式の両方から値を取り出します。"""
        if plan is None:
            return default

        if isinstance(plan, dict):
            return plan.get(key, default)

        return getattr(plan, key, default)
