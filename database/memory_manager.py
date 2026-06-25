from datetime import datetime

from database.models import SessionLocal, Memory


def memory_exists(content):
    db = SessionLocal()
    memory = db.query(Memory).filter(Memory.content == content).first()
    db.close()
    return memory is not None


def save_memory(content, memory_type, category, importance, source, tags=""):
    if not content:
        return False

    if isinstance(tags, list):
        tags = ",".join(tags)

    content = str(content)
    memory_type = str(memory_type)
    category = str(category)
    source = str(source)
    tags = str(tags)
    importance = int(importance)

    if memory_exists(content):
        return False

    db = SessionLocal()

    existing_memory = (
        db.query(Memory)
        .filter(Memory.memory_type == memory_type)
        .filter(Memory.category == category)
        .first()
    )

    if existing_memory:
        existing_memory.content = content
        existing_memory.importance = importance
        existing_memory.source = source
        existing_memory.tags = tags
        existing_memory.created_at = datetime.now().isoformat()
        db.commit()
        db.close()
        return True

    memory = Memory(
        created_at=datetime.now().isoformat(),
        content=content,
        memory_type=memory_type,
        category=category,
        importance=importance,
        source=source,
        tags=tags
    )

    db.add(memory)
    db.commit()
    db.close()
    return True


def get_memories(limit=20):
    db = SessionLocal()
    memories = (
        db.query(Memory)
        .order_by(Memory.importance.desc())
        .limit(limit)
        .all()
    )
    db.close()
    return memories