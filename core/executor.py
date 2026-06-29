from ai.llm import ask_llm


class Executor:
    """Routerが選んだRouteを実行するクラスです。"""

    def execute(self, plan, route, messages):
        """planとrouteを受け取り、必要な処理を実行します。

        planは将来の条件分岐や安全確認で使う予定です。
        現時点ではroute.targetを見て、どの実行方法に渡すかだけを決めます。
        """
        target = self._get_route_value(route, "target", "qwen")
        action = self._get_plan_value(plan, "action", "chat")

        if target == "qwen":
            if action == "ask_clarification":
                return self._execute_ask_clarification(plan)

            if action == "summarize_youtube":
                return self._execute_summarize_youtube()

            if action == "summarize_url":
                return self._execute_summarize_url()

            if action == "create_document":
                return self._execute_create_document()

            if action == "unsupported_external_reading":
                return self._execute_unsupported_external_reading()

            if action == "unsupported_file_creation":
                return self._execute_create_document()

            return self._execute_qwen(messages)

        if target == "openai_candidate":
            return self._execute_openai_candidate()

        return self._execute_unknown_target(target)

    def _execute_qwen(self, messages):
        """Qwenを使って回答を生成します。"""
        return ask_llm(messages)

    def _execute_ask_clarification(self, plan):
        """情報不足のときに、必要最小限の質問を返します。"""
        reason = self._get_plan_value(plan, "reason", "")

        if "YouTube" in reason or "動画" in reason:
            return (
                "YouTubeまたは動画の内容を扱うには、対象のURLが必要です。\n"
                "動画のURLを送ってください。\n"
                "必要なら、要約用・実装参考用・レポート用のどれに近いかも教えてください。"
            )

        if "PDF" in reason or "画像" in reason or "資料" in reason:
            return (
                "PDF・画像・資料の内容を扱うには、対象ファイルまたはURLが必要です。\n"
                "読み取りたいファイルやURLを送ってください。\n"
                "何をしたいか、要約・説明・レポート化などの目的も教えてください。"
            )

        if "Web" in reason or "URL" in reason:
            return (
                "Webページの内容を扱うには、対象のURLが必要です。\n"
                "要約したいページのURLを送ってください。\n"
                "必要なら、短く要約するか、詳しく整理するかも教えてください。"
            )

        return (
            "その作業を進めるには、もう少し情報が必要です。\n"
            "対象となるURL・ファイル・内容、または目的を教えてください。"
        )

    def _execute_summarize_youtube(self):
        """YouTube読み取りが未実装であることを正直に返します。"""
        return (
            "現時点ではYouTube動画の内容を直接読み取る機能は未実装です。\n"
            "動画の要約を行うには、YouTube Reader機能の実装が必要です。\n"
            "URLの種類はYouTubeとして判定できています。"
        )

    def _execute_summarize_url(self):
        """Web読み取りが未実装であることを正直に返します。"""
        return (
            "現時点ではWebページの内容を直接読み取る機能は未実装です。\n"
            "URLの要約を行うには、Web Reader機能の実装が必要です。\n"
            "URLの検出はできています。"
        )

    def _execute_create_document(self):
        """実ファイル作成が未実装であることを正直に返します。"""
        return (
            "現時点ではWord / PDFなどの実ファイル作成機能は未実装です。\n"
            "ただし、文書の構成案や本文案を作ることは可能です。"
        )

    def _execute_unsupported_external_reading(self):
        """外部読み取りが未実装であることを正直に返します。"""
        return (
            "現時点では外部情報を直接読み取る機能は未実装です。\n"
            "Web Reader、YouTube Reader、PDF Readerなどの実装が必要です。"
        )

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

    def _get_plan_value(self, plan, key, default=None):
        """Planインスタンスとdict形式の両方から値を取り出します。"""
        if plan is None:
            return default

        if isinstance(plan, dict):
            return plan.get(key, default)

        return getattr(plan, key, default)
