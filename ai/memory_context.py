def build_memory_context(memories):

    context = """
【長期記憶】
以下はユーザーについての確定情報です。
この内容を優先して回答してください。
矛盾する一般知識や推測より、この長期記憶を優先してください。

"""

    for memory in memories:
        context += f"- {memory.content}\n"

    return context