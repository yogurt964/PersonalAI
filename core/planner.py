from core.models.plan import Plan


class Planner:
    """PersonalAIが次に何をするかを決める簡易Plannerです。"""

    def create_plan(self, user_input, context=None, capabilities=None):
        """ユーザー入力から、実行したい行動の計画を作ります。

        contextとcapabilitiesは将来の拡張用です。
        現時点ではルールベースでactionを決めます。
        """
        action = self._detect_action(user_input)
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
        }

        return plans.get(action, plans["chat"])
