class CapabilityManager:
    """PersonalAIが利用できる能力を管理するクラスです。"""

    def __init__(self):
        # 現時点では、実際にツールを実行せず「使える能力の一覧」だけを持ちます。
        self._capabilities = {
            "chat": {
                "description": "通常の会話を行う",
                "risk": "low",
                "requires_permission": False,
            },
            "memory_read": {
                "description": "長期記憶を参照する",
                "risk": "low",
                "requires_permission": False,
            },
            "memory_write": {
                "description": "長期記憶を保存・更新する",
                "risk": "medium",
                "requires_permission": False,
            },
            "llm_qwen": {
                "description": "Qwenを使って回答や記憶抽出を行う",
                "risk": "medium",
                "requires_permission": False,
            },
        }

    def get_all_capabilities(self):
        """登録されているすべてのcapabilityを返します。"""
        return {
            name: capability.copy()
            for name, capability in self._capabilities.items()
        }

    def get_capability(self, name):
        """名前を指定して、capabilityを1つ取得します。"""
        capability = self._capabilities.get(name)

        if capability is None:
            return None

        return capability.copy()

    def get_available_capabilities(self, user_input=None):
        """現在利用可能なcapabilityを返します。

        user_inputは将来の絞り込み用です。
        現時点では入力内容に関係なく、すべてのcapabilityを返します。
        """
        return self.get_all_capabilities()
