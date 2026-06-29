import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from database.memory_manager import get_memories


SEARCH_FIELDS = [
    "content",
    "category",
    "subcategory",
    "scope",
    "memory_key",
    "source",
    "tags",
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="現在DBに保存されている長期記憶を読み取り専用で一覧表示します。"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="表示する記憶の最大件数です。既定値は20です。",
    )
    parser.add_argument(
        "--memory-type",
        default=None,
        help="memory_typeで絞り込みます。例: user_profile",
    )
    parser.add_argument(
        "--category",
        default=None,
        help="categoryで絞り込みます。例: name, project",
    )
    parser.add_argument(
        "--scope",
        default=None,
        help="scopeで絞り込みます。例: user, project, knowledge",
    )
    parser.add_argument(
        "--active-only",
        action="store_true",
        help="有効な記憶だけ表示します。既定動作と同じです。",
    )
    parser.add_argument(
        "--include-inactive",
        action="store_true",
        help="無効な記憶も含めて表示します。既定では有効な記憶だけ表示します。",
    )
    parser.add_argument(
        "--search",
        default=None,
        help="contentやtagsなどを簡易検索します。",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # このスクリプトは読み取り専用です。記憶の削除・更新・無効化は行いません。
    memories = get_memories(
        limit=args.limit,
        memory_type=args.memory_type,
        category=args.category,
        scope=args.scope,
        active_only=not args.include_inactive,
    )
    memories = filter_by_search(memories, args.search)

    print("=== Memories ===")
    print()

    if not memories:
        print("保存されている記憶はありません。")
        return

    for index, memory in enumerate(memories, start=1):
        print_memory_block(index, memory)


def filter_by_search(memories, search_text):
    if not search_text:
        return memories

    search_text = search_text.lower()
    filtered_memories = []

    for memory in memories:
        searchable_text = " ".join(
            safe_text(getattr(memory, field_name, ""))
            for field_name in SEARCH_FIELDS
        ).lower()

        if search_text in searchable_text:
            filtered_memories.append(memory)

    return filtered_memories


def print_memory_block(index, memory):
    print(f"[{index}]")
    print(f"id: {display_value(getattr(memory, 'id', None))}")
    print(f"content: {display_value(getattr(memory, 'content', None))}")
    print(f"memory_type: {display_value(getattr(memory, 'memory_type', None))}")
    print(f"category: {display_value(getattr(memory, 'category', None))}")
    print(f"subcategory: {display_value(getattr(memory, 'subcategory', None))}")
    print(f"scope: {display_value(getattr(memory, 'scope', None))}")
    print(f"memory_key: {display_value(getattr(memory, 'memory_key', None))}")
    print(f"importance: {display_value(getattr(memory, 'importance', None))}")
    print(f"confidence: {display_value(getattr(memory, 'confidence', None))}")
    print(f"is_active: {display_value(getattr(memory, 'is_active', None))}")
    print(f"source: {display_value(getattr(memory, 'source', None))}")
    print(f"tags: {display_value(getattr(memory, 'tags', None))}")
    print(f"created_at: {display_value(getattr(memory, 'created_at', None))}")
    print(f"updated_at: {display_value(getattr(memory, 'updated_at', None))}")
    print(f"expires_at: {display_value(getattr(memory, 'expires_at', None))}")
    print()


def display_value(value):
    text = safe_text(value)

    if not text:
        return "-"

    return text


def safe_text(value):
    if value is None:
        return ""

    return str(value)


if __name__ == "__main__":
    main()
