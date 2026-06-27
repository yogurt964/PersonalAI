from ai.llm import ask_llm


class Executor:
    """Routerが選んだRouteを実行するクラスです。"""

    def execute(self, plan, route, messages):
        """planとrouteを受け取り、必要な処理を実行します。

        planは将来の条件分岐や安全確認で使う予定です。
        現時点ではroute.targetを見て、どの実行方法に渡すかだけを決めます。
        """
        target = self._get_route_value(route, "target", "qwen")

        if target == "qwen":
            return self._execute_qwen(messages)

        if target == "openai_candidate":
            return self._execute_openai_candidate()

        return self._execute_unknown_target(target)

    def _execute_qwen(self, messages):
        """Qwenを使って回答を生成します。"""
        return ask_llm(messages)

    def _execute_openai_candidate(self):
        """OpenAI候補のrouteを受け取ったときの仮の処理です。

        まだOpenAIは呼び出さず、未実装であることだけを返します。
        """
        return "OpenAI候補の実行はまだ未実装です。"

    def _execute_unknown_target(self, target):
        """未対応のtargetを受け取ったときの安全な戻り値です。"""
        return f"未対応の実行先です: {target}"

    def _get_route_value(self, route, key, default=None):
        """Routeインスタンスとdict形式の両方から値を取り出します。"""
        if route is None:
            return default

        if isinstance(route, dict):
            return route.get(key, default)

        return getattr(route, key, default)
