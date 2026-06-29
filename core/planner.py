from core.models.plan import Plan


class Planner:
    """PersonalAIが次に何をするかを決める簡易Plannerです。"""

    def create_plan(self, user_input, context=None, capabilities=None):
        """ユーザー入力から、実行したい行動の計画を作ります。

        contextにはInputAnalyzerの解析結果が入ります。
        現時点ではルールベースでactionを決めます。
        """
        action = self._detect_action(user_input)

        # 名前や好きな食べ物など、既存の記憶系判定は優先して維持します。
        if action in ["memory_read", "memory_write"]:
            return self._build_plan(action)

        clarification_action = self._detect_clarification_action(user_input, context)

        if clarification_action is not None:
            return self._build_plan(clarification_action)

        context_action = self._detect_action_from_context(context)

        if context_action is not None:
            action = context_action

        return self._build_plan(action)

    def _detect_action(self, user_input):
        """ユーザー入力の言葉を見て、必要なactionを判定します。"""
        text = str(user_input)

        # 質問形の入力は、過去情報の参照として先に判定します。
        # 例: 「私の名前は？」「好きな食べ物は？」
        memory_read_keywords = [
            "私の名前は？",
            "私の名前は?",
            "僕の名前は？",
            "僕の名前は?",
            "好きな食べ物は？",
            "好きな食べ物は?",
            "何が好き",
            "覚えてる",
            "記憶してる",
        ]

        if any(keyword in text for keyword in memory_read_keywords):
            return "memory_read"

        # 覚えてほしい情報が含まれる入力は、長期記憶への保存・更新として扱います。
        # 例: 「覚えて」「私の名前は太郎」「カレーが好き」
        memory_write_keywords = [
            "覚えて",
            "記憶して",
            "私の名前は",
            "僕の名前は",
            "好き",
        ]

        if any(keyword in text for keyword in memory_write_keywords):
            return "memory_write"

        return "chat"

    def _detect_clarification_action(self, user_input, context):
        """明らかに情報が足りない入力なら、追加質問のactionにします。"""
        text = str(user_input)
        task_type = self._get_context_value(context, "task_type")
        has_url = self._get_context_value(context, "has_url", False)

        if has_url:
            return None

        clarification_task_types = [
            "summarize",
            "create_document",
            "question",
        ]

        youtube_keywords = [
            "youtube",
            "YouTube",
            "動画",
        ]

        if (
            task_type in clarification_task_types
            and self._contains_any(text, youtube_keywords)
        ):
            return "ask_clarification_youtube"

        web_keywords = [
            "URL",
            "url",
            "サイト",
            "Web",
            "web",
            "ページ",
        ]

        if (
            task_type in clarification_task_types
            and self._contains_any(text, web_keywords)
        ):
            return "ask_clarification_web"

        file_read_keywords = [
            "PDF",
            "pdf",
            "画像",
            "写真",
            "資料",
        ]

        if self._contains_any(text, file_read_keywords):
            return "ask_clarification_file"

        return None

    def _detect_action_from_context(self, context):
        """InputAnalyzerの結果から、より具体的なactionを判定します。"""
        input_type = self._get_context_value(context, "input_type")
        task_type = self._get_context_value(context, "task_type")
        requires_external_reading = self._get_context_value(
            context,
            "requires_external_reading",
            False,
        )
        requires_file_creation = self._get_context_value(
            context,
            "requires_file_creation",
            False,
        )

        if task_type == "remember":
            return "memory_write"

        if (
            input_type == "youtube"
            and task_type == "summarize"
            and requires_external_reading
        ):
            return "summarize_youtube"

        if (
            input_type == "url"
            and task_type == "summarize"
            and requires_external_reading
        ):
            return "summarize_url"

        if task_type == "create_document" and requires_file_creation:
            return "create_document"

        if requires_external_reading:
            return "unsupported_external_reading"

        if requires_file_creation:
            return "unsupported_file_creation"

        if task_type == "recommend":
            return "recommend"

        if task_type == "question":
            return "answer_question"

        return None

    def _build_plan(self, action):
        """action名から、Executorへ渡しやすいPlanを作ります。"""
        plans = {
            "chat": Plan(
                action="chat",
                reason="通常の会話として処理できるため",
                required_capabilities=["chat", "llm_qwen"],
                requires_permission=False,
                risk="low",
            ),
            "memory_read": Plan(
                action="memory_read",
                reason="過去に保存した情報を参照する質問のため",
                required_capabilities=["memory_read", "llm_qwen"],
                requires_permission=False,
                risk="low",
            ),
            "memory_write": Plan(
                action="memory_write",
                reason="今後も使える情報として記憶する必要があるため",
                required_capabilities=["memory_write", "llm_qwen"],
                requires_permission=False,
                risk="medium",
            ),
            "summarize_youtube": Plan(
                action="summarize_youtube",
                reason="YouTube URLの要約依頼だが、YouTube実読み取りはまだ未実装のため",
                required_capabilities=["chat", "llm_qwen"],
                requires_permission=False,
                risk="low",
            ),
            "summarize_url": Plan(
                action="summarize_url",
                reason="URLの要約依頼だが、Web読み取りはまだ未実装のため",
                required_capabilities=["chat", "llm_qwen"],
                requires_permission=False,
                risk="low",
            ),
            "create_document": Plan(
                action="create_document",
                reason="文書作成依頼だが、実ファイル作成はまだ未実装のため",
                required_capabilities=["chat", "llm_qwen"],
                requires_permission=False,
                risk="medium",
            ),
            "recommend": Plan(
                action="recommend",
                reason="おすすめ・提案依頼として処理します",
                required_capabilities=["chat", "llm_qwen"],
                requires_permission=False,
                risk="low",
            ),
            "answer_question": Plan(
                action="answer_question",
                reason="質問として回答します",
                required_capabilities=["chat", "llm_qwen"],
                requires_permission=False,
                risk="low",
            ),
            "unsupported_external_reading": Plan(
                action="unsupported_external_reading",
                reason="外部情報の読み取りが必要だが、実読み取り機能はまだ未実装のため",
                required_capabilities=["chat", "llm_qwen"],
                requires_permission=False,
                risk="low",
            ),
            "unsupported_file_creation": Plan(
                action="unsupported_file_creation",
                reason="ファイル作成が必要だが、実ファイル作成機能はまだ未実装のため",
                required_capabilities=["chat", "llm_qwen"],
                requires_permission=False,
                risk="medium",
            ),
            "ask_clarification": Plan(
                action="ask_clarification",
                reason="その作業を進めるには追加情報が必要なため",
                required_capabilities=["chat", "llm_qwen"],
                requires_permission=False,
                risk="low",
            ),
            "ask_clarification_youtube": Plan(
                action="ask_clarification",
                reason="YouTubeまたは動画に関する依頼だが、URLが不足しているため",
                required_capabilities=["chat", "llm_qwen"],
                requires_permission=False,
                risk="low",
            ),
            "ask_clarification_web": Plan(
                action="ask_clarification",
                reason="WebページまたはURLに関する依頼だが、URLが不足しているため",
                required_capabilities=["chat", "llm_qwen"],
                requires_permission=False,
                risk="low",
            ),
            "ask_clarification_file": Plan(
                action="ask_clarification",
                reason="PDFまたは画像の読み取り依頼だが、対象ファイルやURLが不足しているため",
                required_capabilities=["chat", "llm_qwen"],
                requires_permission=False,
                risk="low",
            ),
        }

        return plans.get(action, plans["chat"])

    def _get_context_value(self, context, key, default=None):
        """InputAnalyzerのdictから値を取り出します。"""
        if context is None:
            return default

        if isinstance(context, dict):
            return context.get(key, default)

        return getattr(context, key, default)

    def _contains_any(self, text, keywords):
        """入力文に候補キーワードが1つでも含まれているかを調べます。"""
        return any(keyword in text for keyword in keywords)
