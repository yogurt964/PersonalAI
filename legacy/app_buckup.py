# 旧テスト用コードです。
# category導入前のsave_memory()仕様で書かれているため、現在は実行対象外です。

from database.models import create_database
from database.memory_manager import save_memory, get_memories

create_database()

save_memory(
    content="ユーザー名は巧弥",
    memory_type="user_profile",
    importance=10,
    source="user",
    tags="名前,ユーザー情報"
)

memories = get_memories()

for memory in memories:
    print(memory.id, memory.content, memory.memory_type, memory.importance)
