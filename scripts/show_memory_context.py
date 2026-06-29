import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from ai.memory_context import build_memory_context
from database.memory_manager import get_memories


def parse_args():
    parser = argparse.ArgumentParser(
        description="現在DBに保存されている長期記憶からMemoryContextを表示します。"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="取得する記憶の最大件数です。既定値は20です。",
    )
    parser.add_argument(
        "--category",
        default=None,
        help="categoryで絞り込みます。例: project",
    )
    parser.add_argument(
        "--scope",
        default=None,
        help="scopeで絞り込みます。例: user, project, knowledge",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # このスクリプトは確認専用です。DBの記憶を削除・更新しません。
    memories = get_memories(
        limit=args.limit,
        category=args.category,
        scope=args.scope,
    )
    context = build_memory_context(memories)

    print("=== MemoryContext Preview ===")
    print()
    print(context)


if __name__ == "__main__":
    main()
