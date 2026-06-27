from ai.llm import ask_llm
from ai.memory_context import build_memory_context
from ai.memory_extract import extract_memories
from database.chat_history import get_recent_messages, save_message
from database.memory_manager import get_memories, save_memory
from database.models import create_database


class PersonalAI:
    """PersonalAI本体の会話処理をまとめるクラスです。"""

    def __init__(self):
        # 起動時にデータベースとテーブルを用意します。
        create_database()

    def run(self):
        """ユーザー入力を受け取り続けるメインループです。"""
        while True:
            user_input = input("あなた: ")

            if user_input.lower() == "exit":
                break

            ai_response = self.handle_user_input(user_input)

            print()
            print("AI:", ai_response)
            print()

    def handle_user_input(self, user_input):
        """ユーザーの1回分の発言を処理して、AIの返答を返します。"""
        self.save_user_message(user_input)
        self.extract_and_save_memories(user_input)

        messages = self.build_messages()
        ai_response = ask_llm(messages)

        self.save_assistant_message(ai_response)

        return ai_response

    def save_user_message(self, user_input):
        """ユーザー発言を会話履歴に保存します。"""
        save_message("user", user_input)

    def save_assistant_message(self, ai_response):
        """AIの返答を会話履歴に保存します。"""
        save_message("assistant", ai_response)

    def extract_and_save_memories(self, user_input):
        """ユーザー発言から長期記憶を抽出し、保存します。"""
        extracted_memories = extract_memories(user_input)

        for extracted_memory in extracted_memories:
            if extracted_memory.get("content"):
                save_memory(
                    extracted_memory.get("content"),
                    extracted_memory.get("memory_type", "user_profile"),
                    extracted_memory.get("category", "other"),
                    extracted_memory.get("importance", 5),
                    extracted_memory.get("source", "user"),
                    extracted_memory.get("tags", ""),
                )

    def build_messages(self):
        """長期記憶と会話履歴を使って、LLMに渡すmessagesを作ります。"""
        memories = get_memories()
        memory_context = build_memory_context(memories)
        recent_messages = get_recent_messages(20)

        messages = [
            {
                "role": "system",
                "content": """
            あなたはPersonalAIです。

            ユーザーを支援してください。
            分からないことは分からないと言ってください。
            """,
            },
            {
                "role": "system",
                "content": memory_context,
            },
        ]

        for message in recent_messages:
            messages.append(
                {
                    "role": message.role,
                    "content": message.content,
                }
            )

        return messages
