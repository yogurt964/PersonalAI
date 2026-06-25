from database.memory_manager import get_memories

memories = get_memories(100)

for memory in memories:
    print(
        memory.id,
        memory.category,
        memory.content,
        memory.memory_type,
        memory.importance
    )