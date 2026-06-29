import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from database.memory_manager import get_memory_by_id, set_memory_active


def parse_args():
    parser = argparse.ArgumentParser(
        description="Memoryを物理削除せず、is_activeだけを手動で変更します。"
    )
    parser.add_argument(
        "--id",
        type=int,
        required=True,
        help="対象MemoryのIDです。",
    )

    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--deactivate",
        action="store_true",
        help="対象Memoryを無効化します。",
    )
    mode_group.add_argument(
        "--restore",
        action="store_true",
        help="対象Memoryを復元します。",
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help="実際にDBへ変更を適用します。指定しない場合はdry-runです。",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    mode = "deactivate" if args.deactivate else "restore"
    new_is_active = args.restore

    memory = get_memory_by_id(args.id, include_inactive=True)

    if memory is None:
        print(f"[NG] Memory id={args.id} が見つかりません。")
        return 1

    if not args.apply:
        print("=== Memory Status Change Preview ===")
        print(f"mode: {mode}")
        print(f"apply: {args.apply}")
        print()
        print("target:")
        print_memory(memory)
        print()
        print("dry-runです。DBは変更していません。")
        print("実際に変更するには --apply を付けてください。")
        return 0

    old_is_active = getattr(memory, "is_active", None)

    print("target:")
    print_memory(memory)
    print()

    updated_memory = set_memory_active(args.id, new_is_active)

    if updated_memory is None:
        print(f"[NG] Memory id={args.id} が見つかりません。")
        return 1

    print("=== Memory Status Change Applied ===")
    print(f"id: {updated_memory.id}")
    print(f"old is_active: {old_is_active}")
    print(f"new is_active: {updated_memory.is_active}")
    return 0


def print_memory(memory):
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


def display_value(value):
    if value is None or value == "":
        return "-"

    return str(value)


if __name__ == "__main__":
    raise SystemExit(main())
