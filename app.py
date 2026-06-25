from ai.llm import ask_llm

from ai.memory_context import build_memory_context

from database.models import create_database

from ai.memory_extract import extract_memories

from database.chat_history import (
    save_message,
    get_recent_messages
)

from database.memory_manager import (
    get_memories
)

from ai.llm import ask_llm


create_database()

from database.memory_manager import (
    get_memories,
    save_memory
)

while True:

    user_input = input("あなた: ")

    if user_input.lower() == "exit":
        break

    save_message(
        "user",
        user_input
    )

    extracted_memories = extract_memories(user_input)

    for extracted_memory in extracted_memories:
        if extracted_memory.get("content"):
            save_memory(
                extracted_memory.get("content"),
                extracted_memory.get("memory_type", "user_profile"),
                extracted_memory.get("category", "other"),
                extracted_memory.get("importance", 5),
                extracted_memory.get("source", "user"),
                extracted_memory.get("tags", "")
)

    memories = get_memories()

    memory_context = build_memory_context(memories)

    history = get_recent_messages(20)

    messages = []

    messages.append(
        {
            "role": "system",
            "content": """
            あなたはPersonalAIです。

            ユーザーを支援してください。
            分からないことは分からないと言ってください。
            """
        }
    )

    messages.append(
        {
            "role": "system",
            "content": memory_context
        }
    )

    for message in history:

        messages.append(
            {
                "role": message.role,
                "content": message.content
            }
        )

    ai_response = ask_llm(messages)

    save_message(
        "assistant",
        ai_response
    )

    print()
    print("AI:", ai_response)
    print()