from datetime import datetime

from database.models import SessionLocal, Memory


SINGLE_MEMORY_CATEGORIES = {
    "name",
    "favorite_food",
    "current_activity",
}

MULTI_MEMORY_CATEGORIES = {
    "project",
    "preference",
    "goal",
    "personality",
    "other",
    "knowledge",
}


def memory_exists(content):
    db = SessionLocal()
    memory = db.query(Memory).filter(Memory.content == content).first()
    db.close()
    return memory is not None


def save_memory(
    content,
    memory_type,
    category,
    importance,
    source,
    tags="",
    memory_key=None,
    subcategory=None,
    scope="global",
    confidence=80,
    expires_at=None,
):
    if not content:
        return False

    if isinstance(tags, list):
        tags = ",".join(tags)

    content = str(content)
    memory_type = str(memory_type)
    category = str(category)
    source = str(source)
    tags = str(tags)
    importance = to_int(importance, 5)
    scope = str(scope or "global")
    confidence = to_int(confidence, 80)

    if memory_key is not None:
        memory_key = str(memory_key)

    if subcategory is not None:
        subcategory = str(subcategory)

    now = datetime.now().isoformat()

    # confidenceは記憶の確からしさです。範囲外の値が来ても安全な範囲に丸めます。
    confidence = max(0, min(confidence, 100))

    db = SessionLocal()

    try:
        existing_memory = None

        if memory_key:
            # memory_keyがある場合は、同じ種類・同じ範囲・同じキーの記憶を更新します。
            existing_memory = (
                db.query(Memory)
                .filter(Memory.memory_type == memory_type)
                .filter(Memory.scope == scope)
                .filter(Memory.memory_key == memory_key)
                .first()
            )
        elif should_update_by_category(category):
            # 名前や好きな食べ物など、1つにまとまる記憶は従来通りcategory単位で更新します。
            existing_memory = (
                db.query(Memory)
                .filter(Memory.memory_type == memory_type)
                .filter(Memory.category == category)
                .first()
            )

        if existing_memory:
            duplicate_memory = find_duplicate_memory(db, content)

            if duplicate_memory and duplicate_memory.id != existing_memory.id:
                return False

            update_memory(
                existing_memory,
                content,
                category,
                importance,
                source,
                tags,
                memory_key,
                subcategory,
                scope,
                confidence,
                expires_at,
                now,
            )
            db.commit()
            return True

        duplicate_memory = find_duplicate_memory(db, content)

        if duplicate_memory:
            return False

        memory = Memory(
            created_at=now,
            updated_at=now,
            content=content,
            memory_type=memory_type,
            category=category,
            memory_key=memory_key,
            subcategory=subcategory,
            scope=scope,
            confidence=confidence,
            expires_at=expires_at,
            is_active=True,
            importance=importance,
            source=source,
            tags=tags,
        )

        db.add(memory)
        db.commit()
        return True
    finally:
        db.close()


def should_update_by_category(category):
    """categoryだけで上書きしてよい種類かを判定します。"""
    if category in SINGLE_MEMORY_CATEGORIES:
        return True

    if category in MULTI_MEMORY_CATEGORIES:
        return False

    # 未分類のcategoryは、既存動作を壊しにくいように従来通り更新対象にします。
    return True


def to_int(value, default):
    """LLM由来の値が数字でない場合でも、安全に整数へ変換します。"""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def find_duplicate_memory(db, content):
    """同じcontentの記憶がすでにあるかを確認します。"""
    return (
        db.query(Memory)
        .filter(Memory.content == content)
        .first()
    )


def update_memory(
    memory,
    content,
    category,
    importance,
    source,
    tags,
    memory_key,
    subcategory,
    scope,
    confidence,
    expires_at,
    updated_at,
):
    """既存の記憶を、Ver0.13の追加項目も含めて更新します。"""
    memory.content = content
    memory.category = category
    memory.importance = importance
    memory.source = source
    memory.tags = tags
    memory.memory_key = memory_key
    memory.subcategory = subcategory
    memory.scope = scope
    memory.confidence = confidence
    memory.expires_at = expires_at
    memory.updated_at = updated_at
    memory.is_active = True


def get_memories(
    limit=20,
    memory_type=None,
    category=None,
    scope=None,
    active_only=True,
):
    db = SessionLocal()

    try:
        query = db.query(Memory)

        if memory_type is not None:
            query = query.filter(Memory.memory_type == memory_type)

        if category is not None:
            query = query.filter(Memory.category == category)

        if scope is not None:
            query = query.filter(Memory.scope == scope)

        if active_only:
            query = query.filter(Memory.is_active == True)

        memories = (
            query
            .order_by(
                Memory.importance.desc(),
                Memory.updated_at.desc(),
                Memory.created_at.desc(),
            )
            .limit(limit)
            .all()
        )

        return memories
    finally:
        db.close()


def get_memory_by_id(memory_id, include_inactive=True):
    """IDでMemoryを1件取得します。見つからない場合はNoneを返します。"""
    db = SessionLocal()

    try:
        query = db.query(Memory).filter(Memory.id == memory_id)

        if not include_inactive:
            query = query.filter(Memory.is_active == True)

        memory = query.first()

        if memory is None:
            return None

        # 呼び出し元で安全に表示できるよう、セッションから切り離して返します。
        db.expunge(memory)
        return memory
    finally:
        db.close()


def set_memory_active(memory_id, is_active):
    """Memoryを削除せず、is_activeだけを変更します。"""
    db = SessionLocal()

    try:
        memory = db.query(Memory).filter(Memory.id == memory_id).first()

        if memory is None:
            return None

        memory.is_active = bool(is_active)
        memory.updated_at = datetime.now().isoformat()
        db.commit()
        db.refresh(memory)

        # commit後に属性が期限切れにならないよう、返す前に切り離します。
        db.expunge(memory)
        return memory
    finally:
        db.close()
