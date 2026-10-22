"""Synthetic memory demo. No database, model, API key or network access."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.conversation_memory import (
    ConversationSource, MemoryScope, ShortTermMemory, SourceBatch, StateNote,
)


def main():
    scope = MemoryScope("demo-user", "demo-project")
    source = ConversationSource.from_row("demo", 1, "user",
        "今は質問せず聞いてて。週末の予定はまだ決めていない。", "2026-10-22T09:00:00+09:00")
    evidence = SourceBatch(scope, "demo", (source,))
    memory = ShortTermMemory(scope, "demo")
    state = memory.apply(expected_version=0, evidence=evidence, topic="週末の予定",
        upserts=(StateNote("questions", "temporary_preference", "今は質問なし", (source.ref,)),
                 StateNote("weekend", "open_question", "週末の予定は未決定", (source.ref,), ("予定",))))
    print("架空データによる基盤デモ。要点は手動定義で、AIによる抽出ではありません。")
    print("短期記憶:", ", ".join(note.content for note in state.notes))
    print("原文参照ID:", source.ref.message_id)
    print("状態サイズ（UTF-8 JSON）:", len(state.to_json().encode("utf-8")), "bytes")
    ended = memory.end_topic(expected_version=1)
    print("話題終了後:", ", ".join(note.content for note in ended.notes))
    print("その場の希望だけ解除し、未解決事項を保持。原文削除・長期保存は行っていません。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
