from ollama import chat

SYSTEM_PROMPT = """
あなたはPersonalAIです。

基本原則
・ユーザーを支援する
・会話履歴を活用する
・長期記憶を活用する
・分からないことは分からないと言う
・推測は推測と明示する
"""


def ask_llm(messages):

    response = chat(
        model="qwen3:8b",
        messages=messages
    )

    return response.message.content